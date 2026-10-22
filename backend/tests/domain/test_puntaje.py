import numpy as np
import pandas as pd
import pytest

from score.domain.escalas import PorCantidad, PorMinutos, PorPercentil
from score.domain.modelo import MODELO
from score.domain.puntaje import (
    Dimension,
    Indicador,
    Nivel,
    fortalezas_y_debilidades,
    letra,
    percentil_en_grupo,
    puntuar,
)

TRANSPORTE = Dimension(
    "transporte",
    "Transporte",
    60,
    Nivel.PUNTO,
    (
        Indicador("min_metro", 0.5, PorMinutos(5, 25), ""),
        Indicador("recorridos", 0.5, PorCantidad(10), ""),
    ),
)
VERDE = Dimension(
    "verde", "Áreas verdes", 40, Nivel.PUNTO, (Indicador("ndvi", 1, PorCantidad(1), ""),)
)


def _datos(**columnas: list[float]) -> pd.DataFrame:
    n = len(next(iter(columnas.values())))
    return pd.DataFrame({"personas": [1.0] * n, **columnas})


@pytest.mark.parametrize(
    ("puntaje", "esperada"), [(95, "A"), (80, "A"), (79.9, "B"), (50, "C"), (40, "D"), (5, "E")]
)
def test_letra(puntaje: float, esperada: str) -> None:
    assert letra(puntaje) == esperada


def test_letra_sin_puntaje() -> None:
    assert letra(np.nan) is None


def test_puntaje_total_pondera_dimensiones() -> None:
    datos = _datos(min_metro=[5.0], recorridos=[5.0], ndvi=[1.0])
    r = puntuar(datos, (TRANSPORTE, VERDE)).iloc[0]
    assert r["transporte"] == 75  # (100 + 50) / 2
    assert r["verde"] == 100
    assert r["puntaje"] == pytest.approx(0.6 * 75 + 0.4 * 100)
    assert r["cobertura"] == 1.0
    assert r["letra"] == "A"


def test_indicador_sin_dato_reparte_su_peso_dentro_de_la_dimension() -> None:
    # Sin dato de recorridos (vacío en una escala de percentil) el metro decide solo.
    dim = Dimension(
        "d",
        "D",
        1,
        Nivel.PUNTO,
        (
            Indicador("min_metro", 0.5, PorMinutos(5, 25), ""),
            Indicador("icvu", 0.5, PorPercentil(), ""),
        ),
    )
    datos = _datos(min_metro=[5.0], icvu=[np.nan])
    assert puntuar(datos, (dim,)).iloc[0]["d"] == 100


def test_dimension_sin_datos_baja_la_cobertura_y_no_el_puntaje() -> None:
    verde_sin_dato = Dimension(
        "verde", "Verde", 40, Nivel.PUNTO, (Indicador("ndvi", 1, PorPercentil(), ""),)
    )
    datos = _datos(min_metro=[5.0], recorridos=[10.0], ndvi=[np.nan])
    r = puntuar(datos, (TRANSPORTE, verde_sin_dato)).iloc[0]
    assert r["puntaje"] == 100
    assert r["cobertura"] == 0.6


def test_fortalezas_y_debilidades() -> None:
    fila = pd.Series({"transporte": 90.0, "verde": 30.0})
    fuertes, debiles = fortalezas_y_debilidades(fila, (TRANSPORTE, VERDE))
    assert fuertes == ["Transporte"]
    assert debiles == ["Áreas verdes"]


def test_percentil_en_grupo() -> None:
    puntajes = pd.Series([10.0, 20.0, 90.0, 95.0])
    grupos = pd.Series(["a", "a", "b", "b"])
    r = percentil_en_grupo(puntajes, grupos, pd.Series([1.0] * 4))
    assert list(r) == [25, 75, 25, 75]


def test_modelo_v1_pesos_suman_100_e_indicadores_suman_1() -> None:
    assert sum(d.peso for d in MODELO) == 100
    for d in MODELO:
        assert sum(i.peso for i in d.indicadores) == pytest.approx(1.0), d.id
