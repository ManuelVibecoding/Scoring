from score.domain.veredicto import redactar


def test_con_fortalezas_y_debilidades() -> None:
    texto = redactar("B", ["Transporte público", "Servicios cercanos"], ["Seguridad"])
    assert texto == (
        "Muy buena ubicación. Destaca en transporte público y servicios cercanos; "
        "lo más débil es seguridad."
    )


def test_solo_fortalezas() -> None:
    assert redactar("A", ["Áreas verdes"], []) == "Excelente ubicación. Destaca en áreas verdes."


def test_solo_debilidades_en_plural() -> None:
    texto = redactar("D", [], ["Transporte público", "Conectividad vial"])
    assert (
        texto
        == "Ubicación con limitaciones. Lo más débil son transporte público y conectividad vial."
    )


def test_sin_marcas_y_sin_datos() -> None:
    assert redactar("C", [], []) == "Ubicación correcta. Sin fortalezas ni debilidades marcadas."
    assert redactar(None, [], []) == "Sin datos suficientes para evaluar este punto."
