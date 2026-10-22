"""Pruebas de la API con dobles en memoria (sin red ni archivos)."""

from datetime import datetime
from typing import Any, ClassVar

import pandas as pd
import pytest
import shapely
from fastapi.testclient import TestClient
from shapely.geometry.base import BaseGeometry

from score.domain.avisos import Aviso, Operacion, TipoPropiedad
from score.domain.modelo import MODELO
from score.entrypoints.api import Dependencias, crear_app

H3 = "89b2c5ba00fffff"
LAT, LON = -33.45, -70.60


def _aviso(id_: str, tipo: TipoPropiedad, precio: float) -> Aviso:
    return Aviso(
        "falso", id_, Operacion.ARRIENDO, tipo, "Ñuñoa", LAT, LON, precio, None, 60.0, 2, 1, 5, ""
    )


class RepositorioFalso:
    def __init__(self) -> None:
        fila = {
            "lat": LAT,
            "lon": LON,
            "cut": 13120,
            "comuna": "ÑUÑOA",
            "puntaje": 82.0,
            "letra": "A",
            "percentil_rm": 95.0,
            "percentil_comuna": 70.0,
            "personas": 1200.0,
            "hogares": 400.0,
            "viviendas": 420.0,
            "version_modelo": "v1",
            "min_metro": 4.5,
            "cerca_metro": "Chile España",
            **{d.id: 80.0 for d in MODELO},
        }
        fila["seguridad"] = 40.0
        self._tabla = pd.DataFrame([fila], index=pd.Index([H3], name="h3"))
        self._lugares = pd.DataFrame(
            {
                "categoria": ["metro", "colegio"],
                "nombre": ["Chile España", None],
                "lat": [LAT] * 2,
                "lon": [LON] * 2,
            }
        )

    def hexagono_mas_cercano(self, lat: float, lon: float) -> tuple[pd.Series, float] | None:
        return (self._tabla.iloc[0], 0.0) if lat > -34 else None

    def comuna(self, cut: int) -> pd.Series | None:
        return pd.Series({"poblacion": 241_467, "icvu_nivel": "Alto"})

    def medianas(self) -> dict[str, float]:
        return {d.id: 60.0 for d in MODELO}

    def puntuar_en_contexto(self, fila: pd.Series) -> pd.Series:
        return pd.Series(
            {"puntaje": 90.0, "letra": "A", "percentil_rm": 99, "percentil_comuna": 90}
        )

    def capa(self) -> pd.DataFrame:
        return self._tabla[["puntaje", "letra", *(d.id for d in MODELO)]]

    def tabla(self) -> pd.DataFrame:
        return self._tabla

    def hexagonos_en(self, zona: BaseGeometry) -> pd.DataFrame:
        dentro = shapely.contains_xy(zona, self._tabla["lon"], self._tabla["lat"])
        return self._tabla[dentro]

    def lugares(self, categorias: list[str]) -> pd.DataFrame:
        return self._lugares[self._lugares["categoria"].isin(categorias)]

    def contar_lugares_en(self, zona: BaseGeometry) -> dict[str, int]:
        return {"metro": 1, "colegio": 1}

    def contorno_comunas(self) -> dict[str, Any]:
        return {"type": "FeatureCollection", "features": []}


class CacheFalsa:
    def __init__(self) -> None:
        self.guardados: list[str] = []
        self.avisos: list[Aviso] = []

    def consultado_en(self, fuente: str, comuna: str, tipo: TipoPropiedad) -> datetime | None:
        return None

    def guardar(
        self,
        fuente: str,
        comuna: str,
        tipo: TipoPropiedad,
        avisos: list[Aviso],
        momento: datetime,
    ) -> None:
        self.guardados.append(f"{fuente}/{comuna}/{tipo}")
        self.avisos.extend(avisos)

    def todos(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "fuente": "falso",
                    "id": "1",
                    "tipo": "casa",
                    "lat": LAT,
                    "lon": LON,
                    "precio_clp": 1e6,
                }
            ]
        )

    def en_rectangulo(self, *_: float) -> list[Aviso]:
        return self.avisos


class PortalFalso:
    nombre = "falso"

    def avisos_de_comuna(
        self, comuna: str, operacion: Operacion, tipo: TipoPropiedad
    ) -> list[Aviso]:
        return [_aviso(f"{tipo}-1", tipo, 600_000.0)]


class GeocodificadorFalso:
    def buscar(self, texto: str) -> list[dict[str, Any]]:
        return [{"nombre": "Plaza Ñuñoa", "lat": -33.456, "lon": -70.597}]

    def direccion(self, lat: float, lon: float) -> str | None:
        return "Irarrázaval 3450"


class MotorFalso:
    def evaluar(self, lat: Any, lon: Any) -> pd.DataFrame:
        return pd.DataFrame([{"min_metro": 2.0, "cerca_metro": "Ñuble"}])

    def isocrona(self, lat: float, lon: float, bandas: tuple[int, ...]) -> dict[str, Any]:
        return {
            "type": "FeatureCollection",
            "features": [{"properties": {"minutos": b}} for b in bandas],
        }


class SuperficiesFalsas:
    esquinas: ClassVar[list[list[float]]] = [
        [-71.0, -33.0],
        [-70.0, -33.0],
        [-70.0, -34.0],
        [-71.0, -34.0],
    ]

    def png(self, variable: str) -> bytes:
        return b"\x89PNG-" + variable.encode()


def _cliente(con_motor: bool = False) -> TestClient:
    dep = Dependencias(
        RepositorioFalso(),
        CacheFalsa(),
        [PortalFalso()],
        GeocodificadorFalso(),
        MotorFalso() if con_motor else None,
        SuperficiesFalsas(),
    )
    return TestClient(crear_app(dep))


@pytest.fixture
def cliente() -> TestClient:
    return _cliente()


def test_punto_devuelve_ficha_completa(cliente: TestClient) -> None:
    r = cliente.get("/api/punto", params={"lat": LAT, "lon": LON})
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


def test_con_motor_el_punto_se_evalua_en_su_ubicacion_exacta() -> None:
    ficha = _cliente(con_motor=True).get("/api/punto", params={"lat": LAT, "lon": LON}).json()
    assert ficha["cercanias"][0]["minutos"] == 2.0
    assert ficha["cercanias"][0]["lugar"] == "Ñuble"
    assert ficha["puntaje"] == 90.0


def test_punto_fuera_de_la_rm_es_rechazado(cliente: TestClient) -> None:
    assert cliente.get("/api/punto", params={"lat": -20.0, "lon": -70.6}).status_code == 422


def test_precios_consulta_el_portal_cuando_no_hay_cache(cliente: TestClient) -> None:
    r = cliente.get("/api/precios", params={"lat": LAT, "lon": LON})
    assert r.status_code == 200
    datos = r.json()
    assert datos["avisos"] == 2
    assert datos["mediana_arriendo_clp"] == 600_000
    assert datos["fuentes"] == ["falso"]


def test_zona_resume_hexagonos_lugares_y_precios(cliente: TestClient) -> None:
    cliente.get("/api/precios", params={"lat": LAT, "lon": LON})  # llena la caché falsa
    cuadrado = {
        "type": "Polygon",
        "coordinates": [
            [
                [-70.61, -33.46],
                [-70.59, -33.46],
                [-70.59, -33.44],
                [-70.61, -33.44],
                [-70.61, -33.46],
            ]
        ],
    }
    r = cliente.post("/api/zona", json={"geometria": cuadrado})
    assert r.status_code == 200
    informe = r.json()
    assert informe["resumen"]["puntaje"] == 82.0
    assert informe["resumen"]["personas"] == 1200
    assert informe["area_km2"] == pytest.approx(4.1, rel=0.05)
    assert {"id": "metro", "etiqueta": "Estaciones de Metro", "cantidad": 1} in informe["lugares"]
    assert informe["precios"]["avisos"] == 2


def test_zona_invalida(cliente: TestClient) -> None:
    r = cliente.post("/api/zona", json={"geometria": {"type": "Point", "coordinates": [LON, LAT]}})
    assert r.status_code == 422


def test_lugares_y_avisos_como_geojson(cliente: TestClient) -> None:
    lugares = cliente.get("/api/lugares", params={"categorias": "metro,inventada"}).json()
    assert [f["properties"]["nombre"] for f in lugares["features"]] == ["Chile España"]
    assert lugares["features"][0]["geometry"]["coordinates"] == [LON, LAT]
    avisos = cliente.get("/api/avisos").json()
    assert avisos["features"][0]["properties"]["precio_clp"] == 1e6


def test_superficie_e_isocrona() -> None:
    cliente = _cliente(con_motor=True)
    assert cliente.get("/api/superficie").json()["variables"][0] == "puntaje"
    r = cliente.get("/api/superficie/transporte.png")
    assert r.headers["content-type"] == "image/png"
    assert r.content.endswith(b"transporte")
    assert cliente.get("/api/superficie/inventada.png").status_code == 404
    iso = cliente.get("/api/isocrona", params={"lat": LAT, "lon": LON}).json()
    assert [f["properties"]["minutos"] for f in iso["features"]] == [5, 10, 15]


def test_capa_columnar(cliente: TestClient) -> None:
    capa = cliente.get("/api/capa").json()
    assert capa["h3"] == [H3]
    assert capa["puntaje"] == [82.0]


def test_buscar_y_direccion(cliente: TestClient) -> None:
    assert cliente.get("/api/buscar", params={"q": "plaza ñuñoa"}).json()[0]["lat"] == -33.456
    r = cliente.get("/api/direccion", params={"lat": LAT, "lon": LON})
    assert r.json() == {"direccion": "Irarrázaval 3450"}
