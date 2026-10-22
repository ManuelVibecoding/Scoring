from datetime import datetime
from pathlib import Path

from score.adapters.cache_avisos import CacheAvisosDuckDB
from score.domain.avisos import Aviso, Operacion, TipoPropiedad


def _aviso(id_: str, lat: float, precio: float | None = 500_000.0) -> Aviso:
    return Aviso(
        "toctoc",
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
    )


def test_guardar_reemplaza_la_consulta_anterior_de_la_comuna(tmp_path: Path) -> None:
    cache = CacheAvisosDuckDB(tmp_path / "avisos.duckdb")
    t1, t2 = datetime(2026, 10, 1), datetime(2026, 10, 8)
    tipo = TipoPropiedad.DEPARTAMENTO

    assert cache.consultado_en("Ñuñoa", tipo) is None
    cache.guardar("Ñuñoa", tipo, [_aviso("a", -33.45), _aviso("b", -33.46)], t1)
    cache.guardar("Ñuñoa", tipo, [_aviso("c", -33.45, precio=None)], t2)

    assert cache.consultado_en("Ñuñoa", tipo) == t2
    [aviso] = cache.en_rectangulo(-33.5, -33.4, -70.7, -70.5)
    assert aviso.id == "c"
    assert aviso.precio_clp is None
    assert aviso.banos is None


def test_consulta_sin_resultados_igual_queda_registrada(tmp_path: Path) -> None:
    cache = CacheAvisosDuckDB(tmp_path / "avisos.duckdb")
    cache.guardar("Alhué", TipoPropiedad.CASA, [], datetime(2026, 10, 1))
    assert cache.consultado_en("Alhué", TipoPropiedad.CASA) == datetime(2026, 10, 1)
