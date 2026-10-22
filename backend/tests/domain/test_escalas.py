import numpy as np
import pandas as pd
import pytest

from score.domain.escalas import (
    PorCantidad,
    PorDistanciaMinima,
    PorMinutos,
    PorPercentil,
    percentil_ponderado,
)

SIN_PESOS = pd.Series([1.0] * 6)


def test_por_minutos_lineal_entre_ideal_y_limite() -> None:
    minutos = pd.Series([0, 5, 15, 25, 40, np.nan])
    assert list(PorMinutos(5, 25)(minutos, SIN_PESOS)) == [100, 100, 50, 0, 0, 0]


def test_por_distancia_minima_castiga_lo_cercano() -> None:
    metros = pd.Series([10, 50, 225, 400, 2000, np.nan])
    assert list(PorDistanciaMinima(50, 400)(metros, SIN_PESOS)) == [0, 0, 50, 100, 100, 100]


def test_por_cantidad_satura() -> None:
    assert list(PorCantidad(20)(pd.Series([0, 10, 20, 35]), SIN_PESOS)) == [0, 50, 100, 100]


def test_percentil_ponderado_por_poblacion() -> None:
    # Una comuna chica muy buena y una grande mala: la grande pesa más.
    valores = pd.Series([1.0, 9.0])
    pesos = pd.Series([900.0, 100.0])
    assert list(percentil_ponderado(valores, pesos)) == pytest.approx([45.0, 95.0])


def test_percentil_invertido_y_vacios() -> None:
    valores = pd.Series([10.0, 20.0, np.nan])
    resultado = PorPercentil(mayor_es_mejor=False)(valores, pd.Series([1.0, 1.0, 1.0]))
    assert resultado.iloc[0] > resultado.iloc[1]
    assert np.isnan(resultado.iloc[2])


def test_percentil_de_un_valor_nuevo() -> None:
    from score.domain.escalas import percentil_de_valor

    valores = pd.Series([10.0, 20.0, 30.0, 40.0])
    pesos = pd.Series([1.0, 1.0, 1.0, 1.0])
    assert percentil_de_valor(25.0, valores, pesos) == 50.0
    assert percentil_de_valor(5.0, valores, pesos) == 0.0
    assert percentil_de_valor(20.0, valores, pesos) == 37.5


def test_empates_quedan_en_el_centro_de_su_tramo() -> None:
    valores = pd.Series([5.0, 5.0, 5.0, 5.0])
    assert list(percentil_ponderado(valores, pd.Series([1.0] * 4))) == [50.0] * 4
