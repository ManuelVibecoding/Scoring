import json

from score.adapters.portal_inmobiliario import a_aviso, leer_tarjetas, slug_comuna, url_pagina
from score.domain.avisos import Operacion, TipoPropiedad
from score.domain.direcciones import Precision


def _tarjeta(id_: str, valor: float, moneda: str, direccion: str) -> dict[str, object]:
    return {
        "metadata": {"id": id_, "url": f"portalinmobiliario.com/{id_}-depto-_JM"},
        "components": [
            {"type": "price", "price": {"current_price": {"value": valor, "currency": moneda}}},
            {
                "type": "attributes_list",
                "attributes_list": {"texts": ["2 dormitorios", "1 baño", "54 - 72 m² útiles"]},
            },
            {"type": "location", "location": {"text": direccion}},
        ],
    }


def _ubicar(direccion: str) -> tuple[float, float, Precision] | None:
    return (
        (-33.41, -70.58, Precision.EXACTA) if direccion[0].isalpha() and "77" in direccion else None
    )


def test_lee_tarjetas_sin_repetir_aunque_aparezcan_dos_veces() -> None:
    t = _tarjeta("MLC1", 800_000, "CLP", "Asturias 77, Las Condes")
    texto = json.dumps(t)
    html = f'<script>{{"a":{{"polycard":{texto}}},"b":{{"polycard":{texto}}}}}</script>'
    assert [x["metadata"]["id"] for x in leer_tarjetas(html)] == ["MLC1"]


def test_texto_con_llaves_no_rompe_la_lectura() -> None:
    t = _tarjeta("MLC2", 800_000, "CLP", "Calle {rara} 77, Ñuñoa")
    html = f'"polycard":{json.dumps(t)}'
    assert len(leer_tarjetas(html)) == 1


def test_convierte_uf_a_pesos_y_lee_atributos() -> None:
    t = _tarjeta("MLC3", 20, "CLF", "Asturias 77, Las Condes")
    aviso = a_aviso(
        t, Operacion.ARRIENDO, TipoPropiedad.DEPARTAMENTO, "Las Condes", _ubicar, 40_000
    )
    assert aviso is not None
    assert aviso.precio_clp == 800_000
    assert aviso.precio_uf == 20
    assert (aviso.superficie_m2, aviso.dormitorios, aviso.banos) == (54, 2, 1)
    assert aviso.url == "https://portalinmobiliario.com/MLC3-depto-_JM"


def test_sin_ubicacion_se_descarta() -> None:
    t = _tarjeta("MLC4", 800_000, "CLP", "Estadio Nacional, Ñuñoa")
    assert a_aviso(t, Operacion.ARRIENDO, TipoPropiedad.CASA, "Ñuñoa", _ubicar, 40_000) is None


def test_urls() -> None:
    assert slug_comuna("Ñuñoa") == "nunoa-metropolitana"
    assert url_pagina("Las Condes", Operacion.ARRIENDO, TipoPropiedad.CASA, 2).endswith(
        "/arriendo/casa/las-condes-metropolitana/_Desde_97"
    )
