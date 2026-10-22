"""Caché de avisos en DuckDB (un archivo local): crece con cada comuna que se consulta.

Cada consulta queda registrada por portal, comuna y tipo, para saber cuándo hay que
volver a pedirla.
"""

import threading
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from score.domain.avisos import Aviso, Operacion, TipoPropiedad
from score.domain.direcciones import Precision

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS avisos (
    fuente VARCHAR, id VARCHAR, operacion VARCHAR, tipo VARCHAR, comuna VARCHAR,
    lat DOUBLE, lon DOUBLE, precio_clp DOUBLE, precio_uf DOUBLE, superficie_m2 DOUBLE,
    dormitorios INTEGER, banos INTEGER, horas_publicado INTEGER, url VARCHAR,
    precision VARCHAR, comuna_consultada VARCHAR, consultado_en TIMESTAMP
);
CREATE TABLE IF NOT EXISTS consultas (
    fuente VARCHAR, comuna VARCHAR, tipo VARCHAR, consultado_en TIMESTAMP, avisos INTEGER
);
"""
_COLUMNAS_AVISO = list(Aviso.__dataclass_fields__)


class CacheAvisosDuckDB:
    def __init__(self, archivo: Path) -> None:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        self._con = duckdb.connect(str(archivo))
        self._con.execute("SET enable_progress_bar = false")
        self._con.execute(_ESQUEMA)
        self._candado = threading.Lock()

    def consultado_en(self, fuente: str, comuna: str, tipo: TipoPropiedad) -> datetime | None:
        with self._candado:
            fila = self._con.execute(
                "SELECT MAX(consultado_en) FROM consultas"
                " WHERE fuente = ? AND comuna = ? AND tipo = ?",
                [fuente, comuna, str(tipo)],
            ).fetchone()
        return fila[0] if fila else None

    def guardar(
        self,
        fuente: str,
        comuna: str,
        tipo: TipoPropiedad,
        avisos: list[Aviso],
        momento: datetime,
    ) -> None:
        tabla = pd.DataFrame([asdict(a) for a in avisos], columns=_COLUMNAS_AVISO)
        for columna in ("operacion", "tipo", "precision"):
            tabla[columna] = tabla[columna].astype(str)
        tabla["comuna_consultada"] = comuna
        tabla["consultado_en"] = momento
        with self._candado:
            self._con.execute(
                "DELETE FROM avisos WHERE fuente = ? AND comuna_consultada = ? AND tipo = ?",
                [fuente, comuna, str(tipo)],
            )
            if len(tabla):
                self._con.register("nuevos", tabla)
                self._con.execute("INSERT INTO avisos SELECT * FROM nuevos")
                self._con.unregister("nuevos")
            self._con.execute(
                "INSERT INTO consultas VALUES (?, ?, ?, ?, ?)",
                [fuente, comuna, str(tipo), momento, len(tabla)],
            )

    def en_rectangulo(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float
    ) -> list[Aviso]:
        with self._candado:
            filas = self._con.execute(
                f"""
                SELECT {", ".join(_COLUMNAS_AVISO)} FROM avisos
                WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?
                """,
                [lat_min, lat_max, lon_min, lon_max],
            ).fetchall()
        return [_a_aviso(dict(zip(_COLUMNAS_AVISO, f, strict=True))) for f in filas]

    def todos(self) -> pd.DataFrame:
        """Todos los avisos ubicados con confianza, para dibujarlos en el mapa."""
        with self._candado:
            return self._con.execute(
                """
                SELECT fuente, id, tipo, lat, lon, precio_clp, superficie_m2, dormitorios, url
                FROM avisos WHERE precision IN ('exacta', 'interpolada') AND precio_clp > 0
                """
            ).df()

    def importar_muestra(self, muestra: Path) -> int:
        """Carga una muestra del pipeline (`score precios`) si la caché está vacía."""
        with self._candado:
            fila = self._con.execute("SELECT COUNT(*) FROM consultas").fetchone()
        if fila and fila[0] > 0:
            return 0
        tabla = pd.read_parquet(muestra)
        if "precision" not in tabla.columns:
            tabla["precision"] = Precision.EXACTA.value
        momento = datetime.fromisoformat(str(tabla["fecha_muestra"].iloc[0]))
        total = 0
        grupos = tabla.groupby(["fuente", "comuna_consultada", "tipo"])
        for (fuente, comuna, tipo), grupo in grupos:
            registros = grupo[_COLUMNAS_AVISO].to_dict("records")
            avisos = [_a_aviso({str(k): v for k, v in r.items()}) for r in registros]
            self.guardar(str(fuente), str(comuna), TipoPropiedad(str(tipo)), avisos, momento)
            total += len(avisos)
        return total


def _vacio(valor: Any) -> bool:
    return valor is None or (isinstance(valor, float) and pd.isna(valor))


def _real(valor: Any) -> float | None:
    return None if _vacio(valor) else float(valor)


def _entero(valor: Any) -> int | None:
    return None if _vacio(valor) else int(valor)


def _a_aviso(d: dict[str, Any]) -> Aviso:
    return Aviso(
        fuente=str(d["fuente"]),
        id=str(d["id"]),
        operacion=Operacion(str(d["operacion"])),
        tipo=TipoPropiedad(str(d["tipo"])),
        comuna=str(d["comuna"]),
        lat=float(d["lat"]),
        lon=float(d["lon"]),
        precio_clp=_real(d["precio_clp"]),
        precio_uf=_real(d["precio_uf"]),
        superficie_m2=_real(d["superficie_m2"]),
        dormitorios=_entero(d["dormitorios"]),
        banos=_entero(d["banos"]),
        horas_publicado=_entero(d["horas_publicado"]),
        url="" if _vacio(d["url"]) else str(d["url"]),
        precision=Precision(str(d.get("precision") or Precision.EXACTA)),
    )
