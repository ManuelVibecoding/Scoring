"""Muestra de avisos de arriendo de toda la RM, desde uno o varios portales.

Recorre las 52 comunas (departamentos y casas) y guarda los avisos con fecha en
data/interim/avisos/. Sirve para validar el modelo y como punto de partida de la caché
de la app.
"""

from collections.abc import Sequence
from dataclasses import asdict
from datetime import date
from pathlib import Path

import httpx
import pandas as pd

from score.domain.avisos import Operacion, PortalDeAvisos, TipoPropiedad

PATRON_MUESTRAS = "avisos_arriendo_*.parquet"


def muestrear(
    portales: Sequence[PortalDeAvisos],
    comunas: list[str],
    destino: Path,
    operacion: Operacion = Operacion.ARRIENDO,
) -> Path:
    filas: list[dict[str, object]] = []
    for portal in portales:
        for comuna in comunas:
            for tipo in TipoPropiedad:
                try:
                    avisos = portal.avisos_de_comuna(comuna, operacion, tipo)
                except httpx.HTTPError as error:
                    print(f"   {portal.nombre} {comuna} {tipo}: error {error}", flush=True)
                    continue
                print(f"   {portal.nombre} {comuna} {tipo}: {len(avisos)} avisos", flush=True)
                filas.extend({**asdict(a), "comuna_consultada": comuna} for a in avisos)
    destino.mkdir(parents=True, exist_ok=True)
    salida = destino / f"avisos_{operacion}_{date.today():%Y%m%d}.parquet"
    tabla = pd.DataFrame(filas).drop_duplicates(subset=["fuente", "id"])
    for columna in ("operacion", "tipo", "precision"):
        tabla[columna] = tabla[columna].astype(str)
    tabla["fecha_muestra"] = date.today().isoformat()
    tabla.to_parquet(salida)
    return salida


def ultima_muestra(carpeta: Path) -> Path | None:
    muestras = sorted(carpeta.glob(PATRON_MUESTRAS))
    return muestras[-1] if muestras else None
