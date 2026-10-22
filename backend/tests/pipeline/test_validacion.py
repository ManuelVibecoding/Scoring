import numpy as np
import pandas as pd
import pytest

from score.pipeline.validacion import limpiar_avisos, premio_de_ubicacion


def _avisos(**columnas: list[object]) -> pd.DataFrame:
    base: dict[str, list[object]] = {
        "precio_clp": [500_000.0],
        "superficie_m2": [50.0],
        "lat": [-33.45],
        "lon": [-70.60],
        "tipo": ["departamento"],
        "dormitorios": [2],
    }
    base.update(columnas)
    n = max(len(v) for v in base.values())
    return pd.DataFrame({k: v * n if len(v) == 1 else v for k, v in base.items()})


def test_limpiar_descarta_precios_y_superficies_absurdas() -> None:
    avisos = _avisos(
        precio_clp=[500_000.0, 1_000.0, 500_000.0, None],
        superficie_m2=[50.0, 50.0, 5.0, 50.0],
    )
    limpios = limpiar_avisos(avisos)
    assert len(limpios) == 1
    assert limpios["clp_m2"].iloc[0] == 10_000
    assert limpios["h3"].iloc[0].startswith("89")


def test_premio_descuenta_el_tamano() -> None:
    # Mismo barrio: los grandes cuestan menos por m². Sin efecto de ubicación, el premio ~0.
    superficie = np.array([40.0, 60.0, 80.0, 120.0])
    clp_m2 = 20_000 * superficie**-0.3
    avisos = _avisos(superficie_m2=list(superficie), precio_clp=list(clp_m2 * superficie))
    avisos["clp_m2"] = clp_m2
    assert premio_de_ubicacion(avisos).abs().max() == pytest.approx(0, abs=1e-9)


def test_premio_detecta_el_barrio_caro() -> None:
    avisos = _avisos(superficie_m2=[50.0, 50.0, 50.0, 50.0])
    avisos["clp_m2"] = [10_000.0, 10_000.0, 10_000.0, 20_000.0]
    premio = premio_de_ubicacion(avisos)
    assert premio.iloc[3] > 0 > premio.iloc[0]
