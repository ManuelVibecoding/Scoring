import pandas as pd
import pytest

from score.pipeline.comunas import delitos, niveles_icvu


def test_niveles_icvu_lee_filas_de_la_tabla() -> None:
    texto = "\n".join(
        [
            "Cambio nivel Comunas Conectividad y Movilidad ...",
            "Mejoran Huechuraba ↑ ↓ ↑ = ↑ = Medio alto Alto",
            "Peñalolén ↓ = ↑ = = ↑ Medio bajo Medio alto",
            "Mantienen Las Condes = = = = = = Alto Alto",
            "P. Aguirre Cerda ↑ = = = ↑ = Bajo Bajo",
            "Texto que no es parte de la tabla",
        ]
    )
    assert niveles_icvu(texto) == {
        "Huechuraba": "Alto",
        "Peñalolén": "Medio alto",
        "Las Condes": "Alto",
        "P. Aguirre Cerda": "Bajo",
    }


def _casos(anio: int, meses: int, delito: str, n: float, cut: float = 13101.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cut_comuna": cut,
            "fecha": [f"{anio}-{m:02d}-01" for m in range(1, meses + 1)],
            "delito": delito,
            "delito_n": n,
        }
    )


def test_delitos_usa_ultimo_anio_completo_y_calcula_tasas() -> None:
    casos = pd.concat(
        [
            _casos(2024, 12, "Hurtos", 10),  # 120 en 2024
            _casos(2025, 12, "Hurtos", 15),  # 180 en 2025
            _casos(2025, 12, "Homicidios", 1),  # 12 en 2025
            _casos(2026, 3, "Hurtos", 99),  # año incompleto: se ignora
            _casos(2025, 12, "Hurtos", 5, cut=5101.0),  # fuera de la RM
        ]
    )
    poblacion = pd.Series({13101: 200_000})

    r = delitos(casos, poblacion).loc[13101]

    assert r["anio_delitos"] == 2025
    assert r["tasa_dmcs_100k"] == pytest.approx((180 + 12) / 2)
    assert r["tasa_delitos_violentos_100k"] == pytest.approx(12 / 2)
    assert r["homicidios"] == 12
    assert r["variacion_dmcs_anual"] == pytest.approx(192 / 120 - 1)
