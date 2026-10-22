"""Proyección local en metros para la RM.

Equirectangular centrada en Santiago: el error es menor al 1% en toda la región,
suficiente para distancias de caminata, áreas y búsqueda de vecinos.
"""

import numpy as np
import numpy.typing as npt

Arreglo = npt.NDArray[np.float64]

LAT0 = -33.45
M_POR_GRADO_LAT = 110_574.0
M_POR_GRADO_LON = 111_320.0 * float(np.cos(np.radians(LAT0)))


def proyectar(lat: npt.ArrayLike, lon: npt.ArrayLike) -> tuple[Arreglo, Arreglo]:
    """Grados a metros: devuelve (x, y)."""
    return np.asarray(lon, float) * M_POR_GRADO_LON, np.asarray(lat, float) * M_POR_GRADO_LAT


def desproyectar(x: npt.ArrayLike, y: npt.ArrayLike) -> tuple[Arreglo, Arreglo]:
    """Metros a grados: devuelve (lat, lon)."""
    return np.asarray(y, float) / M_POR_GRADO_LAT, np.asarray(x, float) / M_POR_GRADO_LON


def lonlat_a_metros(coordenadas: Arreglo) -> Arreglo:
    """Arreglo N×2 de (lon, lat) a (x, y) en metros (para transformar geometrías)."""
    x, y = proyectar(coordenadas[:, 1], coordenadas[:, 0])
    return np.column_stack([x, y])
