import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix

from score.adapters.motor_cercanias import MedidaPrecalculada, MotorCercanias
from score.domain.geo import proyectar
from score.pipeline.cercanias import _puntos_de_parques
from score.pipeline.medidas import MEDIDAS
from score.pipeline.red import Modo

# ~0,0009° de latitud ≈ 100 m.
GRADO_100M = 0.0009
LAT0, LON0 = -33.45, -70.60


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


@pytest.fixture
def motor() -> MotorCercanias:
    # Red de tres nodos en línea, cada 100 m hacia el norte, en ambas redes.
    lats = np.array([LAT0, LAT0 + GRADO_100M, LAT0 + 2 * GRADO_100M])
    x, y = proyectar(lats, np.full(3, LON0))
    xy = np.column_stack([x, y]).astype(np.float32)
    medidas = {
        m.id: MedidaPrecalculada(
            minutos=np.array([2.0, 3.25, np.inf], dtype=np.float32),
            lugar=np.array([0, 0, -1], dtype=np.int32),
            nombres=np.array([f"{m.id} más cercano"], dtype=object),
        )
        for m in MEDIDAS
    }
    puntos = pd.DataFrame(
        {
            "categoria": ["paradero", "paradero", "colegio", "carcel"],
            "lat": [LAT0, LAT0 + 2 * GRADO_100M, LAT0, LAT0 + 30 * GRADO_100M],
            "lon": [LON0] * 4,
            "recorridos": [["506", "210"], ["210", "D09"], None, None],
            "salidas_hora": [30.0, 12.0, None, None],
        }
    )
    vias = pd.DataFrame({"lat": [LAT0 + 5 * GRADO_100M], "lon": [LON0]})
    unidos = csr_matrix(([100.0, 100.0, 100.0, 100.0], ([0, 1, 1, 2], [1, 0, 2, 1])), shape=(3, 3))
    return MotorCercanias({Modo.PIE: xy, Modo.AUTO: xy}, medidas, puntos, vias, unidos)


def test_evalua_minutos_y_lugar_en_el_punto_exacto(motor: MotorCercanias) -> None:
    fila = motor.evaluar([LAT0], [LON0]).iloc[0]
    assert fila["min_metro"] == pytest.approx(2.0, abs=0.05)
    assert fila["cerca_metro"] == "metro más cercano"
    # El nodo 2 no alcanza ningún lugar: queda sin dato y sin nombre.
    lejano = motor.evaluar([LAT0 + 2 * GRADO_100M], [LON0]).iloc[0]
    assert np.isnan(lejano["min_metro"])
    assert lejano["cerca_metro"] is None


def test_suma_el_tramo_entre_el_punto_y_la_red(motor: MotorCercanias) -> None:
    # 40 m al este del nodo 0: medio minuto más a pie.
    fila = motor.evaluar([LAT0], [LON0 + 40 / 92_850]).iloc[0]
    assert fila["min_metro"] == pytest.approx(2.5, abs=0.05)


def test_conteos_buses_y_distancias(motor: MotorCercanias) -> None:
    fila = motor.evaluar([LAT0], [LON0]).iloc[0]
    assert fila["n800_paradero"] == 2
    assert fila["n800_colegio"] == 1
    assert fila["recorridos_400m"] == 3  # 506, 210 y D09
    assert fila["buses_hora_max_400m"] == 30.0
    assert fila["m_via_rapida"] == pytest.approx(500, rel=0.02)
    assert fila["m_desamenidad"] == pytest.approx(3000, rel=0.02)


def test_isocrona_crece_con_los_minutos(motor: MotorCercanias) -> None:
    geo = motor.isocrona(LAT0, LON0, bandas=(1, 5))
    assert [f["properties"]["minutos"] for f in geo["features"]] == [5, 1]
    assert all(f["geometry"]["type"] in ("Polygon", "MultiPolygon") for f in geo["features"])
