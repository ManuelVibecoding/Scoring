import pytest

from score.domain.avisos import Aviso, Operacion, TipoPropiedad
from score.domain.precios import distancia_m, resumir

LAT, LON = -33.45, -70.60
GRADO_100M = 0.0009


def _aviso(id_: str, metros_al_norte: float, precio: float, m2: float, dorm: int) -> Aviso:
    return Aviso(
        fuente="prueba",
        id=id_,
        operacion=Operacion.ARRIENDO,
        tipo=TipoPropiedad.DEPARTAMENTO,
        comuna="Ñuñoa",
        lat=LAT + metros_al_norte / 100 * GRADO_100M,
        lon=LON,
        precio_clp=precio,
        precio_uf=None,
        superficie_m2=m2,
        dormitorios=dorm,
        banos=1,
        horas_publicado=10,
        url="",
    )


def test_distancia_haversine() -> None:
    assert distancia_m(LAT, LON, LAT + GRADO_100M, LON) == pytest.approx(100, rel=0.01)


def test_resumen_solo_cuenta_lo_que_esta_dentro_del_radio() -> None:
    avisos = [
        _aviso("a", 100, 500_000, 50, 1),
        _aviso("b", 300, 600_000, 60, 2),
        _aviso("c", 500, 700_000, 70, 2),
        _aviso("lejos", 5000, 9_000_000, 100, 3),
    ]
    r = resumir(avisos, LAT, LON, radio_m=800)
    assert r.avisos == 3
    assert r.mediana_arriendo_clp == 600_000
    assert r.mediana_clp_m2 == 10_000
    assert r.mediana_por_dormitorios == {2: 650_000}  # 1 dormitorio tiene un solo aviso
    assert [e.aviso.id for e in r.ejemplos] == ["a", "b", "c"]


def test_resumen_vacio() -> None:
    r = resumir([], LAT, LON, radio_m=800)
    assert r.avisos == 0
    assert r.mediana_arriendo_clp is None
