"""Arma los portales de avisos con sus dependencias (cliente HTTP, geocodificador, UF)."""

from functools import cache
from pathlib import Path

import httpx
import pandas as pd

from score.adapters.geocodificador_local import GeocodificadorLocal
from score.adapters.portal_inmobiliario import PortalInmobiliario
from score.adapters.toctoc import TocToc
from score.adapters.uf_sii import valor_uf
from score.domain.avisos import PortalDeAvisos


def crear_portales(cliente: httpx.Client, procesados: Path) -> list[PortalDeAvisos]:
    comunas = pd.read_parquet(procesados / "comunas.parquet")
    cut_de_comuna = {str(nombre): int(str(cut)) for cut, nombre in comunas["comuna"].items()}

    @cache
    def uf() -> float:
        return valor_uf(cliente)

    return [
        TocToc(cliente),
        PortalInmobiliario(
            cliente, GeocodificadorLocal.desde_archivos(procesados), cut_de_comuna, uf
        ),
    ]
