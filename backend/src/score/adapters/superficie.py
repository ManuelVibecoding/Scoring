"""Superficie continua del puntaje (imagen PNG) para dibujar como mapa de calor.

Los valores por hexágono se llevan a una grilla regular (en Web Mercator, para que calce
con el mapa) y se suavizan con un filtro gaussiano normalizado: sin bordes de hexágono y
sin color donde no hay viviendas.
"""

import io
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd
from PIL import Image
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree

from score.domain.geo import proyectar

# Escala divergente con los colores de la marca: rojo (peor) → claro → negro (mejor).
# Los cortes se ajustan a cada capa: el 10% peor de la población en rojo, la mediana en
# claro y el 10% mejor en negro. Así cada dimensión muestra contraste dentro de la RM.
ROJO, CLARO, NEGRO = (226, 35, 26), (238, 232, 226), (17, 17, 17)
CUANTILES = (0.10, 0.50, 0.90)


@dataclass(frozen=True)
class Grilla:
    lats: npt.NDArray[np.float64]  # una por fila, de norte a sur
    lons: npt.NDArray[np.float64]  # una por columna, de oeste a este

    @property
    def esquinas(self) -> list[list[float]]:
        """Esquinas para MapLibre, en orden: NO, NE, SE, SO."""
        norte, sur = float(self.lats[0]), float(self.lats[-1])
        oeste, este = float(self.lons[0]), float(self.lons[-1])
        return [[oeste, norte], [este, norte], [este, sur], [oeste, sur]]


def _mercator_y(lat: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))


def _lat_de_mercator(y: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return np.degrees(2 * np.arctan(np.exp(y)) - np.pi / 2)


def grilla_para(
    lat: npt.ArrayLike, lon: npt.ArrayLike, resolucion_m: float, margen_m: float
) -> Grilla:
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    grados_lat, grados_lon = margen_m / 110_574, margen_m / 92_850
    norte, sur = lat.max() + grados_lat, lat.min() - grados_lat
    oeste, este = lon.min() - grados_lon, lon.max() + grados_lon
    columnas = int((este - oeste) * 92_850 / resolucion_m)
    filas = int((norte - sur) * 110_574 / resolucion_m)
    y = np.linspace(_mercator_y(np.array([norte]))[0], _mercator_y(np.array([sur]))[0], filas)
    return Grilla(lats=_lat_de_mercator(y), lons=np.linspace(oeste, este, columnas))


def cortes_ponderados(valores: pd.Series, pesos: pd.Series) -> tuple[float, float, float]:
    validos = valores.notna()
    orden = valores[validos].sort_values()
    acumulado = pesos[orden.index].fillna(0).cumsum()
    total = float(acumulado.iloc[-1]) or 1.0
    bajo, medio, alto = (float(orden[acumulado >= q * total].iloc[0]) for q in CUANTILES)
    return bajo, medio, max(alto, medio + 1e-6)


def colorear(
    valores: npt.NDArray[np.float64],
    presencia: npt.NDArray[np.float64],
    cortes: tuple[float, float, float],
) -> npt.NDArray[np.uint8]:
    """RGBA: color según el valor; transparencia según presencia y cuán lejos de la mediana."""
    rgba = np.zeros((*valores.shape, 4), np.uint8)
    for canal in range(3):
        rgba[..., canal] = np.interp(valores, cortes, [ROJO[canal], CLARO[canal], NEGRO[canal]])
    bajo, medio, alto = cortes
    distancia = np.clip(
        np.where(
            valores < medio,
            (medio - valores) / (medio - bajo + 1e-6),
            (valores - medio) / (alto - medio),
        ),
        0,
        1,
    )
    opacidad = (0.25 + 0.55 * distancia) * np.clip((presencia - 0.15) / 0.35, 0, 1)
    rgba[..., 3] = np.nan_to_num(opacidad * 255).astype(np.uint8)
    return rgba


class Superficies:
    def __init__(
        self, tabla: pd.DataFrame, resolucion_m: float = 90, suavizado_m: float = 200
    ) -> None:
        self._tabla = tabla
        self.grilla = grilla_para(tabla["lat"], tabla["lon"], resolucion_m, margen_m=1_500)
        self._sigma = suavizado_m / resolucion_m
        lon, lat = np.meshgrid(self.grilla.lons, self.grilla.lats)
        x, y = proyectar(lat.ravel(), lon.ravel())
        hx, hy = proyectar(tabla["lat"].to_numpy(), tabla["lon"].to_numpy())
        # Cada pixel toma el hexágono más cercano si está a menos de un lado de hexágono.
        distancia, indice = cKDTree(np.column_stack([hx, hy])).query(
            np.column_stack([x, y]), distance_upper_bound=190
        )
        self._forma = lon.shape
        self._indice = np.where(np.isfinite(distancia), indice, -1).reshape(self._forma)
        self._imagenes: dict[str, bytes] = {}

    @property
    def esquinas(self) -> list[list[float]]:
        return self.grilla.esquinas

    def png(self, variable: str) -> bytes:
        if variable not in self._imagenes:
            self._imagenes[variable] = self._dibujar(variable)
        return self._imagenes[variable]

    def _dibujar(self, variable: str) -> bytes:
        valores_hex = self._tabla[variable].to_numpy(dtype=float)
        hay = self._indice >= 0
        crudo = np.where(hay, valores_hex[np.maximum(self._indice, 0)], np.nan)
        presente = np.isfinite(crudo).astype(float)
        suma = gaussian_filter(np.nan_to_num(crudo), self._sigma)
        peso = gaussian_filter(presente, self._sigma)
        suave = np.divide(suma, peso, out=np.full_like(suma, np.nan), where=peso > 1e-6)
        cortes = cortes_ponderados(self._tabla[variable], self._tabla["personas"])
        imagen = Image.fromarray(colorear(suave, peso, cortes), mode="RGBA")
        salida = io.BytesIO()
        imagen.save(salida, format="PNG", optimize=True)
        return salida.getvalue()
