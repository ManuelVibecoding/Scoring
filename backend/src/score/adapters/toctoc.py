"""Adaptador de Toc Toc: lee los avisos que la página de resultados trae embebidos.

Cada página de comuna incluye, en el JSON de Next.js (`__NEXT_DATA__`), hasta 260 avisos
con coordenadas, precio en UF y pesos, superficie, dormitorios y baños. Solo se consulta
la ruta pública de resultados por comuna, que robots.txt permite, a ritmo pausado.
"""

import json
import re
import time
from typing import Any

import httpx

from score.domain.avisos import Aviso, Operacion, TipoPropiedad
from score.pipeline.normalizacion import a_numero, normalizar_nombre

URL_BASE = "https://www.toctoc.com"
_DATOS_NEXT = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def slug_comuna(comuna: str) -> str:
    """'Ñuñoa' → 'nunoa'; 'Las Condes' → 'las-condes'."""
    return normalizar_nombre(comuna).replace(" ", "-")


def url_resultados(comuna: str, operacion: Operacion, tipo: TipoPropiedad) -> str:
    return f"{URL_BASE}/{operacion}/{tipo}/metropolitana/{slug_comuna(comuna)}"


def _entero(texto: str | None) -> int | None:
    valor = a_numero(texto)
    return int(valor) if valor is not None else None


def _positivo(valor: float | None) -> float | None:
    """Algunos avisos publican superficie 0: eso es "sin dato", no un departamento de 0 m²."""
    return valor if valor is not None and valor > 0 else None


def _primero(lista: list[str] | None) -> str | None:
    return lista[0] if lista else None


def _precio(precios: list[dict[str, Any]], prefijo: str) -> float | None:
    for p in precios or []:
        if p.get("prefix") == prefijo and p.get("value"):
            texto = str(p["value"])
            # Pesos usan punto de miles ("750.000"); UF usa coma decimal ("18,5").
            texto = texto.replace(".", "") if prefijo == "$" else texto
            return a_numero(texto)
    return None


def leer_avisos(html: str, operacion: Operacion, tipo: TipoPropiedad, comuna: str) -> list[Aviso]:
    """Convierte la página de resultados en avisos. Ignora los que no tienen coordenadas."""
    coincidencia = _DATOS_NEXT.search(html)
    if not coincidencia:
        return []
    datos = json.loads(coincidencia.group(1))
    resultados = datos["props"]["pageProps"].get("propiedades", {}).get("results", [])
    avisos = []
    for r in resultados:
        if r.get("latitud") is None or r.get("longitud") is None:
            continue
        avisos.append(
            Aviso(
                fuente="toctoc",
                id=str(r.get("idProperty") or r.get("hashId")),
                operacion=operacion,
                tipo=tipo,
                comuna=r.get("comuna") or comuna,
                lat=float(r["latitud"]),
                lon=float(r["longitud"]),
                precio_clp=_precio(r.get("precios", []), "$"),
                precio_uf=_precio(r.get("precios", []), "UF"),
                superficie_m2=_positivo(a_numero(_primero(r.get("superficie")))),
                dormitorios=_entero(_primero(r.get("dormitorios"))),
                banos=_entero(_primero(r.get("bannos"))),
                horas_publicado=r.get("horasPublicado"),
                url=r.get("urlFicha", ""),
            )
        )
    return avisos


class TocToc:
    """Implementa el puerto PortalDeAvisos. Espera `pausa_s` entre consultas."""

    nombre = "toctoc"

    def __init__(self, cliente: httpx.Client, pausa_s: float = 2.0) -> None:
        self._cliente = cliente
        self._pausa_s = pausa_s
        self._ultima = 0.0

    def avisos_de_comuna(
        self, comuna: str, operacion: Operacion, tipo: TipoPropiedad
    ) -> list[Aviso]:
        espera = self._pausa_s - (time.monotonic() - self._ultima)
        if espera > 0:
            time.sleep(espera)
        respuesta = self._cliente.get(url_resultados(comuna, operacion, tipo))
        self._ultima = time.monotonic()
        if respuesta.status_code == 404:
            return []
        respuesta.raise_for_status()
        return leer_avisos(respuesta.text, operacion, tipo, comuna)
