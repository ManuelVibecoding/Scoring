"""Pruebas de la API con dobles en memoria (sin red ni archivos)."""

from datetime import datetime
from typing import Any

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from score.domain.avisos import Aviso, Operacion, TipoPropiedad
from score.domain.modelo import MODELO
from score.entrypoints.api import Dependencias, crear_app

H3 = "89b2c5ba00fffff"


class RepositorioFalso:
    def __init__(self) -> None:
        fila = {
            "lat": -33.45,
            "lon": -70.60,
            "cut": 13120,
            "comuna": "ÑUÑOA",
            "puntaje": 82.0,
            "letra": "A",
            "percentil_rm": 95.0,
            "percentil_comuna": 70.0,
            "personas": 1200.0,
            "version_modelo": "v1",
            "min_metro": 4.5,
            "cerca_metro": "Chile España",
            **{d.id: 80.0 for d in MODELO},
        }
        fila["seguridad"] = 40.0
        self.tabla = pd.DataFrame([fila], index=pd.Index([H3], name="h3"))

    def hexagono_mas_cercano(self, lat: float, lon: float) -> tuple[pd.Series, float] | None:
        return (self.tabla.iloc[0], 0.0) if lat > -34 else None

    def comuna(self, cut: int) -> pd.Series | None:
        return pd.Series({"poblacion": 241_467, "icvu_nivel": "Alto"})

    def medianas(self) -> dict[str, float]:
        return {d.id: 60.0 for d in MODELO}

    def capa(self) -> pd.DataFrame:
        return self.tabla[["puntaje", "letra", *(d.id for d in MODELO)]]

    def contorno_comunas(self) -> dict[str, Any]:
        return {"type": "FeatureCollection", "features": []}


class CacheFalsa:
    def __init__(self) -> None:
        self.guardados: list[str] = []
        self.avisos: list[Aviso] = []

    def consultado_en(self, comuna: str, tipo: TipoPropiedad) -> datetime | None:
        return None

    def guardar(
        self, comuna: str, tipo: TipoPropiedad, avisos: list[Aviso], momento: datetime
    ) -> None:
        self.guardados.append(f"{comuna}/{tipo}")
        self.avisos.extend(avisos)

    def en_rectangulo(self, *_: float) -> list[Aviso]:
        return self.avisos


class PortalFalso:
    nombre = "falso"

    def avisos_de_comuna(
        self, comuna: str, operacion: Operacion, tipo: TipoPropiedad
    ) -> list[Aviso]:
        return [
            Aviso(
                "falso",
                f"{tipo}-1",
                operacion,
                tipo,
                comuna,
                -33.45,
                -70.60,
                600_000.0,
                None,
                60.0,
                2,
                1,
                5,
                "",
            )
        ]


class GeocodificadorFalso:
    def buscar(self, texto: str) -> list[dict[str, Any]]:
        return [{"nombre": "Plaza Ñuñoa", "lat": -33.456, "lon": -70.597}]

    def direccion(self, lat: float, lon: float) -> str | None:
        return "Irarrázaval 3450"


@pytest.fixture
def cliente() -> TestClient:
    dep = Dependencias(RepositorioFalso(), CacheFalsa(), PortalFalso(), GeocodificadorFalso())
    return TestClient(crear_app(dep))


def test_punto_devuelve_ficha_completa(cliente: TestClient) -> None:
    r = cliente.get("/api/punto", params={"lat": -33.45, "lon": -70.60})
    assert r.status_code == 200
    ficha = r.json()
    assert ficha["letra"] == "A"
    assert ficha["comuna"] == "ÑUÑOA"
    assert "seguridad" in ficha["veredicto"].lower()
    assert ficha["cercanias"][0] == {
        "id": "metro",
        "etiqueta": "Metro",
        "modo": "pie",
        "minutos": 4.5,
        "lugar": "Chile España",
    }
    assert len(ficha["dimensiones"]) == len(MODELO)


def test_punto_fuera_de_la_rm_es_rechazado(cliente: TestClient) -> None:
    assert cliente.get("/api/punto", params={"lat": -20.0, "lon": -70.6}).status_code == 422


def test_precios_consulta_el_portal_cuando_no_hay_cache(cliente: TestClient) -> None:
    r = cliente.get("/api/precios", params={"lat": -33.45, "lon": -70.60})
    assert r.status_code == 200
    datos = r.json()
    assert datos["avisos"] == 2
    assert datos["mediana_arriendo_clp"] == 600_000
    assert datos["fuente"] == "falso"


def test_capa_columnar(cliente: TestClient) -> None:
    capa = cliente.get("/api/capa").json()
    assert capa["h3"] == [H3]
    assert capa["puntaje"] == [82.0]


def test_buscar_y_direccion(cliente: TestClient) -> None:
    assert cliente.get("/api/buscar", params={"q": "plaza ñuñoa"}).json()[0]["lat"] == -33.456
    r = cliente.get("/api/direccion", params={"lat": -33.45, "lon": -70.60})
    assert r.json() == {"direccion": "Irarrázaval 3450"}
