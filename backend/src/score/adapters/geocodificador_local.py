"""Geocodificador local sobre el índice de direcciones de OpenStreetMap (sin red).

Para "Asturias 77" en Las Condes busca, en orden:
1. el número exacto en esa calle y comuna;
2. una interpolación entre los dos números conocidos más cercanos (si no están muy lejos);
3. el centro de la calle dentro de la comuna (precisión "calle", no sirve para comparables).
Para un cruce ("Benjamín con Isidora Goyenechea") busca dónde se juntan las dos calles.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from score.domain.direcciones import Precision, separar_calle_y_numero, separar_cruce

# Si el número buscado está a más de esto de un número conocido, no se interpola.
SALTO_MAXIMO = 400
# Dos calles "se cruzan" si algún par de sus vértices está a menos de esto.
DISTANCIA_MAXIMA_CRUCE_M = 40.0
_M_POR_GRADO_LAT = 110_574.0
_M_POR_GRADO_LON = 92_850.0  # a la latitud de Santiago


@dataclass(frozen=True)
class Ubicacion:
    lat: float
    lon: float
    precision: Precision


class GeocodificadorLocal:
    def __init__(self, direcciones: pd.DataFrame, calles: pd.DataFrame) -> None:
        self._numeros: dict[tuple[str, int], tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
        for clave, g in direcciones.sort_values("numero").groupby(["calle", "cut"]):
            calle, cut = cast(tuple[str, int], clave)
            self._numeros[(str(calle), int(cut))] = (
                g["numero"].to_numpy(),
                g["lat"].to_numpy(),
                g["lon"].to_numpy(),
            )
        self._vertices: dict[tuple[str, int], np.ndarray] = {}
        for clave, g in calles.groupby(["calle", "cut"]):
            calle, cut = cast(tuple[str, int], clave)
            self._vertices[(str(calle), int(cut))] = g[["lat", "lon"]].to_numpy()

    @classmethod
    def desde_archivos(cls, procesados: Path) -> "GeocodificadorLocal":
        return cls(
            pd.read_parquet(procesados / "direcciones.parquet"),
            pd.read_parquet(procesados / "calles.parquet"),
        )

    def ubicar(self, direccion: str, cut: int) -> Ubicacion | None:
        partes = separar_calle_y_numero(direccion)
        if partes is None:
            cruce = separar_cruce(direccion)
            return self._cruce(*cruce, cut) if cruce else None
        calle, numero = partes
        conocidos = self._numeros.get((calle, cut))
        if conocidos is not None:
            ubicacion = _por_numero(numero, *conocidos)
            if ubicacion:
                return ubicacion
        vertices = self._vertices.get((calle, cut))
        if vertices is None:
            return None
        lat, lon = np.median(vertices, axis=0)
        return Ubicacion(float(lat), float(lon), Precision.CALLE)

    def _cruce(self, calle_a: str, calle_b: str, cut: int) -> Ubicacion | None:
        """Punto donde se juntan dos calles (si de verdad se cruzan en esa comuna)."""
        a, b = self._vertices.get((calle_a, cut)), self._vertices.get((calle_b, cut))
        if a is None or b is None:
            return None
        escala = np.array([_M_POR_GRADO_LAT, _M_POR_GRADO_LON])
        distancia, cercano = cKDTree(b * escala).query(a * escala)
        i = int(np.argmin(distancia))
        if distancia[i] > DISTANCIA_MAXIMA_CRUCE_M:
            return None
        lat, lon = (a[i] + b[int(cercano[i])]) / 2
        return Ubicacion(float(lat), float(lon), Precision.INTERPOLADA)


def _por_numero(
    numero: int, numeros: np.ndarray, lats: np.ndarray, lons: np.ndarray
) -> Ubicacion | None:
    i = int(np.searchsorted(numeros, numero))
    if i < len(numeros) and numeros[i] == numero:
        return Ubicacion(float(lats[i]), float(lons[i]), Precision.EXACTA)
    abajo, arriba = i - 1, i
    if abajo >= 0 and arriba < len(numeros):
        n0, n1 = numeros[abajo], numeros[arriba]
        if numero - n0 <= SALTO_MAXIMO and n1 - numero <= SALTO_MAXIMO:
            t = (numero - n0) / (n1 - n0)
            return Ubicacion(
                float(lats[abajo] + t * (lats[arriba] - lats[abajo])),
                float(lons[abajo] + t * (lons[arriba] - lons[abajo])),
                Precision.INTERPOLADA,
            )
    vecino = abajo if arriba >= len(numeros) else arriba if abajo < 0 else None
    if vecino is not None and abs(int(numeros[vecino]) - numero) <= SALTO_MAXIMO // 4:
        return Ubicacion(float(lats[vecino]), float(lons[vecino]), Precision.INTERPOLADA)
    return None
