"""Validación del modelo de puntaje contra el mercado y contra el ICVU.

Idea: si el puntaje mide bien la calidad de una ubicación, los lugares con mejor puntaje
deberían arrendarse más caro por m², una vez descontado lo que se debe a la propiedad
misma (tipo, tamaño, dormitorios). Ese "premio de ubicación" se compara con el puntaje.

El precio no es la verdad absoluta (también refleja moda, oferta y prestigio), así que
la validación busca coherencia, no maximizar la correlación.
"""

from dataclasses import dataclass, replace

import h3
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from score.domain.modelo import MODELO
from score.domain.puntaje import Dimension, puntuar
from score.pipeline.hexagonos import RESOLUCION_H3

# Filtros de avisos plausibles (arriendo mensual en pesos).
CLP_M2_MIN, CLP_M2_MAX = 2_000, 40_000
SUPERFICIE_MIN, SUPERFICIE_MAX = 20, 1_000
AVISOS_MINIMOS_POR_HEXAGONO = 3


def limpiar_avisos(avisos: pd.DataFrame) -> pd.DataFrame:
    a = avisos.dropna(subset=["precio_clp", "superficie_m2", "lat", "lon"]).copy()
    a = a[a["superficie_m2"].between(SUPERFICIE_MIN, SUPERFICIE_MAX)]
    a["clp_m2"] = a["precio_clp"] / a["superficie_m2"]
    a = a[a["clp_m2"].between(CLP_M2_MIN, CLP_M2_MAX)]
    a["h3"] = [
        h3.latlng_to_cell(lat, lon, RESOLUCION_H3)
        for lat, lon in zip(a["lat"], a["lon"], strict=True)
    ]
    return a


def premio_de_ubicacion(avisos: pd.DataFrame) -> pd.Series:
    """Residuo de log(precio/m²) tras descontar tipo, tamaño y dormitorios (MCO)."""
    x = pd.DataFrame(
        {
            "constante": 1.0,
            "es_casa": (avisos["tipo"] == "casa").astype(float),
            "log_superficie": np.log(avisos["superficie_m2"]),
            "dormitorios": avisos["dormitorios"].fillna(avisos["dormitorios"].median()),
        }
    )
    y = np.log(avisos["clp_m2"])
    coeficientes, *_ = np.linalg.lstsq(x.to_numpy(), y.to_numpy(), rcond=None)
    return pd.Series(y.to_numpy() - x.to_numpy() @ coeficientes, index=avisos.index)


def _spearman(a: pd.Series, b: pd.Series) -> float:
    validos = a.notna() & b.notna()
    rho, _ = spearmanr(a[validos], b[validos])
    return float(rho)


@dataclass(frozen=True)
class Resultado:
    avisos: int
    hexagonos_con_precio: int
    rho_hexagonos: float
    rho_comunas: float
    rho_icvu: float
    rho_por_dimension: dict[str, float]
    rho_por_ponderacion: dict[str, float]


def _comunal(puntajes: pd.DataFrame, columna: str) -> pd.Series:
    """Promedio por comuna ponderado por población."""
    pesos = puntajes["personas"].fillna(0) + 1e-6
    ponderado = (puntajes[columna] * pesos).groupby(puntajes["cut"]).sum()
    return ponderado / pesos.groupby(puntajes["cut"]).sum()


def ponderaciones_alternativas() -> dict[str, tuple[Dimension, ...]]:
    """El modelo v1 y variantes para medir qué tan sensible es a los pesos."""
    iguales = tuple(replace(d, peso=100 / len(MODELO)) for d in MODELO)
    solo_punto = tuple(
        replace(d, peso=d.peso if d.id not in ("seguridad", "socioeconomico") else 0.0001)
        for d in MODELO
    )
    sin_seguridad = tuple(
        replace(d, peso=d.peso if d.id != "seguridad" else 0.0001) for d in MODELO
    )
    return {
        "v1 (plan)": MODELO,
        "pesos iguales": iguales,
        "solo dimensiones por punto": solo_punto,
        "sin seguridad": sin_seguridad,
    }


LUGARES_DE_REFERENCIA: dict[str, tuple[float, float]] = {
    "Tobalaba (Providencia)": (-33.4180, -70.6013),
    "Plaza Ñuñoa": (-33.4560, -70.5975),
    "Plaza de Maipú": (-33.5100, -70.7570),
    "Plaza de Armas (Santiago)": (-33.4378, -70.6505),
    "Colón con Tomás Moro (Las Condes)": (-33.4155, -70.5590),
    "La Dehesa (Lo Barnechea)": (-33.3580, -70.5180),
    "Plaza de Puente Alto": (-33.6110, -70.5755),
    "Bajos de Mena (Puente Alto)": (-33.6170, -70.5960),
    "La Pintana centro": (-33.5830, -70.6330),
    "Melipilla centro": (-33.6870, -71.2150),
}


def lugares_de_referencia(datos: pd.DataFrame) -> pd.DataFrame:
    filas = {}
    for nombre, (lat, lon) in LUGARES_DE_REFERENCIA.items():
        celda = h3.latlng_to_cell(lat, lon, RESOLUCION_H3)
        if celda not in datos.index:
            distancia = (datos["lat"] - lat) ** 2 + (datos["lon"] - lon) ** 2
            celda = distancia.idxmin()
        filas[nombre] = datos.loc[celda, [d.id for d in MODELO] + ["puntaje", "letra"]]
    return pd.DataFrame(filas).T


def validar(datos: pd.DataFrame, avisos: pd.DataFrame) -> tuple[Resultado, pd.DataFrame]:
    """`datos` es la tabla de puntajes (entradas + resultados) indexada por h3."""
    a = limpiar_avisos(avisos)
    a["premio"] = premio_de_ubicacion(a)
    por_hex = a.groupby("h3").agg(premio=("premio", "median"), avisos=("premio", "size"))
    por_hex = por_hex[por_hex["avisos"] >= AVISOS_MINIMOS_POR_HEXAGONO]
    comparados = datos.join(por_hex, how="inner")

    por_comuna = (
        a.assign(cut=a["h3"].map(datos["cut"]))
        .dropna(subset=["cut"])
        .groupby("cut")["premio"]
        .median()
    )
    puntaje_comunal = _comunal(datos, "puntaje")
    icvu = datos.groupby("cut")["icvu_nivel_orden"].first()

    alternativas = {}
    for nombre, modelo in ponderaciones_alternativas().items():
        p = puntuar(datos, modelo)["puntaje"]
        alternativas[nombre] = _spearman(p.loc[comparados.index], comparados["premio"])

    resultado = Resultado(
        avisos=len(a),
        hexagonos_con_precio=len(comparados),
        rho_hexagonos=_spearman(comparados["puntaje"], comparados["premio"]),
        rho_comunas=_spearman(puntaje_comunal, por_comuna.reindex(puntaje_comunal.index)),
        rho_icvu=_spearman(puntaje_comunal, icvu.reindex(puntaje_comunal.index)),
        rho_por_dimension={d.id: _spearman(comparados[d.id], comparados["premio"]) for d in MODELO},
        rho_por_ponderacion=alternativas,
    )
    return resultado, comparados
