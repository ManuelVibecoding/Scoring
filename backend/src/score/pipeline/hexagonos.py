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


def _cociente(numerador: pd.Series, denominador: pd.Series) -> pd.Series:
    """División que deja vacío (NaN) cuando no hay base para calcular."""
    return (numerador / denominador.where(denominador > 0)).astype(float)


def grilla(manzanas: Path, resolucion: int = RESOLUCION_H3) -> pd.DataFrame:
    """Un hexágono por celda H3 con manzanas: población, hogares, comuna, centro e
    indicadores socio-materiales (escolaridad, hacinamiento, educación superior).

    Las manzanas con datos reservados por el INE no aportan a los promedios.
    """
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    adultos = "(n_edad_18_24 + n_edad_25_44 + n_edad_45_59 + n_edad_60_mas)"
    cine = (
        "(n_cine_nunca_curso_primera_infancia + n_cine_primaria + n_cine_secundaria"
        " + n_cine_terciaria_maestria_doctorado + n_cine_especial_diferencial)"
    )
    mz = con.execute(
        f"""
        SELECT CUT AS cut,
               ST_Y(ST_Centroid(SHAPE)) AS lat, ST_X(ST_Centroid(SHAPE)) AS lon,
               COALESCE(n_per, 0) AS personas, COALESCE(n_hog, 0) AS hogares,
               COALESCE(n_vp, 0) AS viviendas,
               prom_escolaridad18 * {adultos} AS escolaridad_x_adultos,
               CASE WHEN prom_escolaridad18 IS NOT NULL THEN {adultos} END AS adultos,
               CASE WHEN n_vp_ocupada > 0 THEN n_viv_hacinadas END AS hacinadas,
               CASE WHEN n_viv_hacinadas IS NOT NULL THEN n_vp_ocupada END AS ocupadas,
               n_cine_terciaria_maestria_doctorado AS terciaria,
               CASE WHEN n_cine_terciaria_maestria_doctorado IS NOT NULL THEN {cine} END
                   AS con_nivel_educativo
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
        escolaridad_x_adultos=("escolaridad_x_adultos", "sum"),
        adultos=("adultos", "sum"),
        hacinadas=("hacinadas", "sum"),
        ocupadas=("ocupadas", "sum"),
        terciaria=("terciaria", "sum"),
        con_nivel_educativo=("con_nivel_educativo", "sum"),
    )
    hexagonos["escolaridad_hex"] = _cociente(
        hexagonos["escolaridad_x_adultos"], hexagonos["adultos"]
    )
    hexagonos["pct_hacinamiento_hex"] = _cociente(hexagonos["hacinadas"], hexagonos["ocupadas"])
    hexagonos["pct_educacion_superior_hex"] = _cociente(
        hexagonos["terciaria"], hexagonos["con_nivel_educativo"]
    )
    hexagonos = hexagonos.drop(
        columns=[
            "escolaridad_x_adultos",
            "adultos",
            "hacinadas",
            "ocupadas",
            "terciaria",
            "con_nivel_educativo",
        ]
    )
    hexagonos["cut"] = comuna
    centros = np.array([h3.cell_to_latlng(c) for c in hexagonos.index])
    hexagonos["lat"], hexagonos["lon"] = centros[:, 0], centros[:, 1]
    return hexagonos
