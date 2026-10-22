"""Resumen de precios de arriendo alrededor de un punto."""

import math
import statistics
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
class ResumenPrecios:
    radio_m: float
    avisos: int
    mediana_arriendo_clp: float | None
    mediana_clp_m2: float | None
    mediana_por_dormitorios: dict[int, float] = field(default_factory=dict)
    ejemplos: list[AvisoCercano] = field(default_factory=list)


def _mediana(valores: list[float]) -> float | None:
    return statistics.median(valores) if valores else None


def resumir(
    avisos: list[Aviso], lat: float, lon: float, radio_m: float, ejemplos: int = 5
) -> ResumenPrecios:
    """Avisos a menos de `radio_m` del punto: medianas generales y por dormitorios."""
    cercanos = sorted(
        (AvisoCercano(a, distancia_m(lat, lon, a.lat, a.lon)) for a in avisos),
        key=lambda c: c.distancia_m,
    )
    cercanos = [c for c in cercanos if c.distancia_m <= radio_m and c.aviso.precio_clp]
    por_dormitorios: dict[int, list[float]] = {}
    for c in cercanos:
        if c.aviso.dormitorios and c.aviso.precio_clp:
            clave = min(c.aviso.dormitorios, 4)
            por_dormitorios.setdefault(clave, []).append(c.aviso.precio_clp)
    return ResumenPrecios(
        radio_m=radio_m,
        avisos=len(cercanos),
        mediana_arriendo_clp=_mediana([c.aviso.precio_clp for c in cercanos if c.aviso.precio_clp]),
        mediana_clp_m2=_mediana([m for c in cercanos if (m := c.aviso.clp_por_m2) is not None]),
        mediana_por_dormitorios={
            d: statistics.median(v) for d, v in sorted(por_dormitorios.items()) if len(v) >= 2
        },
        ejemplos=cercanos[:ejemplos],
    )
