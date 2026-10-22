"""Extracción de OpenStreetMap para la Región Metropolitana.

Lee el archivo .osm.pbf de Chile con DuckDB (ST_ReadOSM) y deja en data/interim/osm_rm/:

- nodos.parquet   id, lat, lon de los nodos dentro del rectángulo de la RM
- vias.parquet    calles (highway) con su lista ordenada de nodos
- parques.parquet parques y plazas: nodos de su borde y superficie aproximada
- pois.parquet    puntos de interés (comercio, servicios, emergencias)

Cada paso recorre el archivo completo una vez; el resultado se reutiliza si ya existe.
"""

from pathlib import Path

import duckdb

# Rectángulo que contiene a las 52 comunas de la RM, con margen.
LON_MIN, LON_MAX = -71.75, -69.75
LAT_MIN, LAT_MAX = -34.32, -32.90

# Etiquetas OSM que se guardan como puntos de interés: (clave, valor) → categoría.
ETIQUETAS_POI: dict[tuple[str, str], str] = {
    ("shop", "supermarket"): "supermercado",
    ("shop", "mall"): "mall",
    ("shop", "department_store"): "mall",
    ("amenity", "pharmacy"): "farmacia",
    ("amenity", "bank"): "banco",
    ("amenity", "atm"): "cajero",
    ("amenity", "police"): "policia",
    ("amenity", "fire_station"): "bomberos",
    ("amenity", "kindergarten"): "jardin_infantil",
    ("amenity", "marketplace"): "feria",
    ("amenity", "restaurant"): "restaurante",
    ("amenity", "cafe"): "cafe",
    ("leisure", "fitness_centre"): "gimnasio",
    ("amenity", "university"): "universidad",
}


def _condicion_poi(alias: str = "tags") -> str:
    return " OR ".join(f"{alias}['{k}'] = '{v}'" for k, v in ETIQUETAS_POI)


def _categoria_poi(alias: str = "tags") -> str:
    casos = " ".join(
        f"WHEN {alias}['{k}'] = '{v}' THEN '{cat}'" for (k, v), cat in ETIQUETAS_POI.items()
    )
    return f"CASE {casos} END"


def extraer_osm_rm(pbf: Path, destino: Path, forzar: bool = False) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; SET preserve_insertion_order = false;")
    fuente = f"ST_ReadOSM('{pbf.as_posix()}')"
    salida = {
        n: (destino / f"{n}.parquet").as_posix() for n in ("nodos", "vias", "parques", "pois")
    }
    nodos_brutos = (destino / "_nodos_con_tags.parquet").as_posix()

    if forzar or not (destino / "_nodos_con_tags.parquet").exists():
        con.execute(
            f"""
            COPY (
                SELECT id, lat, lon,
                       CASE WHEN cardinality(tags) > 0 THEN tags END AS tags
                FROM {fuente}
                WHERE kind = 'node'
                  AND lat BETWEEN {LAT_MIN} AND {LAT_MAX}
                  AND lon BETWEEN {LON_MIN} AND {LON_MAX}
            ) TO '{nodos_brutos}' (FORMAT parquet)
            """
        )

    if forzar or not (destino / "vias.parquet").exists():
        # Se guardan todas las vías de Chile con highway; el cruce con los nodos de la RM
        # deja solo las que caen dentro del rectángulo.
        con.execute(
            f"""
            COPY (
                WITH vias AS (
                    SELECT id, tags['highway'] AS highway, tags['oneway'] AS oneway,
                           tags['foot'] AS foot, tags['access'] AS acceso,
                           tags['name'] AS nombre, tags['junction'] AS cruce, refs
                    FROM {fuente}
                    WHERE kind = 'way' AND tags['highway'] IS NOT NULL
                ),
                dentro AS (
                    SELECT DISTINCT v.id
                    FROM vias v, UNNEST(v.refs) AS r(ref)
                    JOIN '{nodos_brutos}' n ON n.id = r.ref
                )
                SELECT v.* FROM vias v JOIN dentro USING (id)
            ) TO '{salida["vias"]}' (FORMAT parquet)
            """
        )

    if forzar or not (destino / "parques.parquet").exists():
        con.execute(
            f"""
            COPY (
                WITH areas AS (
                    SELECT id, kind, tags['name'] AS nombre, tags['leisure'] AS tipo,
                           refs, ref_types, ref_roles
                    FROM {fuente}
                    WHERE kind IN ('way', 'relation')
                      AND tags['leisure'] IN ('park', 'garden', 'playground')
                      AND COALESCE(tags['access'], '') NOT IN ('private', 'no')
                ),
                -- Las relaciones (multipolígonos) se expanden a las vías de su borde exterior.
                vias_de_relaciones AS (
                    SELECT a.id AS parque, a.nombre, a.tipo, a.refs[u.i] AS via
                    FROM areas a, UNNEST(range(1, len(a.refs) + 1)) AS u(i)
                    WHERE a.kind = 'relation'
                      AND CAST(a.ref_types[u.i] AS VARCHAR) = 'way'
                      AND a.ref_roles[u.i] = 'outer'
                ),
                bordes AS (
                    SELECT id AS parque, nombre, tipo, refs FROM areas WHERE kind = 'way'
                    UNION ALL
                    SELECT r.parque, r.nombre, r.tipo, w.refs
                    FROM vias_de_relaciones r
                    JOIN (SELECT id, refs FROM {fuente} WHERE kind = 'way') w ON w.id = r.via
                ),
                puntos AS (
                    SELECT b.parque, b.nombre, b.tipo, n.lat, n.lon, n.id AS nodo
                    FROM bordes b, UNNEST(b.refs) AS r(ref)
                    JOIN '{nodos_brutos}' n ON n.id = r.ref
                )
                SELECT parque, ANY_VALUE(nombre) AS nombre, ANY_VALUE(tipo) AS tipo,
                       LIST(nodo) AS nodos, LIST(lat) AS lats, LIST(lon) AS lons
                FROM puntos GROUP BY parque
            ) TO '{salida["parques"]}' (FORMAT parquet)
            """
        )

    if forzar or not (destino / "pois.parquet").exists():
        con.execute(
            f"""
            COPY (
                SELECT 'node' AS tipo_osm, id, {_categoria_poi()} AS categoria,
                       tags['name'] AS nombre, tags['brand'] AS marca, lat, lon
                FROM '{nodos_brutos}'
                WHERE tags IS NOT NULL AND ({_condicion_poi()})
                UNION ALL
                SELECT 'way', w.id, {_categoria_poi("w.tags")}, w.tags['name'],
                       w.tags['brand'], AVG(n.lat), AVG(n.lon)
                FROM (
                    SELECT id, tags, refs FROM {fuente}
                    WHERE kind = 'way' AND ({_condicion_poi()})
                ) w, UNNEST(w.refs) AS r(ref)
                JOIN '{nodos_brutos}' n ON n.id = r.ref
                GROUP BY ALL
            ) TO '{salida["pois"]}' (FORMAT parquet)
            """
        )

    if forzar or not (destino / "nodos.parquet").exists():
        # Solo los nodos que forman calles o bordes de parques: la red no necesita el resto.
        con.execute(
            f"""
            COPY (
                WITH usados AS (
                    SELECT DISTINCT r.ref AS id FROM '{salida["vias"]}', UNNEST(refs) AS r(ref)
                    UNION
                    SELECT DISTINCT u.nodo FROM '{salida["parques"]}', UNNEST(nodos) AS u(nodo)
                )
                SELECT n.id, n.lat, n.lon FROM '{nodos_brutos}' n JOIN usados USING (id)
            ) TO '{salida["nodos"]}' (FORMAT parquet)
            """
        )
    return destino
