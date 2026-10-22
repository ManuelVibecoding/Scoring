"""Motor de cercanías: responde en cualquier coordenada de la RM, no solo en hexágonos.

El pipeline corre un Dijkstra por categoría sobre toda la red de calles y guarda, para
cada nodo (esquina o vértice), los minutos al lugar más cercano y cuál es. Para un punto
cualquiera basta con encontrar su nodo más cercano y sumar el tramo hasta él: la
respuesta es inmediata y propia de ese punto.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import h3
import numpy as np
import numpy.typing as npt
import pandas as pd
from scipy.sparse import csr_matrix, load_npz
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

from score.domain.geo import desproyectar, proyectar
from score.pipeline.medidas import (
    CONTEOS_800M,
    DESAMENIDADES,
    MEDIDAS,
    MINUTOS_MAXIMOS,
    RADIO_BUSES_M,
    RADIO_CONTEO_M,
)
from score.pipeline.red import VELOCIDAD_PEATON_M_MIN, Modo, minutos_de_acceso

RESOLUCION_ISOCRONA = 10  # hexágonos H3 de ~65 m de lado: contorno suave a escala de cuadra


@dataclass(frozen=True)
class MedidaPrecalculada:
    """Para cada nodo de la red: minutos al lugar más cercano e índice de ese lugar."""

    minutos: npt.NDArray[np.floating[Any]]
    lugar: npt.NDArray[np.int32]
    nombres: npt.NDArray[np.object_]


class MotorCercanias:
    def __init__(
        self,
        nodos: dict[Modo, npt.NDArray[np.float32]],
        medidas: dict[str, MedidaPrecalculada],
        puntos: pd.DataFrame,
        vias_rapidas: pd.DataFrame,
        grafo_pie: csr_matrix | None = None,
    ) -> None:
        self._nodos = nodos
        self._arboles = {modo: cKDTree(xy) for modo, xy in nodos.items()}
        self._medidas = medidas
        self._grafo_pie = grafo_pie
        self._conteos = {
            id_: _arbol(puntos[puntos["categoria"].isin(categorias)])
            for id_, categorias in CONTEOS_800M.items()
        }
        self._paraderos = puntos[puntos["categoria"] == "paradero"].reset_index(drop=True)
        self._arbol_paraderos = _arbol(self._paraderos)
        self._arbol_vias = _arbol(vias_rapidas)
        self._arbol_desamenidades = _arbol(puntos[puntos["categoria"].isin(DESAMENIDADES)])

    # ------------------------------------------------------------------ lectura

    @classmethod
    def desde_carpeta(cls, carpeta: Path, con_grafo: bool = True) -> "MotorCercanias":
        nodos = {modo: np.load(carpeta / f"nodos_{modo}.npy") for modo in Modo}
        medidas = {
            m.id: MedidaPrecalculada(
                minutos=np.load(carpeta / f"{m.id}_minutos.npy", mmap_mode="r"),
                lugar=np.load(carpeta / f"{m.id}_lugar.npy", mmap_mode="r"),
                nombres=pd.read_parquet(carpeta / f"{m.id}_lugares.parquet")["nombre"].to_numpy(
                    dtype=object
                ),
            )
            for m in MEDIDAS
        }
        grafo = csr_matrix(load_npz(carpeta / "grafo_pie.npz")) if con_grafo else None
        return cls(
            nodos,
            medidas,
            pd.read_parquet(carpeta / "puntos.parquet"),
            pd.read_parquet(carpeta / "vias_rapidas.parquet"),
            grafo,
        )

    # ------------------------------------------------------------------ consultas

    def evaluar(self, lat: npt.ArrayLike, lon: npt.ArrayLike) -> pd.DataFrame:
        """Indicadores de cercanía para uno o muchos puntos (una fila por punto)."""
        x, y = proyectar(
            np.atleast_1d(np.asarray(lat, float)), np.atleast_1d(np.asarray(lon, float))
        )
        xy = np.column_stack([x, y])
        resultado: dict[str, Any] = {}
        ajustes: dict[Modo, tuple[npt.NDArray[np.int64], npt.NDArray[np.float64]]] = {}
        for modo, arbol_red in self._arboles.items():
            distancia_red, nodo_red = arbol_red.query(xy)
            ajustes[modo] = (np.asarray(nodo_red, np.int64), np.asarray(distancia_red, float))

        for medida in MEDIDAS:
            datos = self._medidas[medida.id]
            nodo, separacion = ajustes[medida.modo]
            minutos = np.asarray(datos.minutos[nodo], float) + minutos_de_acceso(
                medida.modo, separacion
            )
            alcanzable = np.isfinite(minutos) & (minutos <= MINUTOS_MAXIMOS)
            indice = np.asarray(datos.lugar[nodo])
            nombres = datos.nombres[np.maximum(indice, 0)].copy()
            nombres[~alcanzable | (indice < 0)] = None
            resultado[f"min_{medida.id}"] = np.where(alcanzable, minutos, np.nan).round(1)
            resultado[f"cerca_{medida.id}"] = nombres

        for id_, arbol_conteo in self._conteos.items():
            resultado[f"n800_{id_}"] = (
                arbol_conteo.query_ball_point(xy, RADIO_CONTEO_M, return_length=True)
                if arbol_conteo
                else np.zeros(len(xy), int)
            )
        resultado.update(self._buses(xy))
        resultado["m_via_rapida"] = _distancia(self._arbol_vias, xy).round()
        resultado["m_desamenidad"] = _distancia(self._arbol_desamenidades, xy).round()
        return pd.DataFrame(resultado)

    def _buses(self, xy: npt.NDArray[np.float64]) -> dict[str, list[float]]:
        if self._arbol_paraderos is None:
            return {"recorridos_400m": [0.0] * len(xy), "buses_hora_max_400m": [0.0] * len(xy)}
        cercanos = cast(list[list[int]], self._arbol_paraderos.query_ball_point(xy, RADIO_BUSES_M))
        recorridos = self._paraderos["recorridos"].to_numpy()
        frecuencia = self._paraderos["salidas_hora"].fillna(0).to_numpy()
        return {
            "recorridos_400m": [
                float(len({r for i in idx if recorridos[i] is not None for r in recorridos[i]}))
                for idx in cercanos
            ],
            "buses_hora_max_400m": [
                round(float(frecuencia[idx].max()), 1) if idx else 0.0 for idx in cercanos
            ],
        }

    def isocrona(
        self, lat: float, lon: float, bandas: tuple[int, ...] = (5, 10, 15)
    ) -> dict[str, Any]:
        """Áreas alcanzables a pie en cada banda de minutos (GeoJSON, de mayor a menor)."""
        if self._grafo_pie is None:
            raise RuntimeError("El motor se cargó sin la red peatonal")
        x, y = proyectar(np.array([lat]), np.array([lon]))
        separacion, nodo = self._arboles[Modo.PIE].query([x[0], y[0]])
        limite = max(bandas) * VELOCIDAD_PEATON_M_MIN
        metros = dijkstra(self._grafo_pie, indices=int(nodo), limit=limite) + float(separacion)
        xy = self._nodos[Modo.PIE]
        features = []
        for banda in sorted(bandas, reverse=True):
            dentro = np.flatnonzero(metros <= banda * VELOCIDAD_PEATON_M_MIN)
            if len(dentro) == 0:
                continue
            lats, lons = desproyectar(xy[dentro, 0], xy[dentro, 1])
            celdas = {
                h3.latlng_to_cell(a, o, RESOLUCION_ISOCRONA)
                for a, o in zip(lats, lons, strict=True)
            }
            forma = h3.cells_to_h3shape(list(celdas))
            features.append(
                {
                    "type": "Feature",
                    "properties": {"minutos": banda},
                    "geometry": forma.__geo_interface__,
                }
            )
        return {"type": "FeatureCollection", "features": features}


def _arbol(puntos: pd.DataFrame) -> cKDTree | None:
    if len(puntos) == 0:
        return None
    return cKDTree(np.column_stack(proyectar(puntos["lat"].to_numpy(), puntos["lon"].to_numpy())))


def _distancia(arbol: cKDTree | None, xy: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    if arbol is None:
        return np.full(len(xy), np.inf)
    distancia, _ = arbol.query(xy)
    return np.asarray(distancia, dtype=float)
