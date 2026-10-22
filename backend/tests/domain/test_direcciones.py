import pytest

from score.domain.direcciones import normalizar_calle, separar_calle_y_numero, separar_cruce


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [
        ("Av. Apoquindo", "apoquindo"),
        ("AVENIDA IRARRÁZAVAL", "irarrazaval"),
        ("Pasaje Los Aromos", "los aromos"),
        ("General Bustamante", "general bustamante"),
        ("Avenida Calle Larga", "larga"),
        ("Av. Manquehue Nte.", "manquehue norte"),
        ("Pdte. Riesco", "presidente riesco"),
        ("Gral. Bustamante", "general bustamante"),
    ],
)
def test_normalizar_calle(nombre: str, esperado: str) -> None:
    assert normalizar_calle(nombre) == esperado


@pytest.mark.parametrize(
    ("direccion", "esperado"),
    [
        ("Asturias 77, Las Condes, Metro Escuela Militar, Las Condes", ("asturias", 77)),
        ("Florencio García 1301, Ñuñoa, Parque Botánico, Ñuñoa", ("florencio garcia", 1301)),
        ("Av. Irarrázaval N° 3450, Ñuñoa", ("irarrazaval", 3450)),
        ("Calle 5 de Abril 120, Santiago", ("5 de abril", 120)),
        ("Alcántara 900 - 1200, Las Condes, Vaticano", ("alcantara", 900)),
        ("Augusto Leguía Nte. 70, Las Condes", ("augusto leguia norte", 70)),
    ],
)
def test_separar_calle_y_numero(direccion: str, esperado: tuple[str, int]) -> None:
    assert separar_calle_y_numero(direccion) == esperado


@pytest.mark.parametrize(
    "direccion", ["Estadio Nacional, Ñuñoa", "Sector Eduardo Castillo Velasco", ""]
)
def test_sin_numero(direccion: str) -> None:
    assert separar_calle_y_numero(direccion) is None


@pytest.mark.parametrize(
    ("direccion", "esperado"),
    [
        ("BENJAMIN CON ISIDORA GOYENECHEA, Barrio El Golf", ("benjamin", "isidora goyenechea")),
        (
            "Nuevo: Presidente Errázuriz / Burgos, Barrio El Golf",
            ("presidente errazuriz", "burgos"),
        ),
        ("Irarrázaval esq. Pedro de Valdivia", ("irarrazaval", "pedro de valdivia")),
    ],
)
def test_cruce(direccion: str, esperado: tuple[str, str]) -> None:
    assert separar_cruce(direccion) == esperado


def test_no_es_cruce() -> None:
    assert separar_cruce("Asturias 77, Las Condes") is None
    assert separar_cruce("Estadio Nacional, Ñuñoa") is None
