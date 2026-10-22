import numpy as np
import pandas as pd

from score.pipeline.cercanias import _oferta_buses, _puntos_de_parques

# ~0,0009° de latitud ≈ 100 m.
GRADO_100M = 0.0009


def test_parques_se_expanden_a_los_puntos_de_su_borde() -> None:
    parques = pd.DataFrame(
        {
            "categoria": ["plaza", "parque"],
            "nombre": ["Plaza Ñuñoa", "Parque Bustamante"],
            "lats": [[-33.45, -33.451], [-33.44, -33.441, -33.442]],
            "lons": [[-70.59, -70.591], [-70.63, -70.631, -70.632]],
        }
    )
    puntos = _puntos_de_parques(parques, ("parque",))
    assert list(puntos["nombre"]) == ["Parque Bustamante"] * 3
    assert len(_puntos_de_parques(parques, ("plaza", "parque"))) == 5


def test_oferta_de_buses_cuenta_recorridos_distintos_a_400m() -> None:
    hexagonos = pd.DataFrame({"lat": [-33.45], "lon": [-70.60]}, index=["h1"])
    puntos = pd.DataFrame(
        {
            "categoria": ["paradero", "paradero", "paradero"],
            "lat": [-33.45, -33.45 + 2 * GRADO_100M, -33.45 + 10 * GRADO_100M],
            "lon": [-70.60, -70.60, -70.60],
            "recorridos": [["506", "210"], ["210", "D09"], ["401"]],
            "salidas_hora": [30.0, 12.0, 50.0],
        }
    )
    oferta = _oferta_buses(hexagonos, puntos).loc["h1"]
    # El paradero a ~1 km queda fuera: 3 recorridos distintos y el más servido tiene 30/h.
    assert oferta["recorridos_400m"] == 3
    assert oferta["buses_hora_max_400m"] == 30.0


def test_sin_paraderos_cerca_la_oferta_es_cero() -> None:
    hexagonos = pd.DataFrame({"lat": [-33.0], "lon": [-71.0]}, index=["h1"])
    puntos = pd.DataFrame(
        {
            "categoria": ["paradero"],
            "lat": [-33.45],
            "lon": [-70.60],
            "recorridos": [np.array(["506"])],
            "salidas_hora": [10.0],
        }
    )
    oferta = _oferta_buses(hexagonos, puntos).loc["h1"]
    assert oferta["recorridos_400m"] == 0
    assert oferta["buses_hora_max_400m"] == 0.0
