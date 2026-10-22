"""Grilla de hexágonos H3 sobre las zonas habitadas de la RM.

Se usan hexágonos de resolución 9 (lado ~174 m, ~0,1 km²): al tocar un punto del mapa
se busca su hexágono y se leen sus indicadores precalculados. Solo se generan hexágonos
donde el Censo 2024 registra manzanas; el resto del territorio no es habitacional.
"""

from pathlib import Path

import duckdb
import h3
import numpy as np
import pandas as pd

RESOLUCION_H3 = 9


def grilla(manzanas: Path, resolucion: int = RESOLUCION_H3) -> pd.DataFrame:
    """Un hexágono por celda H3 con manzanas: población, hogares, comuna y centro."""
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    mz = con.execute(
        f"""
        SELECT CUT AS cut,
               ST_Y(ST_Centroid(SHAPE)) AS lat, ST_X(ST_Centroid(SHAPE)) AS lon,
               COALESCE(n_per, 0) AS personas, COALESCE(n_hog, 0) AS hogares,
               COALESCE(n_vp, 0) AS viviendas
        FROM '{manzanas.as_posix()}'
        """
    ).df()
    mz["h3"] = [
        h3.latlng_to_cell(lat, lon, resolucion)
        for lat, lon in zip(mz["lat"], mz["lon"], strict=True)
    ]
    # La comuna del hexágono es la que aporta más personas (o más manzanas, si no hay datos).
    peso = mz.assign(peso=mz["personas"] + 1e-3)
    por_comuna = peso.groupby(["h3", "cut"])["peso"].sum().reset_index()
    comuna = (
        por_comuna.sort_values("peso").drop_duplicates("h3", keep="last").set_index("h3")["cut"]
    )

    hexagonos = mz.groupby("h3").agg(
        personas=("personas", "sum"),
        hogares=("hogares", "sum"),
        viviendas=("viviendas", "sum"),
        manzanas=("cut", "size"),
    )
    hexagonos["cut"] = comuna
    centros = np.array([h3.cell_to_latlng(c) for c in hexagonos.index])
    hexagonos["lat"], hexagonos["lon"] = centros[:, 0], centros[:, 1]
    return hexagonos
