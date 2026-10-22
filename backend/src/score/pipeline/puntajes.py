"""Aplica el modelo de puntaje a cada hexágono habitado de la RM.

Une las cercanías por hexágono con los indicadores de su comuna, puntúa con el modelo
del dominio y agrega el percentil del lugar dentro de su comuna y de la RM.
"""

from pathlib import Path

import pandas as pd

from score.domain.escalas import percentil_ponderado
from score.domain.modelo import MODELO, VERSION
from score.domain.puntaje import percentil_en_grupo, puntuar

COLUMNAS_COMUNALES = [
    "comuna",
    "tasa_delitos_violentos_100k",
    "tasa_robo_vivienda_100k",
    "tasa_homicidios_100k_3a",
    "tasa_delitos_armas_100k",
    "poblacion",
    "hogares",
    "pct_pobreza_ingresos",
    "pct_pobreza_multidimensional",
    "icvu_nivel",
    "icvu_nivel_orden",
]


def preparar(hexagonos: pd.DataFrame, comunas: pd.DataFrame) -> pd.DataFrame:
    """Tabla de entrada del modelo: un hexágono por fila con sus datos y los de su comuna."""
    c = comunas[COLUMNAS_COMUNALES].copy()
    robos = c["tasa_robo_vivienda_100k"] * c["poblacion"] / 100_000
    c["robo_vivienda_por_1000_hogares"] = robos / c["hogares"] * 1000
    return hexagonos.join(c.drop(columns=["poblacion", "hogares"]), on="cut")


def calcular(hexagonos: pd.DataFrame, comunas: pd.DataFrame) -> pd.DataFrame:
    datos = preparar(hexagonos, comunas)
    puntajes = puntuar(datos, MODELO)
    pesos = datos["personas"].fillna(0)
    puntajes["percentil_rm"] = percentil_ponderado(puntajes["puntaje"], pesos).round(0)
    puntajes["percentil_comuna"] = percentil_en_grupo(puntajes["puntaje"], datos["cut"], pesos)
    puntajes["version_modelo"] = VERSION
    return datos.join(puntajes)


def construir_puntajes(procesados: Path) -> Path:
    hexagonos = pd.read_parquet(procesados / "hexagonos.parquet").set_index("h3")
    comunas = pd.read_parquet(procesados / "comunas.parquet")
    resultado = calcular(hexagonos, comunas)
    destino = procesados / "puntajes.parquet"
    resultado.reset_index().to_parquet(destino)
    return destino
