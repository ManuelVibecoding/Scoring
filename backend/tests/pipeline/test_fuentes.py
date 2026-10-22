import pytest

from score.pipeline.fuentes import FUENTES, buscar_fuente


def test_ids_unicos() -> None:
    ids = [f.id for f in FUENTES]
    assert len(ids) == len(set(ids))


def test_toda_fuente_tiene_recursos_o_resolver() -> None:
    for fuente in FUENTES:
        assert fuente.recursos or fuente.resolver, fuente.id


def test_buscar_fuente_inexistente_lista_disponibles() -> None:
    with pytest.raises(KeyError, match="censo2024_manzana_entidad"):
        buscar_fuente("no-existe")
