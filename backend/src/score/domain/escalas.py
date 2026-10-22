"""Escalas que convierten un indicador crudo en un puntaje de 0 a 100.

Todas devuelven 100 para lo mejor y 0 para lo peor. Un valor faltante que significa
"no hay dato" queda vacío (NaN) y la dimensión lo ignora; uno que significa "no se llega"
(por ejemplo, el Metro a más de 120 minutos) debe convertirse en 0 antes.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

Escala = Callable[[pd.Series, pd.Series], pd.Series]
"""Recibe la columna del indicador y el peso de cada fila (población) y devuelve 0–100."""


@dataclass(frozen=True)
class PorMinutos:
    """100 hasta `ideal` minutos, baja en línea recta y llega a 0 en `limite`.

    Sin valor significa que no se alcanza en el tiempo máximo calculado: vale 0.
    """

    ideal: float
    limite: float

    def __call__(self, valores: pd.Series, _pesos: pd.Series) -> pd.Series:
        tramo = (self.limite - valores) / (self.limite - self.ideal)
        return (tramo.clip(0, 1) * 100).fillna(0.0)


@dataclass(frozen=True)
class PorDistanciaMinima:
    """Para lo que molesta estando cerca: 0 a `molesto` metros o menos, 100 desde `tranquilo`."""

    molesto: float
    tranquilo: float

    def __call__(self, valores: pd.Series, _pesos: pd.Series) -> pd.Series:
        tramo = (valores - self.molesto) / (self.tranquilo - self.molesto)
        return (tramo.clip(0, 1) * 100).fillna(100.0)


@dataclass(frozen=True)
class PorCantidad:
    """Más es mejor hasta `saturacion`; desde ahí vale 100."""

    saturacion: float

    def __call__(self, valores: pd.Series, _pesos: pd.Series) -> pd.Series:
        return ((valores / self.saturacion).clip(0, 1) * 100).fillna(0.0)


@dataclass(frozen=True)
class PorPercentil:
    """Posición relativa en la RM, ponderada por población.

    Un 70 significa que el 70% de los habitantes de la RM vive en un lugar peor en este
    indicador. Los vacíos siguen vacíos (sin dato).
    """

    mayor_es_mejor: bool = True

    def __call__(self, valores: pd.Series, pesos: pd.Series) -> pd.Series:
        return percentil_ponderado(valores, pesos, self.mayor_es_mejor)


def percentil_de_valor(valor: float, valores: pd.Series, pesos: pd.Series) -> float:
    """Percentil (0–100) de un valor nuevo frente a una población ya existente."""
    validos = valores.notna()
    v, w = valores[validos], pesos[validos].clip(lower=0).astype(float)
    total = float(w.sum())
    if total == 0 or np.isnan(valor):
        return float("nan")
    debajo = float(w[v < valor].sum()) + float(w[v == valor].sum()) / 2
    return debajo / total * 100


def percentil_ponderado(
    valores: pd.Series, pesos: pd.Series, mayor_es_mejor: bool = True
) -> pd.Series:
    """Percentil (0–100) de cada valor, contando cuánta población queda por debajo.

    Los empates reciben el punto medio de su grupo, para que una comuna entera (mismo
    valor en todos sus hexágonos) quede en el centro de su tramo de población.
    """
    validos = valores.notna()
    v = valores[validos] if mayor_es_mejor else -valores[validos]
    w = pesos[validos].clip(lower=0).astype(float)
    if w.sum() == 0:
        w = pd.Series(1.0, index=w.index)
    tabla = pd.DataFrame({"v": v, "w": w}).groupby("v")["w"].sum().sort_index()
    acumulado = tabla.cumsum() - tabla / 2
    resultado = pd.Series(np.nan, index=valores.index)
    resultado[validos] = v.map(acumulado / tabla.sum() * 100).to_numpy()
    return resultado
