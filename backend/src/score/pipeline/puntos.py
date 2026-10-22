"""Catálogo unificado de puntos de interés de la RM.

Junta fuentes oficiales (GTFS, Minsal, Mineduc) con OpenStreetMap en una sola tabla:
categoria, nombre, lat, lon, fuente. Los parques se guardan aparte porque se llega a
ellos por cualquier punto de su borde, no por un único punto.
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull, cKDTree

from score import config
from score.pipeline.red import proyectar

# Superficie mínima (m²) para contar como área verde y como parque.
AREA_MINIMA_PLAZA = 1_000.0
AREA_MINIMA_PARQUE = 20_000.0

# Horario punta mañana para medir la frecuencia de buses.
PUNTA_INICIO_S, PUNTA_FIN_S = 7 * 3600, 9 * 3600

_CATEGORIAS_OSM = {
    "supermercado",
    "mall",
    "farmacia",
    "banco",
    "cajero",
    "policia",
    "bomberos",
    "feria",
    "restaurante",
    "cafe",
    "gimnasio",
    "universidad",
    "carcel",
    "vertedero",
    "planta_tratamiento",
}

# Principales concentraciones de empleo de Santiago (centro aproximado de cada una).
CENTROS_DE_EMPLEO: tuple[tuple[str, float, float], ...] = (
    ("Santiago Centro", -33.4378, -70.6505),
    ("Providencia", -33.4255, -70.6110),
    ("El Golf / Sanhattan", -33.4150, -70.6000),
    ("Ciudad Empresarial", -33.3920, -70.6180),
)

# Vías de tráfico pesado: su ruido es la principal fuente de contaminación acústica.
VIAS_RAPIDAS = ("motorway", "trunk")


def _segundos(columna: str) -> str:
    """'25:10:00' → segundos (GTFS permite horas sobre 24)."""
    return (
        f"(CAST(split_part({columna}, ':', 1) AS INTEGER) * 3600"
        f" + CAST(split_part({columna}, ':', 2) AS INTEGER) * 60"
        f" + CAST(split_part({columna}, ':', 3) AS INTEGER))"
    )


def transporte(con: duckdb.DuckDBPyConnection, gtfs: Path) -> pd.DataFrame:
    """Estaciones de Metro y tren, y paraderos con su frecuencia en punta mañana."""

    def g(archivo: str) -> str:
        return f"read_csv('{(gtfs / archivo).as_posix()}', all_varchar=true)"

    ventana = PUNTA_FIN_S - PUNTA_INICIO_S
    return con.execute(
        f"""
        WITH servicios AS (SELECT service_id FROM {g("calendar.txt")} WHERE monday = '1'),
        viajes AS (
            SELECT t.trip_id, t.route_id, r.route_type, r.route_short_name
            FROM {g("trips.txt")} t JOIN {g("routes.txt")} r USING (route_id)
            WHERE t.service_id IN (SELECT service_id FROM servicios)
        ),
        frecuencias AS (
            SELECT trip_id,
                   SUM(GREATEST(0, LEAST({_segundos("end_time")}, {PUNTA_FIN_S})
                                   - GREATEST({_segundos("start_time")}, {PUNTA_INICIO_S}))
                       / CAST(headway_secs AS DOUBLE)) AS salidas
            FROM {g("frequencies.txt")} GROUP BY trip_id
        ),
        pasadas AS (
            SELECT st.stop_id, v.route_type, v.route_short_name,
                   COALESCE(f.salidas,
                            CASE WHEN {_segundos("st.departure_time")}
                                      BETWEEN {PUNTA_INICIO_S} AND {PUNTA_FIN_S}
                                 THEN 1 ELSE 0 END) AS salidas
            FROM {g("stop_times.txt")} st
            JOIN viajes v USING (trip_id)
            LEFT JOIN frecuencias f USING (trip_id)
        ),
        por_parada AS (
            SELECT COALESCE(NULLIF(s.parent_station, ''), s.stop_id) AS punto,
                   ANY_VALUE(p.route_type) AS route_type,
                   SUM(p.salidas) * 3600.0 / {ventana} AS salidas_hora,
                   LIST(DISTINCT p.route_short_name) AS recorridos
            FROM pasadas p JOIN {g("stops.txt")} s USING (stop_id)
            GROUP BY 1
        )
        SELECT CASE route_type WHEN '1' THEN 'metro' WHEN '3' THEN 'paradero'
                               ELSE 'tren' END AS categoria,
               regexp_replace(s.stop_name, '^P[A-Z]?\\d+-', '') AS nombre,
               CAST(s.stop_lat AS DOUBLE) AS lat, CAST(s.stop_lon AS DOUBLE) AS lon,
               'DTPM GTFS' AS fuente, p.salidas_hora, p.recorridos
        FROM por_parada p JOIN {g("stops.txt")} s ON s.stop_id = p.punto
        """
    ).df()


def salud(con: duckdb.DuckDBPyConnection, shp: Path) -> pd.DataFrame:
    return con.execute(
        f"""
        SELECT categoria, NOMBRE AS nombre, CAST(LATITUD AS DOUBLE) AS lat,
               CAST(LONGITUD AS DOUBLE) AS lon, 'Minsal' AS fuente
        FROM (
            SELECT *, UNNEST([
                CASE WHEN TIPO LIKE '%CESFAM%' OR TIPO LIKE '%CECOSF%' THEN 'cesfam' END,
                CASE WHEN UPPER(URGENCIA) = 'SI' THEN 'urgencia' END,
                CASE WHEN TIPO IN ('Hospital', 'Clínica') THEN 'hospital_clinica' END
            ]) AS categoria
            FROM ST_Read('{shp.as_posix()}')
            WHERE CUT_REGION = '{config.REGION_METROPOLITANA}'
        )
        WHERE categoria IS NOT NULL
        """
    ).df()


def educacion(con: duckdb.DuckDBPyConnection, csv: Path) -> pd.DataFrame:
    """Colegios (básica o media) y jardines (parvularia) en funcionamiento."""
    ensenanzas = [f"ENS_{i:02d}" for i in range(1, 12)]
    lista = "[" + ", ".join(ensenanzas) + "]"
    return con.execute(
        f"""
        WITH e AS (
            SELECT NOM_RBD AS nombre,
                   TRY_CAST(REPLACE(TRIM(LATITUD), ',', '.') AS DOUBLE) AS lat,
                   TRY_CAST(REPLACE(TRIM(LONGITUD), ',', '.') AS DOUBLE) AS lon,
                   list_filter({lista}, lambda x: x IS NOT NULL AND TRIM(x) NOT IN ('', '0'))
                       AS niveles
            FROM read_csv('{csv.as_posix()}', delim=';', header=true, all_varchar=true)
            WHERE COD_REG_RBD = '{config.REGION_METROPOLITANA}' AND ESTADO_ESTAB = '1'
        )
        SELECT 'jardin' AS categoria, nombre, lat, lon, 'Mineduc' AS fuente
        FROM e WHERE list_contains(niveles, '10') AND lat IS NOT NULL
        UNION ALL
        SELECT 'colegio', nombre, lat, lon, 'Mineduc'
        FROM e WHERE len(list_filter(niveles, lambda x: x <> '10')) > 0 AND lat IS NOT NULL
        """
    ).df()


def osm(con: duckdb.DuckDBPyConnection, osm_rm: Path) -> pd.DataFrame:
    df = con.execute(
        f"""
        SELECT CASE categoria WHEN 'jardin_infantil' THEN 'jardin' ELSE categoria END
                   AS categoria,
               COALESCE(nombre, marca) AS nombre, lat, lon, 'OpenStreetMap' AS fuente
        FROM '{(osm_rm / "pois.parquet").as_posix()}'
        """
    ).df()
    return df[df["categoria"].isin(_CATEGORIAS_OSM | {"jardin"})]


def accesos_autopista(con: duckdb.DuckDBPyConnection, osm_rm: Path) -> pd.DataFrame:
    """Nodos donde un enlace de autopista se conecta con la red de calles común.

    Los enlaces casi nunca tienen nombre en OSM, así que cada acceso toma el nombre de la
    autopista más cercana (por ejemplo, "Costanera Norte").
    """
    vias = (osm_rm / "vias.parquet").as_posix()
    nodos = (osm_rm / "nodos.parquet").as_posix()
    accesos = con.execute(
        f"""
        WITH enlaces AS (
            SELECT DISTINCT r.ref AS id FROM '{vias}', UNNEST(refs) AS r(ref)
            WHERE highway = 'motorway_link'
        ),
        comunes AS (
            SELECT DISTINCT r.ref AS id FROM '{vias}', UNNEST(refs) AS r(ref)
            WHERE highway NOT IN ('motorway', 'motorway_link')
        )
        SELECT n.lat, n.lon
        FROM enlaces JOIN comunes USING (id) JOIN '{nodos}' n USING (id)
        """
    ).df()
    autopistas = con.execute(
        f"""
        SELECT v.nombre, n.lat, n.lon
        FROM '{vias}' v, UNNEST(v.refs) AS r(ref) JOIN '{nodos}' n ON n.id = r.ref
        WHERE v.highway = 'motorway' AND v.nombre IS NOT NULL
        """
    ).df()
    if len(autopistas):
        arbol = cKDTree(
            np.column_stack(proyectar(autopistas["lat"].to_numpy(), autopistas["lon"].to_numpy()))
        )
        _, cercana = arbol.query(
            np.column_stack(proyectar(accesos["lat"].to_numpy(), accesos["lon"].to_numpy()))
        )
        accesos["nombre"] = autopistas["nombre"].to_numpy()[cercana]
    accesos["categoria"] = "acceso_autopista"
    accesos["fuente"] = "OpenStreetMap"
    return accesos


def parques(osm_rm: Path) -> pd.DataFrame:
    """Parques y plazas con su superficie (envolvente convexa del borde, en m²)."""
    df = pd.read_parquet(osm_rm / "parques.parquet")

    def superficie(fila: pd.Series) -> float:
        x, y = proyectar(np.asarray(fila["lats"]), np.asarray(fila["lons"]))
        puntos = np.unique(np.column_stack([x, y]).round(1), axis=0)
        if len(puntos) < 3:
            return 0.0
        try:
            return float(ConvexHull(puntos).volume)
        except Exception:  # puntos colineales
            return 0.0

    df["superficie_m2"] = df.apply(superficie, axis=1)
    df = df[(df["superficie_m2"] >= AREA_MINIMA_PLAZA) & (df["tipo"] != "playground")]
    df["categoria"] = np.where(df["superficie_m2"] >= AREA_MINIMA_PARQUE, "parque", "plaza")
    return df[["parque", "categoria", "nombre", "superficie_m2", "lats", "lons"]]


def centros_de_empleo() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"categoria": "centro_empleo", "nombre": n, "lat": lat, "lon": lon, "fuente": "Score"}
            for n, lat, lon in CENTROS_DE_EMPLEO
        ]
    )


def vias_rapidas(osm_rm: Path) -> pd.DataFrame:
    """Nodos de autopistas y vías troncales (para medir la exposición al ruido de tráfico)."""
    tipos = ", ".join(f"'{t}'" for t in VIAS_RAPIDAS)
    return (
        duckdb.connect()
        .execute(
            f"""
            SELECT DISTINCT n.lat, n.lon
            FROM '{(osm_rm / "vias.parquet").as_posix()}' v, UNNEST(v.refs) AS r(ref)
            JOIN '{(osm_rm / "nodos.parquet").as_posix()}' n ON n.id = r.ref
            WHERE v.highway IN ({tipos})
            """
        )
        .df()
    )


def construir_catalogo(
    gtfs: Path, minsal_shp: Path, mineduc_csv: Path, osm_rm: Path
) -> tuple[pd.DataFrame, pd.DataFrame]:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    puntos = pd.concat(
        [
            transporte(con, gtfs),
            salud(con, minsal_shp),
            educacion(con, mineduc_csv),
            osm(con, osm_rm),
            accesos_autopista(con, osm_rm),
            centros_de_empleo(),
        ],
        ignore_index=True,
    )
    return puntos.dropna(subset=["lat", "lon"]), parques(osm_rm)
