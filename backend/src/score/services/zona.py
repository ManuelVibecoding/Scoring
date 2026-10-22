"""Caso de uso: informe de una zona dibujada en el mapa (polígono, rectángulo o círculo)."""

from dataclasses import dataclass
from typing import Any

import shapely
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from score.domain.geo import lonlat_a_metros
from score.domain.modelo import MODELO
from score.domain.precios import EstadisticasPrecios, estadisticas, utiles
from score.domain.veredicto import redactar
from score.domain.zona import ResumenZona, resumir_zona
from score.services.puertos import CacheAvisos, RepositorioPuntajes

# Lo que se cuenta dentro de la zona: (etiqueta, categorías del catálogo).
LUGARES_ZONA: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("metro", "Estaciones de Metro", ("metro",)),
    ("paradero", "Paraderos de bus", ("paradero",)),
    ("colegio", "Colegios", ("colegio",)),
    ("jardin", "Jardines infantiles", ("jardin",)),
    ("salud", "CESFAM y urgencias", ("cesfam", "urgencia")),
    ("supermercado", "Supermercados", ("supermercado",)),
    ("farmacia", "Farmacias", ("farmacia",)),
    ("comercio", "Restaurantes y cafés", ("restaurante", "cafe")),
)
AREA_MAXIMA_KM2 = 400.0


class ZonaInvalidaError(ValueError):
    pass


@dataclass(frozen=True)
class LugaresZona:
    id: str
    etiqueta: str
    cantidad: int


@dataclass(frozen=True)
class InformeZona:
    area_km2: float
    resumen: ResumenZona
    veredicto: str
    lugares: list[LugaresZona]
    precios: EstadisticasPrecios


def leer_zona(geometria: dict[str, Any]) -> BaseGeometry:
    try:
        zona = shape(geometria)
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ZonaInvalidaError("La zona no es un polígono GeoJSON válido.") from error
    if zona.geom_type not in ("Polygon", "MultiPolygon") or zona.is_empty:
        raise ZonaInvalidaError("La zona tiene que ser un polígono.")
    return zona if zona.is_valid else zona.buffer(0)


def area_km2(zona: BaseGeometry) -> float:
    return float(shapely.transform(zona, lonlat_a_metros).area) / 1e6


def informe_zona(
    repo: RepositorioPuntajes, cache: CacheAvisos, geometria: dict[str, Any]
) -> InformeZona:
    zona = leer_zona(geometria)
    area = area_km2(zona)
    if area > AREA_MAXIMA_KM2:
        raise ZonaInvalidaError(
            f"La zona es demasiado grande ({area:.0f} km²); el máximo es 400 km²."
        )

    resumen = resumir_zona(repo.hexagonos_en(zona), MODELO, repo.medianas())
    conteos = repo.contar_lugares_en(zona)

    lon_min, lat_min, lon_max, lat_max = zona.bounds
    candidatos = cache.en_rectangulo(lat_min, lat_max, lon_min, lon_max)
    dentro = [a for a in candidatos if shapely.contains_xy(zona, a.lon, a.lat)]

    return InformeZona(
        area_km2=round(area, 2),
        resumen=resumen,
        veredicto=redactar(resumen.letra, resumen.fortalezas, resumen.debilidades),
        lugares=[
            LugaresZona(id_, etiqueta, sum(conteos.get(c, 0) for c in categorias))
            for id_, etiqueta, categorias in LUGARES_ZONA
        ],
        precios=estadisticas(utiles(dentro)),
    )
