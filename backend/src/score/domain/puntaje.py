"""Modelo de puntaje: dimensiones, indicadores, pesos y veredicto.

Reglas puras: reciben una tabla con los indicadores de cada lugar y devuelven puntajes.
No leen archivos ni conocen de dónde vienen los datos.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
import pandas as pd

from score.domain.escalas import Escala, percentil_ponderado


class Nivel(StrEnum):
    """Qué tan fino es el dato de una dimensión."""

    PUNTO = "punto"
    COMUNA = "comuna"
    MIXTO = "mixto"


@dataclass(frozen=True)
class Indicador:
    columna: str
    peso: float
    escala: Escala
    descripcion: str


@dataclass(frozen=True)
class Dimension:
    id: str
    nombre: str
    peso: float
    nivel: Nivel
    indicadores: tuple[Indicador, ...]


LETRAS: tuple[tuple[float, str], ...] = ((80, "A"), (65, "B"), (50, "C"), (35, "D"), (0, "E"))


def letra(puntaje: float) -> str | None:
    if pd.isna(puntaje):
        return None
    return next(nota for corte, nota in LETRAS if puntaje >= corte)


def puntaje_dimension(datos: pd.DataFrame, dimension: Dimension, pesos: pd.Series) -> pd.Series:
    """Promedio ponderado de los indicadores con dato; vacío si ninguno tiene dato."""
    suma = pd.Series(0.0, index=datos.index)
    peso_disponible = pd.Series(0.0, index=datos.index)
    for indicador in dimension.indicadores:
        valor = indicador.escala(datos[indicador.columna], pesos)
        hay = valor.notna()
        suma += valor.fillna(0.0) * indicador.peso
        peso_disponible += hay * indicador.peso
    return (suma / peso_disponible.where(peso_disponible > 0)).round(1)


def puntuar(
    datos: pd.DataFrame, modelo: tuple[Dimension, ...], columna_pesos: str = "personas"
) -> pd.DataFrame:
    """Puntaje por dimensión, total (0–100) y letra.

    Si una dimensión no tiene datos en un lugar, su peso se reparte entre las demás y la
    cobertura (`cobertura`, 0–1) registra qué fracción del modelo se pudo evaluar.
    """
    pesos = datos[columna_pesos].fillna(0)
    resultado = pd.DataFrame(index=datos.index)
    for dimension in modelo:
        resultado[dimension.id] = puntaje_dimension(datos, dimension, pesos)

    peso_total = sum(d.peso for d in modelo)
    suma = pd.Series(0.0, index=datos.index)
    disponible = pd.Series(0.0, index=datos.index)
    for d in modelo:
        suma += resultado[d.id].fillna(0) * d.peso
        disponible += resultado[d.id].notna() * d.peso
    resultado["puntaje"] = (suma / disponible.where(disponible > 0)).round(1)
    resultado["cobertura"] = (disponible / peso_total).round(2)
    resultado["letra"] = resultado["puntaje"].map(letra)
    return resultado


UMBRAL_FORTALEZA = 65.0
UMBRAL_DEBILIDAD = 50.0


def fortalezas_y_debilidades(
    fila: pd.Series,
    modelo: tuple[Dimension, ...],
    referencia: Mapping[str, float] | None = None,
    cantidad: int = 3,
) -> tuple[list[str], list[str]]:
    """Fortalezas (≥ 65 y sobre lo habitual) y debilidades (< 50) de un lugar, por nombre.

    Con `referencia` (la mediana de cada dimensión en la RM) se ordena por cuánto se
    distingue el lugar, no por el valor absoluto: un 100 en una dimensión donde casi todos
    tienen 100 no es una fortaleza que valga la pena contar.
    """
    nombres = {d.id: d.nombre for d in modelo}
    base = referencia or {}
    valores = {d.id: float(fila[d.id]) for d in modelo if pd.notna(fila[d.id])}
    diferencia = {i: v - base.get(i, 50.0) for i, v in valores.items()}
    fuertes = sorted(
        (i for i, v in valores.items() if v >= UMBRAL_FORTALEZA and diferencia[i] > 0),
        key=lambda i: -diferencia[i],
    )
    debiles = sorted(
        (i for i, v in valores.items() if v < UMBRAL_DEBILIDAD), key=lambda i: diferencia[i]
    )
    return [nombres[i] for i in fuertes[:cantidad]], [nombres[i] for i in debiles[:cantidad]]


def percentil_en_grupo(puntajes: pd.Series, grupos: pd.Series, pesos: pd.Series) -> pd.Series:
    """Percentil de cada puntaje dentro de su grupo (por ejemplo, su comuna), por población."""
    resultado = pd.Series(np.nan, index=puntajes.index)
    for _, indices in puntajes.groupby(grupos).groups.items():
        resultado[indices] = percentil_ponderado(puntajes[indices], pesos[indices])
    return resultado.round(0)
