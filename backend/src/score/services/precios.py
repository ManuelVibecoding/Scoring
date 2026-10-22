"""Caso de uso: arriendos alrededor de un punto, con scraping bajo demanda y caché.

Si la comuna del punto se consultó hace menos de `vigencia`, se usa la caché; si no, se
consulta el portal (unos segundos por tipo de propiedad) y se guarda.
"""

from datetime import datetime, timedelta

from score.domain.avisos import Operacion, PortalDeAvisos, TipoPropiedad
from score.domain.precios import ResumenPrecios, resumir
from score.services.puertos import CacheAvisos

VIGENCIA = timedelta(days=7)
RADIO_M = 800.0
_GRADOS_POR_METRO = 1 / 111_000


def precios_cercanos(
    cache: CacheAvisos,
    portal: PortalDeAvisos,
    comuna: str,
    lat: float,
    lon: float,
    ahora: datetime,
    radio_m: float = RADIO_M,
    vigencia: timedelta = VIGENCIA,
) -> tuple[ResumenPrecios, datetime | None]:
    """Resumen de precios y la fecha del dato más antiguo usado."""
    fechas = []
    for tipo in TipoPropiedad:
        consultado = cache.consultado_en(comuna, tipo)
        if consultado is None or ahora - consultado > vigencia:
            avisos = portal.avisos_de_comuna(comuna, Operacion.ARRIENDO, tipo)
            cache.guardar(comuna, tipo, avisos, ahora)
            consultado = ahora
        fechas.append(consultado)

    margen = radio_m * _GRADOS_POR_METRO * 1.5
    candidatos = cache.en_rectangulo(lat - margen, lat + margen, lon - margen, lon + margen)
    return resumir(candidatos, lat, lon, radio_m), min(fechas) if fechas else None
