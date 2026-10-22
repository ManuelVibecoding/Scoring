"""Caso de uso: arriendos alrededor de un punto, con scraping bajo demanda y caché.

Para cada portal, si la comuna del punto se consultó hace menos de `vigencia`, se usa la
caché; si no, se consulta el portal (de segundos a un par de minutos) y se guarda.
"""

from collections.abc import Sequence
from datetime import datetime, timedelta

from score.domain.avisos import Operacion, PortalDeAvisos, TipoPropiedad
from score.domain.precios import ResumenPrecios, resumir
from score.services.puertos import CacheAvisos

VIGENCIA = timedelta(days=7)
RADIO_M = 800.0
_GRADOS_POR_METRO = 1 / 111_000


def actualizar_comuna(
    cache: CacheAvisos,
    portales: Sequence[PortalDeAvisos],
    comuna: str,
    ahora: datetime,
    vigencia: timedelta = VIGENCIA,
) -> datetime | None:
    """Vuelve a consultar lo que esté vencido. Devuelve la fecha del dato más antiguo."""
    fechas = []
    for portal in portales:
        for tipo in TipoPropiedad:
            consultado = cache.consultado_en(portal.nombre, comuna, tipo)
            if consultado is None or ahora - consultado > vigencia:
                avisos = portal.avisos_de_comuna(comuna, Operacion.ARRIENDO, tipo)
                cache.guardar(portal.nombre, comuna, tipo, avisos, ahora)
                consultado = ahora
            fechas.append(consultado)
    return min(fechas) if fechas else None


def precios_cercanos(
    cache: CacheAvisos,
    portales: Sequence[PortalDeAvisos],
    comuna: str,
    lat: float,
    lon: float,
    ahora: datetime,
    radio_m: float = RADIO_M,
    vigencia: timedelta = VIGENCIA,
) -> tuple[ResumenPrecios, datetime | None]:
    """Resumen de precios y la fecha del dato más antiguo usado."""
    fecha = actualizar_comuna(cache, portales, comuna, ahora, vigencia)
    margen = radio_m * _GRADOS_POR_METRO * 1.5
    candidatos = cache.en_rectangulo(lat - margen, lat + margen, lon - margen, lon + margen)
    return resumir(candidatos, lat, lon, radio_m), fecha
