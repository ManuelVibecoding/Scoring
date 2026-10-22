"""Caso de uso: todo lo que la app muestra al tocar un punto del mapa."""

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

from score.domain.modelo import MODELO
from score.domain.puntaje import fortalezas_y_debilidades
from score.domain.veredicto import redactar
from score.services.puertos import RepositorioPuntajes

# Lo que se muestra en "Cercanías", en este orden: (id, etiqueta, modo).
CERCANIAS: tuple[tuple[str, str, str], ...] = (
    ("metro", "Metro", "pie"),
    ("paradero", "Paradero", "pie"),
    ("supermercado", "Supermercado", "pie"),
    ("farmacia", "Farmacia", "pie"),
    ("colegio", "Colegio", "pie"),
    ("jardin", "Jardín infantil", "pie"),
    ("cesfam", "CESFAM", "pie"),
    ("plaza", "Plaza", "pie"),
    ("parque", "Parque", "pie"),
    ("banco", "Banco", "pie"),
    ("mall", "Mall", "pie"),
    ("urgencia", "Urgencia", "auto"),
    ("bomberos", "Bomberos", "auto"),
    ("policia", "Policía", "auto"),
    ("acceso_autopista", "Autopista", "auto"),
    ("centro_empleo", "Centro de empleo", "auto"),
)

DATOS_COMUNALES: tuple[tuple[str, str, str], ...] = (
    ("poblacion", "Población", "personas"),
    ("escolaridad_promedio", "Escolaridad promedio", "años"),
    ("pct_pobreza_ingresos", "Pobreza por ingresos", "%"),
    ("pct_pobreza_multidimensional", "Pobreza multidimensional", "%"),
    ("tasa_homicidios_100k_3a", "Homicidios", "por 100 mil"),
    ("tasa_dmcs_100k", "Delitos de mayor connotación", "por 100 mil"),
    ("pct_hogares_arrendatarios", "Hogares que arriendan", "%"),
    ("icvu_nivel", "Calidad de vida urbana (ICVU)", "nivel"),
)


def _unidad(columna: str) -> str:
    if columna.startswith("min_"):
        return "min"
    if columna.startswith("m_"):
        return "m"
    if columna.startswith(("pct_",)):
        return "%"
    if columna.startswith("tasa_"):
        return "por 100 mil"
    if "por_1000" in columna:
        return "por 1.000 hogares"
    if columna.startswith("escolaridad"):
        return "años"
    return ""


def _valor(fila: pd.Series, columna: str) -> Any:
    valor = fila.get(columna)
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return None
    if hasattr(valor, "item"):
        return valor.item()
    return valor


@dataclass(frozen=True)
class IndicadorPunto:
    descripcion: str
    valor: float | None
    unidad: str


@dataclass(frozen=True)
class DimensionPunto:
    id: str
    nombre: str
    peso: float
    nivel: str
    puntaje: float | None
    indicadores: list[IndicadorPunto]


@dataclass(frozen=True)
class Cercania:
    id: str
    etiqueta: str
    modo: str
    minutos: float | None
    lugar: str | None


@dataclass(frozen=True)
class DatoComunal:
    etiqueta: str
    valor: Any
    unidad: str


@dataclass(frozen=True)
class FichaPunto:
    h3: str
    lat: float
    lon: float
    distancia_al_hexagono_m: float
    cut: int
    comuna: str
    puntaje: float | None
    letra: str | None
    percentil_rm: float | None
    percentil_comuna: float | None
    veredicto: str
    fortalezas: list[str]
    debilidades: list[str]
    dimensiones: list[DimensionPunto]
    cercanias: list[Cercania]
    barrio: dict[str, float | None]
    datos_comunales: list[DatoComunal]
    version_modelo: str


def consultar_punto(repo: RepositorioPuntajes, lat: float, lon: float) -> FichaPunto | None:
    encontrado = repo.hexagono_mas_cercano(lat, lon)
    if encontrado is None:
        return None
    fila, distancia = encontrado
    comuna = repo.comuna(int(fila["cut"]))
    fuertes, debiles = fortalezas_y_debilidades(fila, MODELO, repo.medianas())

    dimensiones = [
        DimensionPunto(
            id=d.id,
            nombre=d.nombre,
            peso=d.peso,
            nivel=str(d.nivel),
            puntaje=_valor(fila, d.id),
            indicadores=[
                IndicadorPunto(i.descripcion, _valor(fila, i.columna), _unidad(i.columna))
                for i in d.indicadores
            ],
        )
        for d in MODELO
    ]
    return FichaPunto(
        h3=str(fila.name),
        lat=float(fila["lat"]),
        lon=float(fila["lon"]),
        distancia_al_hexagono_m=round(distancia),
        cut=int(fila["cut"]),
        comuna=str(fila["comuna"]),
        puntaje=_valor(fila, "puntaje"),
        letra=_valor(fila, "letra"),
        percentil_rm=_valor(fila, "percentil_rm"),
        percentil_comuna=_valor(fila, "percentil_comuna"),
        veredicto=redactar(_valor(fila, "letra"), fuertes, debiles),
        fortalezas=fuertes,
        debilidades=debiles,
        dimensiones=dimensiones,
        cercanias=[
            Cercania(id_, etiqueta, modo, _valor(fila, f"min_{id_}"), _valor(fila, f"cerca_{id_}"))
            for id_, etiqueta, modo in CERCANIAS
        ],
        barrio={
            c: _valor(fila, c)
            for c in (
                "recorridos_400m",
                "buses_hora_max_400m",
                "n800_colegio",
                "n800_supermercado",
                "n800_comercio_barrio",
                "personas",
            )
        },
        datos_comunales=[
            DatoComunal(etiqueta, _valor(comuna, col) if comuna is not None else None, unidad)
            for col, etiqueta, unidad in DATOS_COMUNALES
        ],
        version_modelo=str(fila.get("version_modelo", "")),
    )
