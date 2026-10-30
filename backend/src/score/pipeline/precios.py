"""Scraper de avisos de arriendo de toda la RM, desde uno o varios portales.

Recorre las 52 comunas (departamentos y casas) y guarda los avisos en un archivo con la
fecha del día en data/interim/avisos/. La app usa siempre el archivo más nuevo (D-030).

Si un portal falla en una comuna, esa comuna conserva los avisos de la corrida anterior:
una corrida a medias nunca deja a la app con menos datos que antes.
"""

from collections.abc import Sequence
from dataclasses import asdict
from datetime import date
from pathlib import Path

import pandas as pd

from score.adapters.avisos_guardados import ultima_muestra
from score.domain.avisos import Operacion, PortalDeAvisos, TipoPropiedad

_CLAVE = ["fuente", "comuna_consultada", "tipo"]


def muestrear(
    portales: Sequence[PortalDeAvisos],
    comunas: list[str],
    destino: Path,
    operacion: Operacion = Operacion.ARRIENDO,
    hoy: date | None = None,
) -> Path | None:
    """Devuelve el archivo nuevo, o None si no se obtuvo nada (queda el anterior)."""
    hoy = hoy or date.today()
    anterior = ultima_muestra(destino)
    filas: list[dict[str, object]] = []
    fallidas: list[tuple[str, str, str]] = []
    for portal in portales:
        for comuna in comunas:
            for tipo in TipoPropiedad:
                try:
                    avisos = portal.avisos_de_comuna(comuna, operacion, tipo)
                except Exception as error:  # una comuna que falla no detiene la corrida
                    print(f"   {portal.nombre} {comuna} {tipo}: error ({error})", flush=True)
                    fallidas.append((portal.nombre, comuna, str(tipo)))
                    continue
                print(f"   {portal.nombre} {comuna} {tipo}: {len(avisos)} avisos", flush=True)
                filas.extend(
                    {**asdict(a), "comuna_consultada": comuna, "fecha_consulta": hoy.isoformat()}
                    for a in avisos
                )

    tabla = pd.DataFrame(filas)
    if len(tabla):
        for columna in ("operacion", "tipo", "precision"):
            tabla[columna] = tabla[columna].astype(str)
    if fallidas and anterior is not None:
        conservados = _de_la_corrida_anterior(pd.read_parquet(anterior), fallidas)
        print(f"   Se conservan {len(conservados)} avisos anteriores de lo que falló.", flush=True)
        tabla = pd.concat([tabla, conservados], ignore_index=True)
    if tabla.empty:
        print("No se obtuvo ningún aviso: se mantienen los datos anteriores.", flush=True)
        return None

    tabla = tabla.drop_duplicates(subset=["fuente", "id"])
    tabla["fecha_muestra"] = hoy.isoformat()
    destino.mkdir(parents=True, exist_ok=True)
    salida = destino / f"avisos_{operacion}_{hoy:%Y%m%d}.parquet"
    tabla.to_parquet(salida)
    return salida


def _de_la_corrida_anterior(
    previa: pd.DataFrame, fallidas: list[tuple[str, str, str]]
) -> pd.DataFrame:
    if "fecha_consulta" not in previa.columns:
        previa = previa.assign(fecha_consulta=previa["fecha_muestra"])
    claves = pd.MultiIndex.from_frame(previa[_CLAVE].astype(str))
    buscadas = pd.MultiIndex.from_tuples(fallidas, names=_CLAVE)
    return previa[claves.isin(buscadas)].drop(columns=["fecha_muestra"])
