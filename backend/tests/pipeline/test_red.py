import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree

from score.pipeline.red import Modo, Red, costo_desde_fuentes, matriz_sin_duplicados

# Red de prueba: una línea de 5 nodos separados 100 m, de oeste a este.
#   0 — 1 — 2 — 3 — 4
X = np.array([0.0, 100.0, 200.0, 300.0, 400.0])
Y = np.zeros(5)


def _red(modo: Modo, dirigida: bool = False) -> Red:
    origen = [0, 1, 2, 3] if dirigida else [0, 1, 2, 3, 1, 2, 3, 4]
    destino = [1, 2, 3, 4] if dirigida else [1, 2, 3, 4, 0, 1, 2, 3]
    costo = np.full(len(origen), 100.0)
    grafo = csr_matrix((costo, (origen, destino)), shape=(5, 5))
    return Red(modo, X, Y, grafo, cKDTree(np.column_stack([X, Y])))


def test_multi_fuente_toma_la_mas_cercana_y_recuerda_cual() -> None:
    grafo = _red(Modo.PIE).grafo
    costos, origen = costo_desde_fuentes(grafo, np.array([0, 4]), np.array([0.0, 0.0]))
    assert costos == pytest.approx([0, 100, 200, 100, 0], abs=1e-3)
    assert list(origen[[0, 1, 3, 4]]) == [0, 0, 4, 4]


def test_costo_inicial_suma_el_tramo_hasta_la_red() -> None:
    red = _red(Modo.PIE)
    # Un supermercado 30 m al norte del nodo 2.
    alcance = red.costo_minimo(np.array([200.0]), np.array([30.0]))
    assert alcance.costo == pytest.approx([230, 130, 30, 130, 230])
    assert (alcance.punto == 0).all()


def test_identifica_el_punto_mas_cercano_de_varios() -> None:
    red = _red(Modo.PIE)
    # Tres farmacias: en los nodos 0 y 4, y otra a 50 m del nodo 4 (pierde contra la primera).
    alcance = red.costo_minimo(np.array([0.0, 400.0, 400.0]), np.array([0.0, 0.0, 50.0]))
    assert list(alcance.punto[[0, 1, 3, 4]]) == [0, 0, 1, 1]
    assert alcance.punto[2] in (0, 1)  # empate: 200 m a ambas


def test_puntos_lejos_de_la_red_se_ignoran() -> None:
    red = _red(Modo.PIE)
    alcance = red.costo_minimo(np.array([200.0]), np.array([1000.0]), distancia_maxima_ajuste=300)
    assert np.isinf(alcance.costo).all()
    assert (alcance.punto == -1).all()


def test_sentido_del_viaje_en_red_dirigida() -> None:
    # Calle de un sentido, de 0 hacia 4. El destino está en el nodo 2.
    red = _red(Modo.AUTO, dirigida=True)
    hacia = red.costo_minimo(np.array([200.0]), np.array([0.0]), hacia_los_puntos=True).costo
    desde = red.costo_minimo(np.array([200.0]), np.array([0.0]), hacia_los_puntos=False).costo
    # Ir hasta el nodo 2 solo es posible desde 0 y 1.
    assert np.isfinite(hacia[:3]).all() and np.isinf(hacia[3:]).all()
    # Salir desde el nodo 2 solo llega a 3 y 4.
    assert np.isinf(desde[:2]).all() and np.isfinite(desde[2:]).all()


def test_aristas_repetidas_conservan_el_minimo_en_vez_de_sumarse() -> None:
    m = matriz_sin_duplicados(
        np.array([0, 0, 1]), np.array([1, 1, 0]), np.array([50.0, 30.0, 40.0]), 2
    )
    assert m[0, 1] == 30.0
    assert m[1, 0] == 40.0
