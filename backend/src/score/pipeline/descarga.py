"""Descarga de fuentes a data/raw/<id>/ con un manifiesto que registra qué se bajó y cuándo.

El manifiesto permite saber la procedencia de cada archivo (URL, fecha, tamaño, sha256)
y evita volver a descargar lo que ya está, salvo que se pida explícitamente.
"""

import hashlib
import json
import re
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

from score.pipeline.fuentes import Fuente, Recurso

MANIFIESTO = "_manifiesto.json"
_TROZO = 1024 * 1024


@dataclass(frozen=True)
class ArchivoDescargado:
    archivo: str
    url: str
    bytes: int
    sha256: str
    descargado: str


def nombre_desde_respuesta(respuesta: httpx.Response, recurso: Recurso) -> str:
    """Nombre local del archivo: el declarado, el de Content-Disposition o el de la URL."""
    if recurso.archivo:
        return recurso.archivo
    disposicion = respuesta.headers.get("content-disposition", "")
    if m := re.search(r"filename\*=UTF-8''([^;]+)", disposicion, re.I):
        return _limpiar(urllib.parse.unquote(m.group(1)))
    if m := re.search(r'filename="?([^";]+)"?', disposicion, re.I):
        return _limpiar(m.group(1))
    return _limpiar(urllib.parse.unquote(Path(urllib.parse.urlparse(recurso.url).path).name))


def _limpiar(nombre: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", nombre).strip("_") or "archivo"


def leer_manifiesto(carpeta: Path) -> dict[str, ArchivoDescargado]:
    ruta = carpeta / MANIFIESTO
    if not ruta.exists():
        return {}
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return {d["url"]: ArchivoDescargado(**d) for d in datos["archivos"]}


def _escribir_manifiesto(
    carpeta: Path, fuente: Fuente, archivos: dict[str, ArchivoDescargado]
) -> None:
    contenido = {
        "fuente": fuente.id,
        "nombre": fuente.nombre,
        "institucion": fuente.institucion,
        "pagina": fuente.pagina,
        "licencia": fuente.licencia,
        "archivos": [asdict(a) for a in archivos.values()],
    }
    (carpeta / MANIFIESTO).write_text(
        json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def descargar_fuente(
    fuente: Fuente, destino: Path, cliente: httpx.Client, forzar: bool = False
) -> list[ArchivoDescargado]:
    """Descarga todos los recursos de una fuente. Devuelve lo que quedó en disco.

    Las fuentes con resolver publican enlaces que cambian en cada visita, así que se
    consideran completas si ya tienen archivos descargados, y su manifiesto se reemplaza
    entero al volver a bajarlas.
    """
    carpeta = destino / fuente.id
    carpeta.mkdir(parents=True, exist_ok=True)
    previos = leer_manifiesto(carpeta)
    completos = all((carpeta / a.archivo).exists() for a in previos.values())
    if fuente.resolver and previos and completos and not forzar:
        return list(previos.values())

    base = {} if fuente.resolver else previos
    resultado: dict[str, ArchivoDescargado] = {}
    for recurso in fuente.obtener_recursos(cliente):
        previo = base.get(recurso.url)
        if previo and not forzar and (carpeta / previo.archivo).exists():
            resultado[recurso.url] = previo
            continue
        descargado = _descargar_recurso(recurso, carpeta, cliente)
        if any(a.archivo == descargado.archivo for a in resultado.values()):
            continue  # el mismo archivo publicado con dos enlaces
        resultado[recurso.url] = descargado
        _escribir_manifiesto(carpeta, fuente, {**base, **resultado})

    _escribir_manifiesto(carpeta, fuente, {**base, **resultado})
    return list(resultado.values())


def _descargar_recurso(recurso: Recurso, carpeta: Path, cliente: httpx.Client) -> ArchivoDescargado:
    with cliente.stream("GET", recurso.url) as respuesta:
        respuesta.raise_for_status()
        nombre = nombre_desde_respuesta(respuesta, recurso)
        temporal = carpeta / f"{nombre}.parcial"
        resumen = hashlib.sha256()
        total = 0
        with temporal.open("wb") as salida:
            for trozo in respuesta.iter_bytes(_TROZO):
                salida.write(trozo)
                resumen.update(trozo)
                total += len(trozo)
    final = carpeta / nombre
    temporal.replace(final)
    return ArchivoDescargado(
        archivo=nombre,
        url=recurso.url,
        bytes=total,
        sha256=resumen.hexdigest(),
        descargado=datetime.now(UTC).isoformat(timespec="seconds"),
    )
