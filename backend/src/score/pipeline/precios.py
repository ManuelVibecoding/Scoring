"""Muestra de avisos de arriendo de toda la RM, para validar el puntaje contra el mercado.

Recorre las 52 comunas (departamentos y casas) en un portal y guarda los avisos con
fecha en data/interim/avisos/. No es el scraping bajo demanda de la app: es una foto
del mercado para calibrar el modelo.
"""

from dataclasses import asdict
from datetime import date
from pathlib import Path

import httpx
import pandas as pd

from score.domain.avisos import Operacion, PortalDeAvisos, TipoPropiedad


def muestrear(
    portal: PortalDeAvisos,
    comunas: list[str],
    destino: Path,
    operacion: Operacion = Operacion.ARRIENDO,
) -> Path:
    filas: list[dict[str, object]] = []
    for comuna in comunas:
        for tipo in TipoPropiedad:
            try:
                avisos = portal.avisos_de_comuna(comuna, operacion, tipo)
            except httpx.HTTPError as error:
                print(f"   {comuna} {tipo}: error {error}")
                continue
            print(f"   {comuna} {tipo}: {len(avisos)} avisos")
            filas.extend({**asdict(a), "comuna_consultada": comuna} for a in avisos)
    destino.mkdir(parents=True, exist_ok=True)
    salida = destino / f"{portal.nombre}_{operacion}_{date.today():%Y%m%d}.parquet"
    tabla = pd.DataFrame(filas).drop_duplicates(subset=["fuente", "id"])
    tabla["fecha_muestra"] = date.today().isoformat()
    tabla.to_parquet(salida)
    return salida
