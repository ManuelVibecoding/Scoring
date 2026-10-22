import pytest

from score.pipeline.normalizacion import a_numero, normalizar_nombre


@pytest.mark.parametrize("nombre", ["Ñuñoa", "NUÑOA", "  ñuñoa ", "Nunoa"])
def test_normalizar_nombre(nombre: str) -> None:
    assert normalizar_nombre(nombre) == "nunoa"


def test_normalizar_nombre_compuesto() -> None:
    assert normalizar_nombre("Estación  Central") == "estacion central"
    assert normalizar_nombre("O'Higgins") == "ohiggins"


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [("-33,4448709", -33.4448709), (" 12 ", 12.0), ("*", None), ("", None), (None, None)],
)
def test_a_numero(texto: str | None, esperado: float | None) -> None:
    assert a_numero(texto) == esperado
