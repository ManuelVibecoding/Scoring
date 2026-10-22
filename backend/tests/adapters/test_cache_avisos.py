from datetime import datetime
from pathlib import Path

from score.adapters.cache_avisos import CacheAvisosDuckDB
from score.domain.avisos import Aviso, Operacion, TipoPropiedad
from score.domain.direcciones import Precision


def _aviso(
    id_: str,
    lat: float,
    precio: float | None = 500_000.0,
    fuente: str = "toctoc",
    precision: Precision = Precision.EXACTA,
) -> Aviso:
    return Aviso(
        fuente,
        id_,
        Operacion.ARRIENDO,
        TipoPropiedad.DEPARTAMENTO,
        "Ñuñoa",
        lat,
        -70.6,
        precio,
        None,
        50.0,
        2,
        None,
        3,
        "https://x.cl",
        precision,
    )


def test_guardar_reemplaza_la_consulta_anterior_del_mismo_portal(tmp_path: Path) -> None:
    cache = CacheAvisosDuckDB(tmp_path / "avisos.duckdb")
    t1, t2 = datetime(2026, 10, 1), datetime(2026, 10, 8)
    tipo = TipoPropiedad.DEPARTAMENTO

    assert cache.consultado_en("toctoc", "Ñuñoa", tipo) is None
    cache.guardar("toctoc", "Ñuñoa", tipo, [_aviso("a", -33.45), _aviso("b", -33.46)], t1)
    cache.guardar("portal", "Ñuñoa", tipo, [_aviso("p", -33.45, fuente="portal")], t1)
    cache.guardar("toctoc", "Ñuñoa", tipo, [_aviso("c", -33.45, precio=None)], t2)

    assert cache.consultado_en("toctoc", "Ñuñoa", tipo) == t2
    assert cache.consultado_en("portal", "Ñuñoa", tipo) == t1
    ids = sorted(a.id for a in cache.en_rectangulo(-33.5, -33.4, -70.7, -70.5))
    assert ids == ["c", "p"]


def test_precision_se_conserva_y_el_mapa_solo_usa_las_confiables(tmp_path: Path) -> None:
    cache = CacheAvisosDuckDB(tmp_path / "avisos.duckdb")
    momento = datetime(2026, 10, 1)
    avisos = [_aviso("ok", -33.45), _aviso("calle", -33.45, precision=Precision.CALLE)]
    cache.guardar("portal", "Ñuñoa", TipoPropiedad.DEPARTAMENTO, avisos, momento)

    leidos = {a.id: a for a in cache.en_rectangulo(-33.5, -33.4, -70.7, -70.5)}
    assert leidos["calle"].precision is Precision.CALLE
    assert list(cache.todos()["id"]) == ["ok"]


def test_consulta_sin_resultados_igual_queda_registrada(tmp_path: Path) -> None:
    cache = CacheAvisosDuckDB(tmp_path / "avisos.duckdb")
    cache.guardar("toctoc", "Alhué", TipoPropiedad.CASA, [], datetime(2026, 10, 1))
    assert cache.consultado_en("toctoc", "Alhué", TipoPropiedad.CASA) == datetime(2026, 10, 1)
