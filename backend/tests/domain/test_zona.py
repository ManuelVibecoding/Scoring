import pandas as pd
import pytest

from score.domain.escalas import PorCantidad
from score.domain.puntaje import Dimension, Indicador, Nivel
from score.domain.zona import resumir_zona

MODELO = (
    Dimension(
        "transporte", "Transporte", 50, Nivel.PUNTO, (Indicador("x", 1, PorCantidad(1), ""),)
    ),
    Dimension("verde", "Áreas verdes", 50, Nivel.PUNTO, (Indicador("y", 1, PorCantidad(1), ""),)),
)


def test_promedios_ponderados_por_poblacion() -> None:
    hexagonos = pd.DataFrame(
        {
            "puntaje": [90.0, 50.0],
            "letra": ["A", "C"],
            "transporte": [90.0, 30.0],
            "verde": [80.0, 70.0],
            "personas": [300.0, 100.0],
            "hogares": [100.0, 40.0],
            "viviendas": [110.0, 45.0],
            "comuna": ["ÑUÑOA", "MACUL"],
        }
    )
    z = resumir_zona(hexagonos, MODELO, {"transporte": 50.0, "verde": 60.0})
    assert z.puntaje == pytest.approx(80.0)  # (90·300 + 50·100) / 400
    assert z.letra == "A"
    assert z.dimensiones == {"transporte": 75.0, "verde": 77.5}
    assert z.distribucion_letras["A"] == 0.75
    assert z.comunas == {"ÑUÑOA": 0.75, "MACUL": 0.25}
    assert z.personas == 400
    assert z.fortalezas == ["Transporte", "Áreas verdes"]


def test_zona_vacia() -> None:
    columnas = [
        "puntaje",
        "letra",
        "transporte",
        "verde",
        "personas",
        "hogares",
        "viviendas",
        "comuna",
    ]
    z = resumir_zona(pd.DataFrame(columns=columnas), MODELO, {})
    assert z.hexagonos == 0
    assert z.puntaje is None
