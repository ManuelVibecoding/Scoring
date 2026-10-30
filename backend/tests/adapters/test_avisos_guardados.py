from datetime import date
from pathlib import Path

import pandas as pd

from score.adapters.avisos_guardados import AvisosGuardados


def _guardar(carpeta: Path, dia: str, filas: list[dict[str, object]]) -> None:
    base = {
        "fuente": "toctoc",
        "operacion": "arriendo",
        "tipo": "departamento",
        "comuna": "ÑUÑOA",
        "lat": -33.45,
        "lon": -70.60,
        "precio_clp": 500_000.0,
        "precio_uf": None,
        "superficie_m2": 50.0,
        "dormitorios": 2,
        "banos": 1,
        "horas_publicado": None,
        "url": "https://x.cl",
        "precision": "exacta",
        "comuna_consultada": "ÑUÑOA",
        "fecha_muestra": f"{dia[:4]}-{dia[4:6]}-{dia[6:]}",
    }
    carpeta.mkdir(parents=True, exist_ok=True)
    tabla = pd.DataFrame([{**base, **f} for f in filas])
    tabla.to_parquet(carpeta / f"avisos_arriendo_{dia}.parquet")


def test_sin_archivos_no_hay_avisos_ni_fecha(tmp_path: Path) -> None:
    avisos = AvisosGuardados(tmp_path / "avisos")
    assert avisos.fecha() is None
    assert avisos.en_rectangulo(-34, -33, -71, -70) == []
    assert avisos.todos().empty


def test_usa_el_archivo_mas_nuevo_y_cambia_si_aparece_otro(tmp_path: Path) -> None:
    carpeta = tmp_path / "avisos"
    _guardar(carpeta, "20261015", [{"id": "viejo"}])
    _guardar(carpeta, "20261022", [{"id": "a"}, {"id": "b", "fuente": "portalinmobiliario"}])
    avisos = AvisosGuardados(carpeta)

    assert avisos.fecha() == date(2026, 10, 22)
    assert sorted(a.id for a in avisos.en_rectangulo(-33.5, -33.4, -70.7, -70.5)) == ["a", "b"]
    assert avisos.fuentes() == ["portalinmobiliario", "toctoc"]

    _guardar(carpeta, "20261030", [{"id": "nuevo"}])  # el scraper corre con la app abierta
    assert avisos.fecha() == date(2026, 10, 30)
    assert [a.id for a in avisos.en_rectangulo(-33.5, -33.4, -70.7, -70.5)] == ["nuevo"]


def test_el_mapa_solo_muestra_avisos_bien_ubicados_y_con_precio(tmp_path: Path) -> None:
    carpeta = tmp_path / "avisos"
    _guardar(
        carpeta,
        "20261022",
        [{"id": "ok"}, {"id": "calle", "precision": "calle"}, {"id": "sin", "precio_clp": None}],
    )
    assert list(AvisosGuardados(carpeta).todos()["id"]) == ["ok"]
