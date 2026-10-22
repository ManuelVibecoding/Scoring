"""Ficha de las 52 comunas de la Región Metropolitana.

Una fila por comuna (identificada por su código CUT) y una columna por indicador.
Cada función lee una fuente y devuelve un DataFrame indexado por CUT; `construir_fichas`
las une y escribe el resultado en data/processed/.
"""

import re
from pathlib import Path

import duckdb
import pandas as pd
import pdfplumber

from score import config
from score.pipeline.extraccion import asegurar_extraido
from score.pipeline.normalizacion import normalizar_nombre

# Delitos de mayor connotación social según la clasificación del CEAD.
DMCS = (
    "Robos con violencia o intimidación",
    "Robo violento de vehículo motorizado",
    "Robo por sorpresa",
    "Robo de vehículo motorizado",
    "Robo de objetos de o desde vehículo",
    "Robo en lugar habitado",
    "Robo en lugar no habitado",
    "Otros robos con fuerza en las cosas",
    "Hurtos",
    "Lesiones leves",
    "Lesiones menos graves",
    "Lesiones graves o gravísimas",
    "Homicidios",
    "Violaciones",
)
# Los que más pesan para quien vive en el lugar (no para quien solo trabaja o compra ahí).
DELITOS_VIOLENTOS = (
    "Robos con violencia o intimidación",
    "Robo violento de vehículo motorizado",
    "Robo por sorpresa",
    "Homicidios",
)
ROBO_VIVIENDA = ("Robo en lugar habitado",)

NIVELES_ICVU = ("Bajo", "Medio bajo", "Medio alto", "Alto")
# Nombres abreviados en las tablas del informe ICVU.
_ALIAS_ICVU = {"p. aguirre cerda": "pedro aguirre cerda"}
_FILA_ICVU = re.compile(
    r"^(?:(?:Mejoran|Disminuyen|Mantienen)\s+)?(?P<comuna>[^\d↑↓=]+?)\s+"
    r"(?:[↑↓=]\s+){6}"
    r"(?P<n2015>Medio alto|Medio bajo|Alto|Bajo)\s+(?P<n2025>Medio alto|Medio bajo|Alto|Bajo)\s*$"
)


def _conexion() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    return con


# ---------------------------------------------------------------- Censo 2024


def _num(col: str) -> str:
    """Columna de texto del censo a número: acepta coma decimal y deja '*' como NULL."""
    return f"TRY_CAST(REPLACE({col}, ',', '.') AS DOUBLE)"


def _suma(col: str) -> str:
    return f"SUM({_num(col)})"


def _suma_de(*cols: str) -> str:
    return " + ".join(f"COALESCE({_suma(c)}, 0)" for c in cols)


def censo(con: duckdb.DuckDBPyConnection, csv: Path) -> pd.DataFrame:
    """Indicadores demográficos y de vivienda desde la base manzana–entidad.

    Incluye las filas "contenedor comunal", que agrupan lo que el INE reserva a nivel de
    manzana: sin ellas la población de la RM queda ~1,5% corta.
    """
    s = _suma
    adultos = " + ".join(
        _num(c) for c in ("n_edad_18_24", "n_edad_25_44", "n_edad_45_59", "n_edad_60_mas")
    )
    cine = _suma_de(
        "n_cine_nunca_curso_primera_infancia",
        "n_cine_primaria",
        "n_cine_secundaria",
        "n_cine_terciaria_maestria_doctorado",
        "n_cine_especial_diferencial",
    )
    transporte = _suma_de(
        "n_transporte_auto",
        "n_transporte_publico",
        "n_transporte_camina",
        "n_transporte_bicicleta",
        "n_transporte_motocicleta",
        "n_transporte_cab_lan_bote",
        "n_transporte_otros",
    )
    tipos_vivienda = _suma_de(
        "n_tipo_viv_casa",
        "n_tipo_viv_depto",
        "n_tipo_viv_indigena",
        "n_tipo_viv_pieza",
        "n_tipo_viv_mediagua",
        "n_tipo_viv_movil",
        "n_tipo_viv_otro",
    )
    consulta = f"""
        WITH b AS (
            SELECT * FROM read_csv('{csv.as_posix()}', delim=';', header=true, all_varchar=true)
            WHERE COD_REGION = '{config.REGION_METROPOLITANA}'
        )
        SELECT
            CAST(CUT AS INTEGER) AS cut,
            {s("n_per")} AS poblacion,
            {s("n_hog")} AS hogares,
            {s("n_vp")} AS viviendas,
            ({s("n_edad_0_5")} + {s("n_edad_6_13")} + {s("n_edad_14_17")}) / {s("n_per")}
                AS pct_menores_18,
            {s("n_edad_60_mas")} / {s("n_per")} AS pct_60_mas,
            {s("n_inmigrantes")} / {s("n_per")} AS pct_inmigrantes,
            SUM({_num("prom_escolaridad18")} * ({adultos}))
                / SUM(CASE WHEN {_num("prom_escolaridad18")} IS NOT NULL
                           THEN {adultos} END) AS escolaridad_promedio,
            {s("n_cine_terciaria_maestria_doctorado")} / ({cine}) AS pct_educacion_superior,
            {s("n_desocupado")} / ({s("n_ocupado")} + {s("n_desocupado")}) AS pct_desocupacion,
            {s("n_viv_hacinadas")} / {s("n_vp_ocupada")} AS pct_viviendas_hacinadas,
            ({s("n_tenencia_arrendada_contrato")} + {s("n_tenencia_arrendada_sin_contrato")})
                / {s("n_hog")} AS pct_hogares_arrendatarios,
            {s("n_tipo_viv_depto")} / ({tipos_vivienda}) AS pct_departamentos,
            {s("n_transporte_publico")} / ({transporte}) AS pct_viaja_transporte_publico,
            {s("n_transporte_auto")} / ({transporte}) AS pct_viaja_auto,
            {s("n_serv_internet_fija")} / {s("n_hog")} AS pct_hogares_internet_fija
        FROM b GROUP BY 1
    """
    return con.execute(consulta).df().set_index("cut")


def territorio(con: duckdb.DuckDBPyConnection, comunal: Path) -> pd.DataFrame:
    """Nombre, provincia y superficie (km², proyectada a UTM 19S) de cada comuna."""
    return (
        con.execute(
            f"""
            SELECT CUT AS cut, COMUNA AS comuna, PROVINCIA AS provincia,
                   ST_Area(ST_Transform(SHAPE, 'EPSG:4674', 'EPSG:32719', always_xy := true))
                       / 1e6 AS superficie_km2
            FROM '{comunal.as_posix()}'
            """
        )
        .df()
        .set_index("cut")
    )


# ---------------------------------------------------------------- Pobreza (Casen 2024)


def _tabla_sae(xlsx: Path, columna_valor: int, nombre: str) -> pd.Series:
    df = pd.read_excel(xlsx, header=None, skiprows=3)
    df = df[pd.to_numeric(df[0], errors="coerce").notna()]
    serie = pd.Series(df[columna_valor].astype(float).values, index=df[0].astype(int), name=nombre)
    return serie[serie.index // 1000 == config.REGION_METROPOLITANA]


def pobreza(carpeta: Path) -> pd.DataFrame:
    return pd.concat(
        [
            _tabla_sae(carpeta / "sae_ingresos_2024.xlsx", 5, "pct_pobreza_ingresos"),
            _tabla_sae(
                carpeta / "sae_multidimensional_2024.xlsx", 5, "pct_pobreza_multidimensional"
            ),
            _tabla_sae(
                carpeta / "sae-inseguridad-alimentaria-2024.xlsx",
                3,
                "pct_inseguridad_alimentaria",
            ),
        ],
        axis=1,
    ).rename_axis("cut")


# ---------------------------------------------------------------- Delitos (CEAD)


def delitos(casos: pd.DataFrame, poblacion: pd.Series) -> pd.DataFrame:
    """Tasas por 100 mil habitantes del último año completo y su variación anual.

    `casos` tiene columnas cut_comuna, fecha, delito y delito_n (un registro por mes).
    """
    casos = casos.assign(
        cut=casos["cut_comuna"].astype(int), anio=pd.to_datetime(casos["fecha"]).dt.year
    )
    casos = casos[casos["cut"] // 1000 == config.REGION_METROPOLITANA]
    meses = casos.groupby("anio")["fecha"].nunique()
    anio = int(meses[meses == 12].index.max())

    def total(anio_: int, tipos: tuple[str, ...]) -> pd.Series:
        filtro = (casos["anio"] == anio_) & casos["delito"].isin(tipos)
        return casos[filtro].groupby("cut")["delito_n"].sum()

    dmcs, dmcs_previo = total(anio, DMCS), total(anio - 1, DMCS)
    por_100k = 100_000 / poblacion
    return pd.DataFrame(
        {
            "anio_delitos": anio,
            "tasa_dmcs_100k": dmcs * por_100k,
            "tasa_delitos_violentos_100k": total(anio, DELITOS_VIOLENTOS) * por_100k,
            "tasa_robo_vivienda_100k": total(anio, ROBO_VIVIENDA) * por_100k,
            "homicidios": total(anio, ("Homicidios",)),
            "variacion_dmcs_anual": dmcs / dmcs_previo - 1,
        }
    ).rename_axis("cut")


# ---------------------------------------------------------------- Salud (Minsal)


def salud(con: duckdb.DuckDBPyConnection, shp: Path) -> pd.DataFrame:
    return (
        con.execute(
            f"""
            SELECT CAST(CUT_COMUNA AS INTEGER) AS cut,
                   COUNT(*) FILTER (WHERE TIPO LIKE '%CESFAM%' OR TIPO LIKE '%CECOSF%')
                       AS centros_salud_familiar,
                   COUNT(*) FILTER (WHERE UPPER(URGENCIA) = 'SI') AS servicios_urgencia,
                   COUNT(*) FILTER (WHERE TIPO = 'Hospital') AS hospitales,
                   COUNT(*) FILTER (WHERE TIPO = 'Clínica') AS clinicas,
                   COUNT(*) AS establecimientos_salud
            FROM ST_Read('{shp.as_posix()}')
            WHERE CUT_REGION = '{config.REGION_METROPOLITANA}'
            GROUP BY 1
            """
        )
        .df()
        .set_index("cut")
    )


# ---------------------------------------------------------------- Educación (Mineduc)


def educacion(con: duckdb.DuckDBPyConnection, csv: Path) -> pd.DataFrame:
    """Establecimientos en funcionamiento (ESTADO_ESTAB = 1) por dependencia."""
    ensenanzas = ", ".join(f"ENS_{i:02d}" for i in range(1, 12))
    return (
        con.execute(
            f"""
            SELECT CAST(COD_COM_RBD AS INTEGER) AS cut,
                   COUNT(*) AS establecimientos_educacionales,
                   COUNT(*) FILTER (WHERE '10' IN ({ensenanzas})) AS con_educacion_parvularia,
                   COUNT(*) FILTER (WHERE COD_DEPE2 IN ('1', '5')) AS publicos,
                   COUNT(*) FILTER (WHERE COD_DEPE2 = '2') AS particulares_subvencionados,
                   COUNT(*) FILTER (WHERE COD_DEPE2 = '3') AS particulares_pagados,
                   SUM(TRY_CAST(MAT_TOTAL AS INTEGER)) AS matricula
            FROM read_csv('{csv.as_posix()}', delim=';', header=true, all_varchar=true)
            WHERE COD_REG_RBD = '{config.REGION_METROPOLITANA}' AND ESTADO_ESTAB = '1'
            GROUP BY 1
            """
        )
        .df()
        .set_index("cut")
    )


# ---------------------------------------------------------------- Transporte (GTFS)


def transporte(con: duckdb.DuckDBPyConnection, gtfs: Path, comunal: Path) -> pd.DataFrame:
    """Paraderos de bus y estaciones de Metro dentro de cada comuna."""

    def g(archivo: str) -> str:
        return f"read_csv('{(gtfs / archivo).as_posix()}', all_varchar=true)"

    return (
        con.execute(
            f"""
            WITH metro AS (
                SELECT DISTINCT COALESCE(NULLIF(s.parent_station, ''), s.stop_id) AS estacion
                FROM {g("routes.txt")} r
                JOIN {g("trips.txt")} t USING (route_id)
                JOIN {g("stop_times.txt")} st USING (trip_id)
                JOIN {g("stops.txt")} s USING (stop_id)
                WHERE r.route_type = '1'
            ),
            puntos AS (
                SELECT s.stop_id,
                       s.stop_id IN (SELECT estacion FROM metro) AS es_metro,
                       COALESCE(s.location_type, '0') = '0'
                           AND s.stop_id NOT IN (SELECT estacion FROM metro)
                           AND s.stop_id LIKE 'P%' AS es_paradero,
                       ST_Point(CAST(s.stop_lon AS DOUBLE), CAST(s.stop_lat AS DOUBLE)) AS geom
                FROM {g("stops.txt")} s
            )
            SELECT c.CUT AS cut,
                   COUNT(*) FILTER (WHERE p.es_paradero) AS paraderos_bus,
                   COUNT(*) FILTER (WHERE p.es_metro) AS estaciones_metro
            FROM '{comunal.as_posix()}' c
            JOIN puntos p ON ST_Contains(c.SHAPE, p.geom)
            GROUP BY 1
            """
        )
        .df()
        .set_index("cut")
    )


# ---------------------------------------------------------------- ICVU 2025


def niveles_icvu(texto: str) -> dict[str, str]:
    """Extrae {comuna: nivel 2025} de las tablas de cambios del informe ICVU."""
    niveles: dict[str, str] = {}
    for linea in texto.splitlines():
        if m := _FILA_ICVU.match(linea.strip()):
            niveles[m["comuna"].strip()] = m["n2025"]
    return niveles


def icvu(pdf: Path, nombres: pd.Series) -> pd.DataFrame:
    with pdfplumber.open(pdf) as documento:
        texto = "\n".join(pagina.extract_text() or "" for pagina in documento.pages)
    por_nombre: dict[str, str] = {}
    for comuna, nivel_2025 in niveles_icvu(texto).items():
        clave = normalizar_nombre(comuna)
        por_nombre[_ALIAS_ICVU.get(clave, clave)] = nivel_2025
    nivel = nombres.map(lambda n: por_nombre.get(normalizar_nombre(n)))
    return pd.DataFrame(
        {
            "icvu_nivel": nivel,
            "icvu_nivel_orden": nivel.map(
                lambda n: NIVELES_ICVU.index(n) + 1 if isinstance(n, str) else None
            ),
        }
    )


# ---------------------------------------------------------------- Ficha completa


def construir_fichas(raw: Path, interim: Path, procesados: Path) -> Path:
    cartografia = asegurar_extraido(
        raw, interim, "censo2024_cartografia_rm", "cartografia_censo2024_R13.zip"
    )
    base_censo = asegurar_extraido(
        raw, interim, "censo2024_manzana_entidad", "Base_manzana_entidad_CPV24.zip"
    )
    minsal = asegurar_extraido(
        raw, interim, "minsal_establecimientos", "ESTABLECIMIENTOS_12062026_DES.zip"
    )
    gtfs = asegurar_extraido(raw, interim, "dtpm_gtfs", "GTFS_20261003.zip")
    mineduc = asegurar_extraido(
        raw, interim, "mineduc_directorio", "Directorio-Oficial-EE-2025.rar"
    )
    comunal = next(cartografia.glob("*_Comunal.parquet"))

    con = _conexion()
    base = territorio(con, comunal)
    demografia = censo(con, next(base_censo.glob("*.csv")))
    fichas = base.join(demografia)
    fichas["densidad_hab_km2"] = fichas["poblacion"] / fichas["superficie_km2"]

    casos = pd.read_parquet(raw / "cead_delitos" / "cead_delincuencia_chile.parquet")
    fichas = (
        fichas.join(pobreza(raw / "casen_pobreza_comunal"))
        .join(delitos(casos, fichas["poblacion"]))
        .join(salud(con, next(minsal.glob("*.shp"))))
        .join(educacion(con, next(mineduc.glob("*.csv"))))
        .join(transporte(con, gtfs, comunal))
        .join(icvu(raw / "icvu" / "icvu_2025.pdf", fichas["comuna"]))
    )
    conteos = [
        "centros_salud_familiar",
        "servicios_urgencia",
        "hospitales",
        "clinicas",
        "establecimientos_salud",
        "establecimientos_educacionales",
        "con_educacion_parvularia",
        "publicos",
        "particulares_subvencionados",
        "particulares_pagados",
        "paraderos_bus",
        "estaciones_metro",
    ]
    fichas[conteos] = fichas[conteos].fillna(0).astype(int)
    fichas = fichas.sort_index()

    procesados.mkdir(parents=True, exist_ok=True)
    destino = procesados / "comunas.parquet"
    fichas.to_parquet(destino)
    fichas.to_csv(procesados / "comunas.csv", encoding="utf-8-sig")
    return destino
