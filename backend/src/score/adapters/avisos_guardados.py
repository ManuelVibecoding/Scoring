"""Avisos de arriendo guardados por el scraper (`score precios`). La app solo los lee.

Cada corrida del scraper deja un archivo con fecha en data/interim/avisos/. La app usa el
más nuevo; si aparece uno más nuevo con la app abierta, lo carga en la consulta siguiente.
Sin archivos, la app funciona igual, pero sin arriendos.
"""

import threading
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from score.domain.avisos import Aviso, Operacion, TipoPropiedad
from score.domain.direcciones import Precision

PATRON_MUESTRAS = "avisos_arriendo_*.parquet"
_COLUMNAS_AVISO = list(Aviso.__dataclass_fields__)
_CONFIABLES = (Precision.EXACTA.value, Precision.INTERPOLADA.value)


def ultima_muestra(carpeta: Path) -> Path | None:
    """El archivo más nuevo (el nombre lleva la fecha, así que el orden alfabético sirve)."""
    muestras = sorted(carpeta.glob(PATRON_MUESTRAS))
    return muestras[-1] if muestras else None


class AvisosGuardados:
    def __init__(self, carpeta: Path) -> None:
        self._carpeta = carpeta
        self._candado = threading.Lock()
        self._archivo: Path | None = None
        self._tabla = pd.DataFrame(columns=[*_COLUMNAS_AVISO, "fecha_muestra"])

    def _al_dia(self) -> pd.DataFrame:
        with self._candado:
            archivo = ultima_muestra(self._carpeta)
            if archivo is not None and archivo != self._archivo:
                self._tabla = _leer(archivo)
                self._archivo = archivo
            return self._tabla

    def fecha(self) -> date | None:
        """Día en que se corrió el scraper que generó los datos en uso."""
        tabla = self._al_dia()
        return date.fromisoformat(str(tabla["fecha_muestra"].iloc[0])) if len(tabla) else None

    def fuentes(self) -> list[str]:
        return sorted(self._al_dia()["fuente"].unique().tolist())

    def en_rectangulo(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float
    ) -> list[Aviso]:
        tabla = self._al_dia()
        dentro = tabla[
            tabla["lat"].between(lat_min, lat_max) & tabla["lon"].between(lon_min, lon_max)
        ]
        registros = dentro.to_dict("records")
        return [_a_aviso({str(k): v for k, v in r.items()}) for r in registros]

    def todos(self) -> pd.DataFrame:
        """Avisos ubicados con confianza y con precio, para dibujarlos en el mapa."""
        tabla = self._al_dia()
        utiles = tabla[tabla["precision"].isin(_CONFIABLES) & (tabla["precio_clp"] > 0)]
        columnas = ["fuente", "id", "tipo", "lat", "lon", "precio_clp", "superficie_m2"]
        return utiles[[*columnas, "dormitorios", "url"]]


def _leer(archivo: Path) -> pd.DataFrame:
    tabla = pd.read_parquet(archivo)
    if "precision" not in tabla.columns:  # muestras anteriores a la geocodificación propia
        tabla["precision"] = Precision.EXACTA.value
    tabla = tabla.dropna(subset=["lat", "lon"])
    return tabla.drop_duplicates(subset=["fuente", "id"]).reset_index(drop=True)


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
