"""Puertos: lo que los casos de uso necesitan del mundo exterior, sin decir cómo se obtiene."""

from datetime import datetime
from typing import Any, Protocol

import pandas as pd
from shapely.geometry.base import BaseGeometry

from score.domain.avisos import Aviso, TipoPropiedad


class RepositorioPuntajes(Protocol):
    def hexagono_mas_cercano(self, lat: float, lon: float) -> tuple[pd.Series, float] | None:
        """Fila del hexágono que contiene (o está más cerca de) el punto y la distancia en m."""
        ...

    def comuna(self, cut: int) -> pd.Series | None: ...

    def medianas(self) -> dict[str, float]:
        """Mediana de cada dimensión en la RM (ponderada por población)."""
        ...

    def puntuar_en_contexto(self, fila: pd.Series) -> pd.Series:
        """Dimensiones, puntaje, letra y percentiles de un lugar nuevo frente a la RM."""
        ...

    def capa(self) -> pd.DataFrame:
        """Puntaje y dimensiones de todos los hexágonos, para pintar el mapa."""
        ...

    def tabla(self) -> pd.DataFrame:
        """Todos los hexágonos con sus indicadores y puntajes."""
        ...

    def hexagonos_en(self, zona: BaseGeometry) -> pd.DataFrame:
        """Hexágonos cuyo centro cae dentro de la zona."""
        ...

    def lugares(self, categorias: list[str]) -> pd.DataFrame:
        """Puntos de interés de esas categorías (categoria, nombre, lat, lon)."""
        ...

    def contar_lugares_en(self, zona: BaseGeometry) -> dict[str, int]:
        """Cantidad de puntos de interés por categoría dentro de la zona."""
        ...

    def contorno_comunas(self) -> dict[str, Any]:
        """GeoJSON simplificado de los límites comunales."""
        ...


class MotorDeCercanias(Protocol):
    def evaluar(self, lat: Any, lon: Any) -> pd.DataFrame:
        """Minutos, lugar más cercano y conteos en uno o varios puntos exactos."""
        ...

    def isocrona(self, lat: float, lon: float, bandas: tuple[int, ...]) -> dict[str, Any]:
        """Áreas alcanzables a pie (GeoJSON)."""
        ...


class CacheAvisos(Protocol):
    def consultado_en(self, fuente: str, comuna: str, tipo: TipoPropiedad) -> datetime | None: ...

    def guardar(
        self,
        fuente: str,
        comuna: str,
        tipo: TipoPropiedad,
        avisos: list[Aviso],
        momento: datetime,
    ) -> None: ...

    def todos(self) -> pd.DataFrame:
        """Avisos ubicados con confianza (para dibujarlos en el mapa)."""
        ...

    def en_rectangulo(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float
    ) -> list[Aviso]: ...


class Geocodificador(Protocol):
    def buscar(self, texto: str) -> list[dict[str, Any]]: ...

    def direccion(self, lat: float, lon: float) -> str | None: ...
