"""Caso de uso: arriendos alrededor de un punto, con los avisos que dejó el último scraper.

La app nunca consulta los portales por su cuenta: los datos se actualizan solo cuando se
corre `score precios` (D-030).
"""

from score.domain.precios import ResumenPrecios, resumir
from score.services.puertos import AvisosDeArriendo

RADIO_M = 800.0
_GRADOS_POR_METRO = 1 / 111_000


def precios_cercanos(
    avisos: AvisosDeArriendo, lat: float, lon: float, radio_m: float = RADIO_M
) -> ResumenPrecios:
    margen = radio_m * _GRADOS_POR_METRO * 1.5
    candidatos = avisos.en_rectangulo(lat - margen, lat + margen, lon - margen, lon + margen)
    return resumir(candidatos, lat, lon, radio_m)
