"""Repositorio de puntajes sobre los Parquet generados por el pipeline (todo en memoria)."""

import json
from functools import cached_property
from pathlib import Path
from typing import Any

import duckdb
import h3
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from score.domain.modelo import MODELO
from score.pipeline.hexagonos import RESOLUCION_H3
from score.pipeline.red import proyectar

# Más lejos que esto del hexágono habitado más cercano, el punto no se evalúa.
DISTANCIA_MAXIMA_M = 1_500.0


class RepositorioParquet:
    def __init__(self, procesados: Path, cartografia: Path) -> None:
        self._puntajes = pd.read_parquet(procesados / "puntajes.parquet").set_index("h3")
        self._comunas = pd.read_parquet(procesados / "comunas.parquet")
        self._cartografia = cartografia
        x, y = proyectar(self._puntajes["lat"].to_numpy(), self._puntajes["lon"].to_numpy())
        self._arbol = cKDTree(np.column_stack([x, y]))

    def hexagono_mas_cercano(self, lat: float, lon: float) -> tuple[pd.Series, float] | None:
        celda = h3.latlng_to_cell(lat, lon, RESOLUCION_H3)
        if celda in self._puntajes.index:
            return self._puntajes.loc[celda], 0.0
        x, y = proyectar(np.array([lat]), np.array([lon]))
        distancia, indice = self._arbol.query([x[0], y[0]])
        if distancia > DISTANCIA_MAXIMA_M:
            return None
        return self._puntajes.iloc[int(indice)], float(distancia)

    def comuna(self, cut: int) -> pd.Series | None:
        if cut not in self._comunas.index:
            return None
        fila = self._comunas.loc[cut]
        return fila if isinstance(fila, pd.Series) else None

    @cached_property
    def _medianas(self) -> dict[str, float]:
        pesos = self._puntajes["personas"].fillna(0)
        medianas = {}
        for d in MODELO:
            orden = self._puntajes[d.id].dropna().sort_values()
            acumulado = pesos[orden.index].cumsum()
            medianas[d.id] = float(orden[acumulado >= acumulado.iloc[-1] / 2].iloc[0])
        return medianas

    def medianas(self) -> dict[str, float]:
        return self._medianas

    def capa(self) -> pd.DataFrame:
        columnas = ["puntaje", "letra", *(d.id for d in MODELO)]
        return self._puntajes[columnas].round(1)

    @cached_property
    def _geojson_comunas(self) -> dict[str, Any]:
        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        filas = con.execute(
            f"""
            SELECT CUT, COMUNA,
                   ST_AsGeoJSON(ST_SimplifyPreserveTopology(SHAPE, 0.0004)) AS geometria
            FROM '{self._cartografia.as_posix()}'
            """
        ).fetchall()
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"cut": cut, "comuna": nombre},
                    "geometry": json.loads(geometria),
                }
                for cut, nombre, geometria in filas
            ],
        }

    def contorno_comunas(self) -> dict[str, Any]:
        return self._geojson_comunas
