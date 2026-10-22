import pandas as pd
import pytest

from score.adapters.geocodificador_local import GeocodificadorLocal
from score.domain.direcciones import Precision

LAS_CONDES, LA_FLORIDA = 13114, 13110


@pytest.fixture
def geo() -> GeocodificadorLocal:
    direcciones = pd.DataFrame(
        {
            "calle": ["asturias", "asturias", "asturias", "asturias"],
            "numero": [10, 50, 90, 8176],
            "cut": [LAS_CONDES, LAS_CONDES, LAS_CONDES, LA_FLORIDA],
            "lat": [-33.4100, -33.4120, -33.4140, -33.5296],
            "lon": [-70.5800, -70.5800, -70.5800, -70.5964],
        }
    )
    # Isidora Goyenechea corre de este a oeste; Benjamín la cruza de norte a sur.
    calles = pd.DataFrame(
        {
            "calle": ["isidora goyenechea"] * 3 + ["benjamin"] * 3,
            "cut": [LAS_CONDES] * 6,
            "lat": [-33.4150, -33.4150, -33.4150, -33.4140, -33.4150, -33.4160],
            "lon": [-70.6000, -70.6010, -70.6020, -70.6010, -70.6010, -70.6010],
        }
    )
    return GeocodificadorLocal(direcciones, calles)


def test_numero_exacto(geo: GeocodificadorLocal) -> None:
    u = geo.ubicar("Asturias 50, Las Condes, Metro Escuela Militar", LAS_CONDES)
    assert u is not None
    assert (u.lat, u.precision) == (-33.4120, Precision.EXACTA)


def test_interpola_entre_numeros_conocidos(geo: GeocodificadorLocal) -> None:
    u = geo.ubicar("Av. Asturias 70", LAS_CONDES)
    assert u is not None
    assert u.precision is Precision.INTERPOLADA
    assert u.lat == pytest.approx(-33.4130)


def test_misma_calle_en_otra_comuna_no_se_confunde(geo: GeocodificadorLocal) -> None:
    u = geo.ubicar("Asturias 8176", LA_FLORIDA)
    assert u is not None and u.lat == pytest.approx(-33.5296)
    assert geo.ubicar("Asturias 8176", LAS_CONDES) is None


def test_sin_numeros_conocidos_usa_la_calle(geo: GeocodificadorLocal) -> None:
    u = geo.ubicar("Isidora Goyenechea 3000", LAS_CONDES)
    assert u is not None
    assert u.precision is Precision.CALLE


def test_cruce_de_calles(geo: GeocodificadorLocal) -> None:
    u = geo.ubicar("BENJAMIN CON ISIDORA GOYENECHEA, Barrio El Golf", LAS_CONDES)
    assert u is not None
    assert u.precision is Precision.INTERPOLADA
    assert (u.lat, u.lon) == pytest.approx((-33.4150, -70.6010))


def test_calles_que_no_se_cruzan(geo: GeocodificadorLocal) -> None:
    assert geo.ubicar("Asturias con Isidora Goyenechea", LAS_CONDES) is None


def test_sin_numero_no_ubica(geo: GeocodificadorLocal) -> None:
    assert geo.ubicar("Estadio Nacional, Ñuñoa", 13120) is None
