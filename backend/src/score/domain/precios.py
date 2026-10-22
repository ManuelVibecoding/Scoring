"""Resúmenes de precios de arriendo: alrededor de un punto o dentro de una zona."""

import math
import statistics
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field

from score.domain.avisos import Aviso

RADIO_TIERRA_M = 6_371_000.0


def distancia_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en línea recta (haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * RADIO_TIERRA_M * math.asin(math.sqrt(a))


@dataclass(frozen=True)
class AvisoCercano:
    aviso: Aviso
    distancia_m: float


@dataclass(frozen=True)
class EstadisticasPrecios:
    avisos: int
    mediana_arriendo_clp: float | None
    mediana_clp_m2: float | None
    mediana_por_dormitorios: dict[int, float] = field(default_factory=dict)
    por_fuente: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ResumenPrecios(EstadisticasPrecios):
    radio_m: float = 0.0
    ejemplos: list[AvisoCercano] = field(default_factory=list)


# Dos avisos se consideran el mismo (publicado en dos portales) si están a menos de esto,
# con el mismo número de dormitorios y un precio que difiere en menos de 2%.
_DISTANCIA_DUPLICADO_M = 80.0


def _es_duplicado(a: Aviso, b: Aviso) -> bool:
    if a.fuente == b.fuente or a.dormitorios != b.dormitorios:
        return False
    if not a.precio_clp or not b.precio_clp:
        return False
    if abs(a.precio_clp - b.precio_clp) > 0.02 * max(a.precio_clp, b.precio_clp):
        return False
    return distancia_m(a.lat, a.lon, b.lat, b.lon) <= _DISTANCIA_DUPLICADO_M


def utiles(avisos: Iterable[Aviso]) -> list[Aviso]:
    """Avisos con precio y ubicados con confianza, sin repetir uno publicado en dos portales."""
    elegidos: list[Aviso] = []
    for a in avisos:
        if (
            a.ubicacion_confiable
            and a.precio_clp
            and not any(_es_duplicado(a, e) for e in elegidos)
        ):
            elegidos.append(a)
    return elegidos


def estadisticas(avisos: list[Aviso]) -> EstadisticasPrecios:
    """Medianas generales, por m² y por dormitorios (con al menos 2 avisos por grupo)."""
    por_dormitorios: dict[int, list[float]] = {}
    for a in avisos:
        if a.dormitorios and a.precio_clp:
            por_dormitorios.setdefault(min(a.dormitorios, 4), []).append(a.precio_clp)
    precios = [a.precio_clp for a in avisos if a.precio_clp]
    por_m2 = [m for a in avisos if (m := a.clp_por_m2) is not None]
    return EstadisticasPrecios(
        avisos=len(avisos),
        mediana_arriendo_clp=statistics.median(precios) if precios else None,
        mediana_clp_m2=statistics.median(por_m2) if por_m2 else None,
        mediana_por_dormitorios={
            d: statistics.median(v) for d, v in sorted(por_dormitorios.items()) if len(v) >= 2
        },
        por_fuente=dict(Counter(a.fuente for a in avisos)),
    )


def resumir(
    avisos: list[Aviso], lat: float, lon: float, radio_m: float, ejemplos: int = 5
) -> ResumenPrecios:
    """Avisos a menos de `radio_m` del punto: medianas y los más cercanos como ejemplo."""
    ordenados = sorted(
        (AvisoCercano(a, distancia_m(lat, lon, a.lat, a.lon)) for a in avisos),
        key=lambda c: c.distancia_m,
    )
    dentro = [c for c in ordenados if c.distancia_m <= radio_m]
    elegidos = utiles(c.aviso for c in dentro)
    cercanos = [c for c in dentro if c.aviso in elegidos]
    base = estadisticas(elegidos)
    return ResumenPrecios(
        avisos=base.avisos,
        mediana_arriendo_clp=base.mediana_arriendo_clp,
        mediana_clp_m2=base.mediana_clp_m2,
        mediana_por_dormitorios=base.mediana_por_dormitorios,
        por_fuente=base.por_fuente,
        radio_m=radio_m,
        ejemplos=cercanos[:ejemplos],
    )
