"""Redes de calles (a pie y en auto) y cálculo de distancias mínimas sobre ellas.

La red es un grafo disperso (scipy) cuyos nodos son los nodos de OSM. Para saber cuánto
se demora cada punto de la ciudad en llegar al supermercado más cercano, se corre un
único Dijkstra desde un nodo virtual conectado a todos los supermercados: así se obtiene
la distancia al más cercano para todos los nodos de una vez.
"""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import duckdb
import numpy as np
import numpy.typing as npt
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

Arreglo = npt.NDArray[np.float64]

# Proyección local equirectangular centrada en Santiago: error < 1% en toda la RM,
# suficiente para distancias de caminata y búsqueda de vecinos.
_LAT0 = -33.45
_M_POR_GRADO_LAT = 110_574.0
_M_POR_GRADO_LON = 111_320.0 * float(np.cos(np.radians(_LAT0)))

VELOCIDAD_PEATON_M_MIN = 80.0  # 4,8 km/h

# Velocidades medias supuestas en hora punta (km/h). Son una aproximación: no hay datos
# públicos de congestión por calle.
VELOCIDAD_AUTO_KMH: dict[str, float] = {
    "motorway": 70,
    "motorway_link": 40,
    "trunk": 50,
    "trunk_link": 35,
    "primary": 35,
    "primary_link": 30,
    "secondary": 30,
    "secondary_link": 25,
    "tertiary": 27,
    "tertiary_link": 25,
    "unclassified": 25,
    "residential": 22,
    "living_street": 12,
    "service": 12,
}
_NO_CAMINABLES = (
    "motorway",
    "motorway_link",
    "construction",
    "proposed",
    "platform",
    "raceway",
    "bus_guideway",
    "busway",
    "elevator",
    "abandoned",
)


class Modo(StrEnum):
    PIE = "pie"
    AUTO = "auto"


def proyectar(lat: Arreglo, lon: Arreglo) -> tuple[Arreglo, Arreglo]:
    """Grados a metros en la proyección local."""
    return np.asarray(lon) * _M_POR_GRADO_LON, np.asarray(lat) * _M_POR_GRADO_LAT


@dataclass(frozen=True)
class Red:
    """Grafo dirigido con costos en metros (a pie) o segundos (en auto)."""

    modo: Modo
    x: Arreglo
    y: Arreglo
    grafo: csr_matrix
    _arbol: cKDTree

    @property
    def n_nodos(self) -> int:
        return len(self.x)

    def ajustar(self, x: Arreglo, y: Arreglo) -> tuple[npt.NDArray[np.int64], Arreglo]:
        """Nodo de la red más cercano a cada punto y la distancia en línea recta (m)."""
        distancia, indice = self._arbol.query(np.column_stack([x, y]))
        return np.asarray(indice, dtype=np.int64), np.asarray(distancia, dtype=np.float64)

    def costo_de_acceso(self, metros: Arreglo) -> Arreglo:
        """Costo de recorrer el tramo entre un punto y su nodo (a pie o a 15 km/h)."""
        if self.modo is Modo.PIE:
            return metros
        return metros / (15 / 3.6)

    def costo_minimo(
        self,
        x: Arreglo,
        y: Arreglo,
        hacia_los_puntos: bool = True,
        distancia_maxima_ajuste: float = 300.0,
    ) -> "Alcance":
        """Costo desde cada nodo de la red hasta el más cercano de los puntos dados.

        Con `hacia_los_puntos=True` se mide el viaje nodo → punto (ir al supermercado);
        con False, punto → nodo (que llegue la ambulancia). En la red a pie da lo mismo.
        Los puntos a más de `distancia_maxima_ajuste` metros de la red se ignoran.
        """
        nodos, separacion = self.ajustar(x, y)
        validos = np.flatnonzero(separacion <= distancia_maxima_ajuste)
        if len(validos) == 0:
            return Alcance(np.full(self.n_nodos, np.inf), np.full(self.n_nodos, -1))
        grafo = self.grafo.T.tocsr() if hacia_los_puntos else self.grafo
        costo, nodo_origen = costo_desde_fuentes(
            grafo, nodos[validos], self.costo_de_acceso(separacion[validos])
        )
        # Qué punto corresponde a cada nodo de origen (si varios caen en el mismo nodo,
        # el de menor costo de acceso).
        orden = validos[np.argsort(-separacion[validos])]
        punto_de_nodo = np.full(self.n_nodos, -1, dtype=np.int64)
        punto_de_nodo[nodos[orden]] = orden
        punto = np.where(nodo_origen >= 0, punto_de_nodo[np.maximum(nodo_origen, 0)], -1)
        return Alcance(costo, punto)


@dataclass(frozen=True)
class Alcance:
    """Para cada nodo: costo al punto más cercano y el índice de ese punto (-1 si no hay)."""

    costo: Arreglo
    punto: npt.NDArray[np.int64]


def matriz_sin_duplicados(
    origen: npt.NDArray[np.int64], destino: npt.NDArray[np.int64], costo: Arreglo, n: int
) -> csr_matrix:
    """Matriz dispersa que conserva el costo mínimo cuando una arista se repite.

    scipy suma las entradas duplicadas; en una red eso alargaría tramos compartidos.
    """
    orden = np.lexsort((costo, destino, origen))
    o, d, c = origen[orden], destino[orden], costo[orden]
    primera = np.ones(len(o), dtype=bool)
    primera[1:] = (o[1:] != o[:-1]) | (d[1:] != d[:-1])
    return csr_matrix((c[primera], (o[primera], d[primera])), shape=(n, n))


def costo_desde_fuentes(
    grafo: csr_matrix, fuentes: npt.NDArray[np.int64], costo_inicial: Arreglo
) -> tuple[Arreglo, npt.NDArray[np.int64]]:
    """Dijkstra multi-fuente desde un nodo virtual unido a cada fuente con su costo inicial.

    Devuelve el costo mínimo a cada nodo y el nodo fuente desde el que se llegó (-1 si
    ninguno lo alcanza).
    """
    n = grafo.shape[0]
    virtual = n
    coo = grafo.tocoo()
    # Un costo 0 se perdería en la matriz dispersa: se usa un mínimo positivo.
    ampliado = matriz_sin_duplicados(
        np.concatenate([coo.row, np.full(len(fuentes), virtual)]).astype(np.int64),
        np.concatenate([coo.col, fuentes]).astype(np.int64),
        np.concatenate([coo.data, np.maximum(costo_inicial, 1e-6)]),
        n + 1,
    )
    distancias, predecesores = dijkstra(
        ampliado, directed=True, indices=virtual, return_predecessors=True
    )
    return distancias[:n], _origen(predecesores[:n], virtual)


def _origen(predecesores: npt.NDArray[np.int32], virtual: int) -> npt.NDArray[np.int64]:
    """Sigue los predecesores hasta la fuente, saltando de a potencias de dos."""
    indices = np.arange(len(predecesores))
    padre = predecesores.astype(np.int64)
    inalcanzable = padre < 0
    padre[(padre == virtual) | inalcanzable] = indices[(padre == virtual) | inalcanzable]
    while True:
        siguiente = padre[padre]
        if np.array_equal(siguiente, padre):
            break
        padre = siguiente
    return np.where(inalcanzable, -1, padre)


def _filtro_sql(modo: Modo) -> str:
    restringido = "COALESCE(acceso, '') IN ('private', 'no')"
    if modo is Modo.PIE:
        excluidos = ", ".join(f"'{h}'" for h in _NO_CAMINABLES)
        return (
            f"highway NOT IN ({excluidos}) AND COALESCE(foot, '') <> 'no' "
            f"AND (NOT {restringido} OR foot IN ('yes', 'designated'))"
        )
    incluidos = ", ".join(f"'{h}'" for h in VELOCIDAD_AUTO_KMH)
    return f"highway IN ({incluidos}) AND NOT {restringido}"


def construir_red(osm: Path, modo: Modo) -> Red:
    """Arma la red desde vias.parquet y nodos.parquet, conservando la componente principal."""
    tramos = (
        duckdb.connect()
        .execute(
            f"""
            WITH v AS (
                SELECT highway, oneway, cruce, refs FROM '{(osm / "vias.parquet").as_posix()}'
                WHERE {_filtro_sql(modo)}
            ),
            pares AS (
                SELECT highway, oneway, cruce, refs[u.i] AS a, refs[u.i + 1] AS b
                FROM v, UNNEST(range(1, len(refs))) AS u(i)
            )
            SELECT p.highway, p.oneway, p.cruce, p.a, p.b,
                   na.lat AS lat_a, na.lon AS lon_a, nb.lat AS lat_b, nb.lon AS lon_b
            FROM pares p
            JOIN '{(osm / "nodos.parquet").as_posix()}' na ON na.id = p.a
            JOIN '{(osm / "nodos.parquet").as_posix()}' nb ON nb.id = p.b
            """
        )
        .df()
    )
    ids, inverso = np.unique(np.concatenate([tramos["a"], tramos["b"]]), return_inverse=True)
    a, b = inverso[: len(tramos)], inverso[len(tramos) :]
    xa, ya = proyectar(tramos["lat_a"].to_numpy(), tramos["lon_a"].to_numpy())
    xb, yb = proyectar(tramos["lat_b"].to_numpy(), tramos["lon_b"].to_numpy())
    largo = np.hypot(xb - xa, yb - ya)

    x, y = np.empty(len(ids)), np.empty(len(ids))
    x[a], y[a], x[b], y[b] = xa, ya, xb, yb

    if modo is Modo.PIE:
        origen, destino, costo = np.concatenate([a, b]), np.concatenate([b, a]), np.tile(largo, 2)
    else:
        velocidad = tramos["highway"].map(VELOCIDAD_AUTO_KMH).to_numpy(dtype=float) / 3.6
        segundos = largo / velocidad
        sentido = tramos["oneway"].fillna("").to_numpy()
        unico = (
            np.isin(sentido, ["yes", "true", "1"])
            | (tramos["cruce"].fillna("").to_numpy() == "roundabout")
            | (tramos["highway"].to_numpy() == "motorway")
        )
        inverso_solo = sentido == "-1"
        ida = ~inverso_solo
        vuelta = ~unico
        origen = np.concatenate([a[ida], b[vuelta]])
        destino = np.concatenate([b[ida], a[vuelta]])
        costo = np.concatenate([segundos[ida], segundos[vuelta]])

    costo = np.maximum(costo, 1e-3)
    grafo = matriz_sin_duplicados(
        origen.astype(np.int64), destino.astype(np.int64), costo, len(ids)
    )
    return _componente_principal(modo, x, y, grafo)


def _componente_principal(modo: Modo, x: Arreglo, y: Arreglo, grafo: csr_matrix) -> Red:
    _, etiquetas = connected_components(grafo, directed=True, connection="strong")
    principal = np.bincount(etiquetas).argmax()
    conservar = np.flatnonzero(etiquetas == principal)
    sub = grafo[conservar][:, conservar].tocsr()
    return Red(modo, x[conservar], y[conservar], sub, cKDTree(np.column_stack([x, y])[conservar]))
