"""Adaptador de Portal Inmobiliario: recorre las páginas públicas de resultados por comuna.

Solo usa las rutas que robots.txt permite (`/_Desde_N` para paginar). Esas páginas no
traen coordenadas, sino la dirección escrita del aviso; se ubica con el geocodificador
local (índice de direcciones de OpenStreetMap). Los avisos sin número quedan con
precisión "aproximada" o "calle" y no se usan para comparar con un punto exacto.
"""

import json
import re
import time
from collections.abc import Callable
from typing import Any

import httpx

from score.adapters.geocodificador_local import GeocodificadorLocal
from score.domain.avisos import Aviso, Operacion, TipoPropiedad
from score.domain.direcciones import Precision
from score.pipeline.normalizacion import normalizar_nombre

URL_BASE = "https://www.portalinmobiliario.com"
AVISOS_POR_PAGINA = 48
PAGINAS_MAXIMAS = 60  # ~2.900 avisos por comuna y tipo


def slug_comuna(comuna: str) -> str:
    """'Ñuñoa' → 'nunoa-metropolitana'."""
    return normalizar_nombre(comuna).replace(" ", "-") + "-metropolitana"


def url_pagina(comuna: str, operacion: Operacion, tipo: TipoPropiedad, pagina: int) -> str:
    base = f"{URL_BASE}/{operacion}/{tipo}/{slug_comuna(comuna)}"
    return base if pagina == 0 else f"{base}/_Desde_{pagina * AVISOS_POR_PAGINA + 1}"


def leer_tarjetas(html: str) -> list[dict[str, Any]]:
    """Extrae los objetos `polycard` (una tarjeta por aviso) del JSON de la página."""
    tarjetas: dict[str, dict[str, Any]] = {}
    posicion = 0
    while (inicio := html.find('"polycard":', posicion)) >= 0:
        apertura = html.find("{", inicio)
        profundidad, fin = 0, apertura
        en_texto, escapado = False, False
        for fin in range(apertura, len(html)):
            caracter = html[fin]
            if en_texto:
                if escapado:
                    escapado = False
                elif caracter == "\\":
                    escapado = True
                elif caracter == '"':
                    en_texto = False
            elif caracter == '"':
                en_texto = True
            elif caracter == "{":
                profundidad += 1
            elif caracter == "}":
                profundidad -= 1
                if profundidad == 0:
                    break
        posicion = fin
        try:
            tarjeta = json.loads(html[apertura : fin + 1])
        except json.JSONDecodeError:
            continue
        identificador = tarjeta.get("metadata", {}).get("id")
        if identificador:
            tarjetas[identificador] = tarjeta  # la misma tarjeta puede repetirse en la página
    return list(tarjetas.values())


def total_de_resultados(html: str) -> int | None:
    coincidencia = re.search(r'"total":(\d+)', html)
    return int(coincidencia.group(1)) if coincidencia else None


def _numero(texto: str) -> float | None:
    """'54 - 72 m² útiles' → 54 (el menor de un rango)."""
    coincidencia = re.search(r"\d+(?:[.,]\d+)?", texto.replace(".", "").replace(",", "."))
    return float(coincidencia.group()) if coincidencia else None


def a_aviso(
    tarjeta: dict[str, Any],
    operacion: Operacion,
    tipo: TipoPropiedad,
    comuna: str,
    ubicar: Callable[[str], tuple[float, float, Precision] | None],
    uf: float,
) -> Aviso | None:
    partes = {c.get("type"): c for c in tarjeta.get("components", [])}
    precio = partes.get("price", {}).get("price", {}).get("current_price", {})
    valor, moneda = precio.get("value"), precio.get("currency")
    direccion = partes.get("location", {}).get("location", {}).get("text", "")
    ubicacion = ubicar(direccion)
    if valor is None or ubicacion is None:
        return None
    lat, lon, precision = ubicacion
    atributos = partes.get("attributes_list", {}).get("attributes_list", {}).get("texts", [])
    superficie = next((_numero(a) for a in atributos if "m²" in a), None)
    dormitorios = next((_numero(a) for a in atributos if "dormitorio" in a), None)
    banos = next((_numero(a) for a in atributos if "baño" in a), None)
    metadatos = tarjeta.get("metadata", {})
    return Aviso(
        fuente="portalinmobiliario",
        id=str(metadatos.get("id")),
        operacion=operacion,
        tipo=tipo,
        comuna=comuna,
        lat=lat,
        lon=lon,
        precio_clp=float(valor) * uf if moneda == "CLF" else float(valor),
        precio_uf=float(valor) if moneda == "CLF" else float(valor) / uf,
        superficie_m2=superficie if superficie and superficie > 0 else None,
        dormitorios=int(dormitorios) if dormitorios else None,
        banos=int(banos) if banos else None,
        horas_publicado=None,
        url="https://" + str(metadatos.get("url", "")).removeprefix("https://"),
        precision=precision,
    )


class PortalInmobiliario:
    """Implementa el puerto PortalDeAvisos. Espera `pausa_s` entre páginas."""

    nombre = "portalinmobiliario"

    def __init__(
        self,
        cliente: httpx.Client,
        geocodificador: GeocodificadorLocal,
        cut_de_comuna: dict[str, int],
        uf: Callable[[], float],
        pausa_s: float = 1.5,
    ) -> None:
        self._cliente = cliente
        self._geo = geocodificador
        self._cut = {normalizar_nombre(k): v for k, v in cut_de_comuna.items()}
        self._uf = uf
        self._pausa_s = pausa_s
        self._ultima = 0.0

    def _get(self, url: str) -> httpx.Response:
        espera = self._pausa_s - (time.monotonic() - self._ultima)
        if espera > 0:
            time.sleep(espera)
        respuesta = self._cliente.get(url)
        self._ultima = time.monotonic()
        return respuesta

    def avisos_de_comuna(
        self, comuna: str, operacion: Operacion, tipo: TipoPropiedad
    ) -> list[Aviso]:
        cut = self._cut.get(normalizar_nombre(comuna))
        if cut is None:
            return []
        uf = self._uf()

        def ubicar(direccion: str) -> tuple[float, float, Precision] | None:
            u = self._geo.ubicar(direccion, cut)
            return (u.lat, u.lon, u.precision) if u else None

        avisos: dict[str, Aviso] = {}
        total = None
        for pagina in range(PAGINAS_MAXIMAS):
            respuesta = self._get(url_pagina(comuna, operacion, tipo, pagina))
            if respuesta.status_code == 404:
                break
            respuesta.raise_for_status()
            html = respuesta.text
            total = total if total is not None else total_de_resultados(html)
            nuevos = 0
            for tarjeta in leer_tarjetas(html):
                aviso = a_aviso(tarjeta, operacion, tipo, comuna, ubicar, uf)
                if aviso and aviso.id not in avisos:
                    avisos[aviso.id] = aviso
                    nuevos += 1
            vistos = (pagina + 1) * AVISOS_POR_PAGINA
            if nuevos == 0 or total is None or vistos >= total:
                break
        return list(avisos.values())
