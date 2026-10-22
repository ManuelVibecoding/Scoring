"""Índice de direcciones de la RM para geocodificar avisos sin depender de un servicio externo.

A partir de OpenStreetMap genera:
- direcciones.parquet: calle normalizada, número, comuna (CUT) y coordenadas
- calles.parquet:      vértices de cada calle con nombre, por comuna (para ubicar por calle)
"""

import re
from pathlib import Path

import duckdb
import pandas as pd

from score.domain.direcciones import normalizar_calle


def _numero(texto: str) -> int | None:
    """'1301', '1301-A', '1301 B' → 1301."""
    coincidencia = re.match(r"\s*(\d{1,5})", str(texto))
    return int(coincidencia.group(1)) if coincidencia else None


def _con_comuna(con: duckdb.DuckDBPyConnection, tabla: pd.DataFrame, comunal: Path) -> pd.DataFrame:
    con.register("puntos", tabla)
    resultado = con.execute(
        f"""
        SELECT p.*, c.CUT AS cut
        FROM puntos p
        JOIN '{comunal.as_posix()}' c ON ST_Contains(c.SHAPE, ST_Point(p.lon, p.lat))
        """
    ).df()
    con.unregister("puntos")
    return resultado


def construir_indice(osm_rm: Path, comunal: Path, procesados: Path) -> tuple[Path, Path]:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")

    direcciones = pd.read_parquet(osm_rm / "direcciones.parquet")
    direcciones["calle"] = direcciones["calle"].map(normalizar_calle)
    direcciones["numero"] = direcciones["numero"].map(_numero)
    direcciones = direcciones.dropna(subset=["numero"]).astype({"numero": int})
    direcciones = _con_comuna(con, direcciones, comunal)
    direcciones = direcciones.drop_duplicates(subset=["calle", "numero", "cut"])

    calles = con.execute(
        f"""
        SELECT v.nombre AS calle, n.lat, n.lon
        FROM '{(osm_rm / "vias.parquet").as_posix()}' v, UNNEST(v.refs) AS r(ref)
        JOIN '{(osm_rm / "nodos.parquet").as_posix()}' n ON n.id = r.ref
        WHERE v.nombre IS NOT NULL
        """
    ).df()
    calles["calle"] = calles["calle"].map(normalizar_calle)
    calles = _con_comuna(con, calles, comunal)

    procesados.mkdir(parents=True, exist_ok=True)
    salida_dir, salida_calles = procesados / "direcciones.parquet", procesados / "calles.parquet"
    direcciones[["calle", "numero", "cut", "lat", "lon"]].to_parquet(salida_dir)
    calles[["calle", "cut", "lat", "lon"]].to_parquet(salida_calles)
    return salida_dir, salida_calles
