"""Cercanías por hexágono: minutos al punto de interés más cercano y conteos alrededor.

Para cada hexágono habitado de la RM se calcula, por categoría:
- min_<id>:    minutos a pie (o en auto) al más cercano, medidos sobre la red de calles
- cerca_<id>:  nombre de ese lugar
- n800_<id>:   cuántos hay a menos de 800 m en línea recta (oferta del barrio)
y además la oferta de buses en los paraderos a menos de 400 m.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from score.pipeline.red import VELOCIDAD_PEATON_M_MIN, Alcance, Modo, Red, proyectar


@dataclass(frozen=True)
class Medida:
    id: str
    categorias: tuple[str, ...]
    modo: Modo
    hacia_los_puntos: bool = True


# A pie: lo que se usa en la vida diaria. En auto: emergencias y conectividad vial.
MEDIDAS: tuple[Medida, ...] = (
    Medida("metro", ("metro",), Modo.PIE),
    Medida("tren", ("tren",), Modo.PIE),
    Medida("paradero", ("paradero",), Modo.PIE),
    Medida("supermercado", ("supermercado",), Modo.PIE),
    Medida("farmacia", ("farmacia",), Modo.PIE),
    Medida("banco", ("banco",), Modo.PIE),
    Medida("cajero", ("cajero", "banco"), Modo.PIE),
    Medida("colegio", ("colegio",), Modo.PIE),
    Medida("jardin", ("jardin",), Modo.PIE),
    Medida("cesfam", ("cesfam",), Modo.PIE),
    Medida("feria", ("feria",), Modo.PIE),
    Medida("mall", ("mall",), Modo.PIE),
    Medida("gimnasio", ("gimnasio",), Modo.PIE),
    Medida("plaza", ("plaza", "parque"), Modo.PIE),
    Medida("parque", ("parque",), Modo.PIE),
    Medida("urgencia", ("urgencia",), Modo.AUTO),
    Medida("hospital_clinica", ("hospital_clinica",), Modo.AUTO),
    Medida("bomberos", ("bomberos",), Modo.AUTO, hacia_los_puntos=False),
    Medida("policia", ("policia",), Modo.AUTO, hacia_los_puntos=False),
    Medida("acceso_autopista", ("acceso_autopista",), Modo.AUTO),
    Medida("centro_empleo", ("centro_empleo",), Modo.AUTO),
)

# Distancia en línea recta (m) a lo que molesta por estar cerca, no por tener que ir.
DESAMENIDADES: tuple[str, ...] = ("carcel", "vertedero", "planta_tratamiento")

CONTEOS_800M: dict[str, tuple[str, ...]] = {
    "colegio": ("colegio",),
    "jardin": ("jardin",),
    "supermercado": ("supermercado",),
    "farmacia": ("farmacia",),
    "paradero": ("paradero",),
    "comercio_barrio": ("restaurante", "cafe", "feria", "gimnasio"),
}
RADIO_CONTEO_M = 800.0
RADIO_BUSES_M = 400.0
# Más allá de esto el lugar se considera "no accesible" desde el hexágono.
MINUTOS_MAXIMOS = 120.0


def _puntos_de_parques(parques: pd.DataFrame, categorias: tuple[str, ...]) -> pd.DataFrame:
    """Un punto por nodo del borde: a un parque se entra por cualquier lado."""
    sel = parques[parques["categoria"].isin(categorias)]
    return pd.DataFrame(
        {
            "nombre": np.repeat(sel["nombre"].to_numpy(), sel["lats"].map(len)),
            "lat": np.concatenate(sel["lats"].to_numpy()) if len(sel) else [],
            "lon": np.concatenate(sel["lons"].to_numpy()) if len(sel) else [],
        }
    )


def _a_minutos(red: Red, costo: np.ndarray) -> np.ndarray:
    minutos = costo / VELOCIDAD_PEATON_M_MIN if red.modo is Modo.PIE else costo / 60.0
    return np.where(minutos <= MINUTOS_MAXIMOS, minutos, np.nan)


def _distancia_recta(hx: np.ndarray, hy: np.ndarray, puntos: pd.DataFrame) -> np.ndarray:
    """Metros en línea recta al punto más cercano (infinito si no hay puntos)."""
    if len(puntos) == 0:
        return np.full(len(hx), np.inf)
    arbol = cKDTree(np.column_stack(proyectar(puntos["lat"].to_numpy(), puntos["lon"].to_numpy())))
    distancia, _ = arbol.query(np.column_stack([hx, hy]))
    return np.asarray(distancia, dtype=float)


def calcular(
    hexagonos: pd.DataFrame,
    puntos: pd.DataFrame,
    parques: pd.DataFrame,
    vias_rapidas: pd.DataFrame,
    redes: dict[Modo, Red],
) -> pd.DataFrame:
    resultado = hexagonos.copy()
    hx, hy = proyectar(hexagonos["lat"].to_numpy(), hexagonos["lon"].to_numpy())
    ajustes = {modo: red.ajustar(hx, hy) for modo, red in redes.items()}

    resultado["m_via_rapida"] = _distancia_recta(hx, hy, vias_rapidas).round()
    resultado["m_desamenidad"] = _distancia_recta(
        hx, hy, puntos[puntos["categoria"].isin(DESAMENIDADES)]
    ).round()

    for medida in MEDIDAS:
        red = redes[medida.modo]
        if medida.id in ("plaza", "parque"):
            fuente = _puntos_de_parques(parques, medida.categorias)
        else:
            fuente = puntos[puntos["categoria"].isin(medida.categorias)].reset_index(drop=True)
        px, py = proyectar(fuente["lat"].to_numpy(), fuente["lon"].to_numpy())
        alcance: Alcance = red.costo_minimo(px, py, medida.hacia_los_puntos)

        nodo, separacion = ajustes[medida.modo]
        costo = alcance.costo[nodo] + red.costo_de_acceso(separacion)
        minutos = _a_minutos(red, costo)
        resultado[f"min_{medida.id}"] = minutos.round(1)
        indice = alcance.punto[nodo]
        nombres = fuente["nombre"].to_numpy(dtype=object)
        alcanzable = (indice >= 0) & np.isfinite(minutos)
        cercano = nombres[np.maximum(indice, 0)]
        cercano[~alcanzable] = None
        resultado[f"cerca_{medida.id}"] = cercano

    for id_conteo, categorias in CONTEOS_800M.items():
        sel = puntos[puntos["categoria"].isin(categorias)]
        arbol = cKDTree(np.column_stack(proyectar(sel["lat"].to_numpy(), sel["lon"].to_numpy())))
        resultado[f"n800_{id_conteo}"] = arbol.query_ball_point(
            np.column_stack([hx, hy]), RADIO_CONTEO_M, return_length=True
        )

    resultado = resultado.join(_oferta_buses(hexagonos, puntos))
    return resultado


def _oferta_buses(hexagonos: pd.DataFrame, puntos: pd.DataFrame) -> pd.DataFrame:
    """Recorridos distintos y frecuencia del paradero más servido a menos de 400 m."""
    paraderos = puntos[puntos["categoria"] == "paradero"].reset_index(drop=True)
    arbol = cKDTree(
        np.column_stack(proyectar(paraderos["lat"].to_numpy(), paraderos["lon"].to_numpy()))
    )
    hx, hy = proyectar(hexagonos["lat"].to_numpy(), hexagonos["lon"].to_numpy())
    # Con varios puntos de consulta, scipy devuelve una lista de índices por punto.
    cercanos = cast(
        list[list[int]], arbol.query_ball_point(np.column_stack([hx, hy]), RADIO_BUSES_M)
    )
    recorridos = paraderos["recorridos"].to_numpy()
    frecuencia = paraderos["salidas_hora"].fillna(0).to_numpy()
    return pd.DataFrame(
        {
            "recorridos_400m": [
                len({r for i in idx for r in (recorridos[i] if recorridos[i] is not None else [])})
                for idx in cercanos
            ],
            "buses_hora_max_400m": [
                float(frecuencia[idx].max()) if idx else 0.0 for idx in cercanos
            ],
        },
        index=hexagonos.index,
    ).round(1)


def construir_cercanias(raw: Path, interim: Path, procesados: Path) -> Path:
    """Trabajo completo: OSM → redes → puntos de interés → hexágonos → cercanías."""
    from score.pipeline import hexagonos as hx
    from score.pipeline import puntos as pt
    from score.pipeline.extraccion import asegurar_extraido
    from score.pipeline.osm import extraer_osm_rm
    from score.pipeline.red import construir_red

    osm_rm = extraer_osm_rm(raw / "osm_chile" / "chile-latest.osm.pbf", interim / "osm_rm")
    cartografia = asegurar_extraido(
        raw, interim, "censo2024_cartografia_rm", "cartografia_censo2024_R13.zip"
    )
    minsal = asegurar_extraido(
        raw, interim, "minsal_establecimientos", "ESTABLECIMIENTOS_12062026_DES.zip"
    )
    gtfs = asegurar_extraido(raw, interim, "dtpm_gtfs", "GTFS_20261003.zip")
    mineduc = asegurar_extraido(
        raw, interim, "mineduc_directorio", "Directorio-Oficial-EE-2025.rar"
    )

    puntos, parques = pt.construir_catalogo(
        gtfs, next(minsal.glob("*.shp")), next(mineduc.glob("*.csv")), osm_rm
    )
    grilla = hx.grilla(next(cartografia.glob("*_Manzanas.parquet")))
    redes = {modo: construir_red(osm_rm, modo) for modo in Modo}
    vias = pt.vias_rapidas(osm_rm)
    return guardar(calcular(grilla, puntos, parques, vias, redes), puntos, procesados)


def guardar(cercanias: pd.DataFrame, puntos: pd.DataFrame, procesados: Path) -> Path:
    procesados.mkdir(parents=True, exist_ok=True)
    destino = procesados / "hexagonos.parquet"
    cercanias.reset_index().to_parquet(destino)
    puntos.drop(columns=["recorridos"]).to_parquet(procesados / "puntos_interes.parquet")
    return destino
