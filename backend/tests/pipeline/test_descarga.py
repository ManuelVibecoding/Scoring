from pathlib import Path

import httpx
import pytest

from score.pipeline.descarga import descargar_fuente, leer_manifiesto, nombre_desde_respuesta
from score.pipeline.fuentes import Fuente, Recurso


def _fuente(*recursos: Recurso) -> Fuente:
    return Fuente(
        id="prueba",
        nombre="Prueba",
        institucion="Test",
        pagina="https://ejemplo.cl",
        licencia="CC0",
        descripcion="",
        recursos=list(recursos),
    )


def _cliente(contenidos: dict[str, bytes], llamadas: list[str]) -> httpx.Client:
    def responder(peticion: httpx.Request) -> httpx.Response:
        llamadas.append(str(peticion.url))
        return httpx.Response(200, content=contenidos[str(peticion.url)])

    return httpx.Client(transport=httpx.MockTransport(responder))


def test_descarga_guarda_archivo_y_manifiesto(tmp_path: Path) -> None:
    llamadas: list[str] = []
    url = "https://ejemplo.cl/datos/base.csv"
    cliente = _cliente({url: b"a,b\n1,2\n"}, llamadas)

    [archivo] = descargar_fuente(_fuente(Recurso(url)), tmp_path, cliente)

    assert (tmp_path / "prueba" / "base.csv").read_bytes() == b"a,b\n1,2\n"
    assert archivo.bytes == 8
    assert leer_manifiesto(tmp_path / "prueba")[url].sha256 == archivo.sha256


def test_no_vuelve_a_descargar_si_ya_existe(tmp_path: Path) -> None:
    llamadas: list[str] = []
    url = "https://ejemplo.cl/x.zip"
    cliente = _cliente({url: b"zip"}, llamadas)
    fuente = _fuente(Recurso(url))

    descargar_fuente(fuente, tmp_path, cliente)
    descargar_fuente(fuente, tmp_path, cliente)
    descargar_fuente(fuente, tmp_path, cliente, forzar=True)

    assert llamadas == [url, url]


def test_fuente_con_resolver_no_duplica_ni_redescarga(tmp_path: Path) -> None:
    llamadas: list[str] = []
    contenidos = {"https://x.cl/r/1": b"a", "https://x.cl/r/2": b"a"}
    cliente = _cliente(contenidos, llamadas)
    fuente = Fuente(
        id="prueba",
        nombre="Prueba",
        institucion="Test",
        pagina="https://x.cl",
        licencia="CC0",
        descripcion="",
        resolver=lambda _: [Recurso(u, "pobreza.xlsx") for u in contenidos],
    )

    primera = descargar_fuente(fuente, tmp_path, cliente)
    segunda = descargar_fuente(fuente, tmp_path, cliente)

    assert [a.archivo for a in primera] == ["pobreza.xlsx"]
    assert segunda == primera
    assert len(llamadas) == 2


@pytest.mark.parametrize(
    ("cabecera", "esperado"),
    [
        (
            {"content-disposition": 'attachment; filename="Pobreza Comunal.xlsx"'},
            "Pobreza_Comunal.xlsx",
        ),
        (
            {"content-disposition": "attachment; filename*=UTF-8''%C3%91u%C3%B1oa.xlsx"},
            "Ñuñoa.xlsx",
        ),
        ({}, "Cartografía_R13.zip"),
    ],
)
def test_nombre_del_archivo(cabecera: dict[str, str], esperado: str) -> None:
    respuesta = httpx.Response(200, headers=cabecera)
    recurso = Recurso("https://ejemplo.cl/d/Cartograf%C3%ADa_R13.zip")
    assert nombre_desde_respuesta(respuesta, recurso) == esperado


def test_nombre_declarado_tiene_prioridad() -> None:
    respuesta = httpx.Response(200, headers={"content-disposition": 'filename="otro.pdf"'})
    assert nombre_desde_respuesta(respuesta, Recurso("https://x.cl/a", "icvu.pdf")) == "icvu.pdf"
