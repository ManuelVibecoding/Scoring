"""Registro de fuentes de datos: qué se descarga, de dónde y bajo qué licencia.

Cada fuente declara sus recursos. La mayoría son URLs fijas; algunas (como BIDAT)
publican enlaces que cambian, y se resuelven leyendo la página de la fuente.
"""

import re
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass, field

import httpx


@dataclass(frozen=True)
class Recurso:
    """Un archivo a descargar. Sin nombre, se usa el que entrega el servidor."""

    url: str
    archivo: str | None = None


ResolverRecursos = Callable[[httpx.Client], list[Recurso]]


@dataclass(frozen=True)
class Fuente:
    id: str
    nombre: str
    institucion: str
    pagina: str
    licencia: str
    descripcion: str
    recursos: list[Recurso] = field(default_factory=list)
    resolver: ResolverRecursos | None = None
    pesada: bool = False

    def obtener_recursos(self, cliente: httpx.Client) -> list[Recurso]:
        return self.resolver(cliente) if self.resolver else list(self.recursos)


def enlaces_de_pagina(cliente: httpx.Client, pagina: str, patron: str) -> list[str]:
    """Devuelve los enlaces de una página que coinciden con un patrón, sin repetir."""
    html = cliente.get(pagina).raise_for_status().text
    vistos: dict[str, None] = {}
    for href in re.findall(r'href=["\']([^"\']+)["\']', html):
        absoluto = urllib.parse.urljoin(pagina, href)
        if re.search(patron, absoluto):
            vistos[absoluto] = None
    return list(vistos)


_BUCKET_CENSO = "https://storage.googleapis.com/bktdescargascenso2024"
_BIDAT_POBREZA = "https://bidat.gob.cl/details/ficha/dataset/base-de-datos-pobreza-comunal-2024"


def _recursos_pobreza_comunal(cliente: httpx.Client) -> list[Recurso]:
    enlaces = enlaces_de_pagina(cliente, _BIDAT_POBREZA, r"/contenido-web/recurso/")
    return [Recurso(url) for url in enlaces]


FUENTES: list[Fuente] = [
    Fuente(
        id="censo2024_cartografia_rm",
        nombre="Cartografía Censo 2024, Región Metropolitana",
        institucion="INE",
        pagina="https://censo2024.ine.gob.cl/resultados/",
        licencia="Datos abiertos INE",
        descripcion="Límites de manzanas, zonas, comunas y entidades (GeoParquet).",
        recursos=[
            Recurso(
                f"{_BUCKET_CENSO}/Cartografia/GEOPARQUET/"
                + urllib.parse.quote("Cartografía_censo2024_R13.zip"),
                "cartografia_censo2024_R13.zip",
            )
        ],
    ),
    Fuente(
        id="censo2024_manzana_entidad",
        nombre="Base manzana–entidad Censo 2024",
        institucion="INE",
        pagina="https://censo2024.ine.gob.cl/resultados/",
        licencia="Datos abiertos INE",
        descripcion="189 variables de personas, hogares y viviendas por manzana (todo el país).",
        recursos=[
            Recurso(f"{_BUCKET_CENSO}/Datos_agregados/Base_manzana_entidad_CPV24.zip"),
            Recurso(f"{_BUCKET_CENSO}/Datos_agregados/diccionario_variables_glosas_censo2024.xlsx"),
        ],
    ),
    Fuente(
        id="minsal_establecimientos",
        nombre="Establecimientos de salud",
        institucion="IDE-Minsal",
        pagina="https://www.minsal.cl/ide-minsal-geoportal-descarga-de-datos/",
        licencia="Datos abiertos Minsal",
        descripcion="Establecimientos vigentes al 12-06-2026 (shapefile WGS84).",
        recursos=[
            Recurso(
                "https://www.minsal.cl/wp-content/uploads/2026/08/ESTABLECIMIENTOS_12062026_DES.zip"
            )
        ],
    ),
    Fuente(
        id="dtpm_gtfs",
        nombre="GTFS Red Metropolitana de Movilidad",
        institucion="DTPM",
        pagina="https://www.dtpm.cl/index.php/gtfs-vigente",
        licencia="Ver términos en dtpm.cl",
        descripcion="Buses RED, Metro, EFE y bus al aeropuerto, vigente desde el 03-10-2026.",
        recursos=[Recurso("https://www.dtpm.cl/descargas/gtfs/GTFS_20261003.zip")],
    ),
    Fuente(
        id="osm_chile",
        nombre="OpenStreetMap Chile",
        institucion="Geofabrik / OpenStreetMap",
        pagina="https://download.geofabrik.de/south-america/chile.html",
        licencia="ODbL (atribución a OpenStreetMap)",
        descripcion="Calles, puntos de interés, parques y autopistas (~333 MB).",
        recursos=[Recurso("https://download.geofabrik.de/south-america/chile-latest.osm.pbf")],
        pesada=True,
    ),
    Fuente(
        id="mineduc_directorio",
        nombre="Directorio oficial de establecimientos educacionales 2025",
        institucion="Mineduc",
        pagina="https://datosabiertos.mineduc.cl/directorio-de-establecimientos-educacionales/",
        licencia="Datos abiertos Mineduc",
        descripcion="Colegios con dependencia, matrícula y coordenadas.",
        recursos=[
            Recurso(
                "https://datosabiertos.mineduc.cl/wp-content/uploads/2025/11/Directorio-Oficial-EE-2025.rar"
            )
        ],
    ),
    Fuente(
        id="cead_delitos",
        nombre="Casos policiales por comuna (CEAD)",
        institucion="CEAD, vía extracción comunitaria de bastianolea/delincuencia_chile",
        pagina="https://github.com/bastianolea/delincuencia_chile",
        licencia="Datos públicos CEAD; código GPL-3.0",
        descripcion="Casos policiales mensuales por comuna y delito, 2010–dic 2025. "
        "Se usa mientras el sitio oficial del CEAD no permita descarga directa.",
        recursos=[
            Recurso(
                "https://github.com/bastianolea/delincuencia_chile/raw/main/"
                "datos/procesados/cead_delincuencia_chile.parquet"
            )
        ],
    ),
    Fuente(
        id="mma_ruido",
        nombre="Mapa de ruido del Gran Santiago 2023",
        institucion="Ministerio del Medio Ambiente",
        pagina="https://ruido.mma.gob.cl/mapas-de-ruido/",
        licencia="Datos abiertos MMA",
        descripcion="Niveles de ruido modelados, 35 comunas del Gran Santiago.",
        recursos=[
            Recurso(
                "https://ruido.mma.gob.cl/wp-content/uploads/2024/12/Mapa-de-Ruido-GSU-2023-MMA-2024.zip"
            )
        ],
        pesada=True,
    ),
    Fuente(
        id="casen_pobreza_comunal",
        nombre="Pobreza comunal 2024 (estimaciones SAE, Casen 2024)",
        institucion="Ministerio de Desarrollo Social y Familia",
        pagina=_BIDAT_POBREZA,
        licencia="Datos abiertos MDSF",
        descripcion="Tasa de pobreza por ingresos, pobreza multidimensional e inseguridad "
        "alimentaria por comuna.",
        resolver=_recursos_pobreza_comunal,
    ),
    Fuente(
        id="icvu",
        nombre="Índice de Calidad de Vida Urbana 2025",
        institucion="CChC + Instituto de Estudios Urbanos UC",
        pagina="https://estudiosurbanos.uc.cl/",
        licencia="Publicación académica (uso con cita)",
        descripcion="Índice comunal en 6 dimensiones; 42 comunas de la RM.",
        recursos=[
            Recurso(
                "https://estudiosurbanos.uc.cl/wp-content/uploads/2026/07/DOCUMENTO-ICVU-2025-1.pdf",
                "icvu_2025.pdf",
            )
        ],
    ),
]


def buscar_fuente(id_fuente: str) -> Fuente:
    for fuente in FUENTES:
        if fuente.id == id_fuente:
            return fuente
    disponibles = ", ".join(f.id for f in FUENTES)
    raise KeyError(f"No existe la fuente '{id_fuente}'. Disponibles: {disponibles}")
