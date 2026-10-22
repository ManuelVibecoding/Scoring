"""Resumen de una zona dibujada: promedios ponderados por población de sus hexágonos."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from score.domain.puntaje import LETRAS, Dimension, fortalezas_y_debilidades, letra


@dataclass(frozen=True)
class ResumenZona:
    hexagonos: int
    personas: float
    hogares: float
    viviendas: float
    puntaje: float | None
    letra: str | None
    rango_puntaje: tuple[float, float] | None  # percentiles 10 y 90 (por población)
    distribucion_letras: dict[str, float]  # fracción de la población en cada letra
    dimensiones: dict[str, float | None]
    fortalezas: list[str]
    debilidades: list[str]
    comunas: dict[str, float]  # fracción de la población por comuna


def _promedio(valores: pd.Series, pesos: pd.Series) -> float | None:
    validos = valores.notna()
    if not validos.any():
        return None
    w = pesos[validos]
    if w.sum() == 0:
        return round(float(valores[validos].mean()), 1)
    return round(float(np.average(valores[validos], weights=w)), 1)


def _cuantil(valores: pd.Series, pesos: pd.Series, q: float) -> float:
    orden = valores.sort_values()
    acumulado = pesos[orden.index].cumsum()
    return float(orden[acumulado >= q * acumulado.iloc[-1]].iloc[0])


def resumir_zona(
    hexagonos: pd.DataFrame,
    modelo: tuple[Dimension, ...],
    referencia: dict[str, float],
) -> ResumenZona:
    """`hexagonos` trae puntaje, letra, dimensiones, personas y comuna de cada hexágono."""
    if len(hexagonos) == 0:
        return ResumenZona(0, 0, 0, 0, None, None, None, {}, {}, [], [], {})
    pesos = hexagonos["personas"].fillna(0).astype(float)
    if pesos.sum() == 0:
        pesos = pd.Series(1.0, index=hexagonos.index)
    total = float(pesos.sum())
    dimensiones = {d.id: _promedio(hexagonos[d.id], pesos) for d in modelo}
    puntaje = _promedio(hexagonos["puntaje"], pesos)
    fuertes, debiles = fortalezas_y_debilidades(pd.Series(dimensiones), modelo, referencia)
    por_letra = pesos.groupby(hexagonos["letra"]).sum() / total
    por_comuna = pesos.groupby(hexagonos["comuna"]).sum() / total
    return ResumenZona(
        hexagonos=len(hexagonos),
        personas=float(hexagonos["personas"].fillna(0).sum()),
        hogares=float(hexagonos["hogares"].fillna(0).sum()),
        viviendas=float(hexagonos["viviendas"].fillna(0).sum()),
        puntaje=puntaje,
        letra=letra(puntaje) if puntaje is not None else None,
        rango_puntaje=(
            round(_cuantil(hexagonos["puntaje"], pesos, 0.1), 1),
            round(_cuantil(hexagonos["puntaje"], pesos, 0.9), 1),
        ),
        distribucion_letras={nota: round(float(por_letra.get(nota, 0.0)), 3) for _, nota in LETRAS},
        dimensiones=dimensiones,
        fortalezas=fuertes,
        debilidades=debiles,
        comunas={
            str(c): round(float(v), 3) for c, v in por_comuna.sort_values(ascending=False).items()
        },
    )
