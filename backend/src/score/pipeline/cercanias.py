"""Cercanías: precálculo sobre toda la red de calles y valores por hexágono.

1. Por cada categoría (Metro, supermercado, urgencia…) se corre un Dijkstra multi-fuente
   sobre la red de calles y se guarda, para cada nodo, los minutos al lugar más cercano y
   cuál es (data/processed/motor/).
2. Con ese motor se evalúa cada hexágono habitado:
   - min_<id>:    minutos a pie (o en auto) al más cercano
   - cerca_<id>:  nombre de ese lugar
   - n800_<id>:   cuántos hay a menos de 800 m en línea recta
   - recorridos y buses a 400 m, distancia a vías rápidas y desamenidades.
La app usa el mismo motor para responder en el punto exacto que se toca.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import save_npz

from score.adapters.motor_cercanias import MotorCercanias
from score.domain.geo import proyectar
from score.pipeline.medidas import MEDIDAS, Medida
from score.pipeline.red import VELOCIDAD_PEATON_M_MIN, Alcance, Modo, Red


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


def fuente_de(medida: Medida, puntos: pd.DataFrame, parques: pd.DataFrame) -> pd.DataFrame:
    if medida.id in ("plaza", "parque"):
        return _puntos_de_parques(parques, medida.categorias)
    return puntos[puntos["categoria"].isin(medida.categorias)].reset_index(drop=True)


def _a_minutos(red: Red, costo: np.ndarray) -> np.ndarray:
    return costo / VELOCIDAD_PEATON_M_MIN if red.modo is Modo.PIE else costo / 60.0


def guardar_motor(
    redes: dict[Modo, Red],
    puntos: pd.DataFrame,
    parques: pd.DataFrame,
    vias_rapidas: pd.DataFrame,
    carpeta: Path,
) -> Path:
    """Corre un Dijkstra por medida y guarda el motor de cercanías en `carpeta`."""
    carpeta.mkdir(parents=True, exist_ok=True)
    for modo, red in redes.items():
        np.save(carpeta / f"nodos_{modo}.npy", np.column_stack([red.x, red.y]).astype(np.float32))
    save_npz(carpeta / "grafo_pie.npz", redes[Modo.PIE].grafo)

    for medida in MEDIDAS:
        red = redes[medida.modo]
        fuente = fuente_de(medida, puntos, parques)
        px, py = proyectar(fuente["lat"].to_numpy(), fuente["lon"].to_numpy())
        alcance: Alcance = red.costo_minimo(px, py, medida.hacia_los_puntos)
        np.save(
            carpeta / f"{medida.id}_minutos.npy", _a_minutos(red, alcance.costo).astype(np.float32)
        )
        np.save(carpeta / f"{medida.id}_lugar.npy", alcance.punto.astype(np.int32))
        fuente[["nombre", "lat", "lon"]].to_parquet(carpeta / f"{medida.id}_lugares.parquet")

    puntos.to_parquet(carpeta / "puntos.parquet")
    vias_rapidas.to_parquet(carpeta / "vias_rapidas.parquet")
    return carpeta


def construir_cercanias(raw: Path, interim: Path, procesados: Path) -> Path:
    """Trabajo completo: OSM → redes → puntos de interés → motor → hexágonos."""
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
    redes = {modo: construir_red(osm_rm, modo) for modo in Modo}
    carpeta_motor = guardar_motor(
        redes, puntos, parques, pt.vias_rapidas(osm_rm), procesados / "motor"
    )

    motor = MotorCercanias.desde_carpeta(carpeta_motor, con_grafo=False)
    grilla = hx.grilla(next(cartografia.glob("*_Manzanas.parquet")))
    cercanias = motor.evaluar(grilla["lat"].to_numpy(), grilla["lon"].to_numpy())
    cercanias.index = grilla.index
    resultado = grilla.join(cercanias)

    destino = procesados / "hexagonos.parquet"
    resultado.reset_index().to_parquet(destino)
    puntos.to_parquet(procesados / "puntos_interes.parquet")
    return destino
