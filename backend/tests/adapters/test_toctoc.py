import json

import pytest

from score.adapters.toctoc import leer_avisos, slug_comuna, url_resultados
from score.domain.avisos import Operacion, TipoPropiedad

# Estructura observada en toctoc.com (octubre 2026), reducida a los campos que se usan.
AVISO = {
    "titulo": "Depto. Mariposa 2D - 3B",
    "comuna": "Ñuñoa",
    "urlFicha": "https://www.toctoc.com/arriendo/departamento/metropolitana/nunoa/b_2593",
    "hashId": "2593",
    "precios": [
        {"order": 0, "prefix": "UF", "value": "18"},
        {"order": 1, "prefix": "$", "value": "750.000"},
    ],
    "superficie": ["70"],
    "dormitorios": ["2"],
    "bannos": ["3"],
    "horasPublicado": 1695,
    "idProperty": 4311676,
    "latitud": -33.4515369,
    "longitud": -70.6129412,
}


def _pagina(*resultados: dict[str, object]) -> str:
    datos = {
        "props": {
            "pageProps": {"propiedades": {"total": len(resultados), "results": list(resultados)}}
        }
    }
    script = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(datos)}</script>'
    return f"<html>{script}</html>"


def test_lee_un_aviso_completo() -> None:
    [aviso] = leer_avisos(_pagina(AVISO), Operacion.ARRIENDO, TipoPropiedad.DEPARTAMENTO, "Ñuñoa")
    assert aviso.id == "4311676"
    assert aviso.precio_clp == 750_000
    assert aviso.precio_uf == 18
    assert aviso.superficie_m2 == 70
    assert (aviso.dormitorios, aviso.banos) == (2, 3)
    assert aviso.lat == pytest.approx(-33.4515369)
    assert aviso.clp_por_m2 == pytest.approx(750_000 / 70)


def test_uf_con_decimales_y_sin_precio_en_pesos() -> None:
    otro = {**AVISO, "precios": [{"prefix": "UF", "value": "18,5"}]}
    [aviso] = leer_avisos(_pagina(otro), Operacion.ARRIENDO, TipoPropiedad.DEPARTAMENTO, "Ñuñoa")
    assert aviso.precio_uf == 18.5
    assert aviso.precio_clp is None
    assert aviso.clp_por_m2 is None


def test_superficie_cero_es_sin_dato() -> None:
    sin_m2 = {**AVISO, "superficie": ["0"]}
    [aviso] = leer_avisos(_pagina(sin_m2), Operacion.ARRIENDO, TipoPropiedad.CASA, "Ñuñoa")
    assert aviso.superficie_m2 is None


def test_ignora_avisos_sin_coordenadas_y_paginas_sin_datos() -> None:
    sin_ubicacion = {**AVISO, "latitud": None}
    assert leer_avisos(_pagina(sin_ubicacion), Operacion.ARRIENDO, TipoPropiedad.CASA, "X") == []
    assert leer_avisos("<html>error</html>", Operacion.ARRIENDO, TipoPropiedad.CASA, "X") == []


@pytest.mark.parametrize(
    ("comuna", "slug"),
    [("Ñuñoa", "nunoa"), ("LAS CONDES", "las-condes"), ("Estación Central", "estacion-central")],
)
def test_slug_de_comuna(comuna: str, slug: str) -> None:
    assert slug_comuna(comuna) == slug


def test_url_de_resultados() -> None:
    url = url_resultados("Las Condes", Operacion.ARRIENDO, TipoPropiedad.CASA)
    assert url == "https://www.toctoc.com/arriendo/casa/metropolitana/las-condes"
