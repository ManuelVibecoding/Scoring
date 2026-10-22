"""Puertos: lo que los casos de uso necesitan del mundo exterior, sin decir cómo se obtiene."""

from datetime import datetime
from typing import Any, Protocol

import pandas as pd

from score.domain.avisos import Aviso, TipoPropiedad


class RepositorioPuntajes(Protocol):
    def hexagono_mas_cercano(self, lat: float, lon: float) -> tuple[pd.Series, float] | None:
        """Fila del hexágono que contiene (o está más cerca de) el punto y la distancia en m."""
        ...

    def comuna(self, cut: int) -> pd.Series | None: ...

    def medianas(self) -> dict[str, float]:
        """Mediana de cada dimensión en la RM (ponderada por población)."""
        ...

    def capa(self) -> pd.DataFrame:
        """Puntaje y dimensiones de todos los hexágonos, para pintar el mapa."""
        ...

    def contorno_comunas(self) -> dict[str, Any]:
        """GeoJSON simplificado de los límites comunales."""
        ...


class CacheAvisos(Protocol):
    def consultado_en(self, comuna: str, tipo: TipoPropiedad) -> datetime | None: ...

    def guardar(
        self, comuna: str, tipo: TipoPropiedad, avisos: list[Aviso], momento: datetime
    ) -> None: ...

    def en_rectangulo(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float
    ) -> list[Aviso]: ...


class Geocodificador(Protocol):
    def buscar(self, texto: str) -> list[dict[str, Any]]: ...

    def direccion(self, lat: float, lon: float) -> str | None: ...
