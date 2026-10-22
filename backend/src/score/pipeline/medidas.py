"""Qué se mide alrededor de cada lugar: categorías, modo de viaje y radios de conteo.

Lo usan el pipeline (para precalcular) y el motor de cercanías de la app (para responder
en cualquier punto), así ambos miden exactamente lo mismo.
"""

from dataclasses import dataclass

from score.pipeline.red import Modo


@dataclass(frozen=True)
class Medida:
    id: str
    categorias: tuple[str, ...]
    modo: Modo
    hacia_los_puntos: bool = True


# A pie: lo que se usa en la vida diaria. En auto: emergencias y conectividad vial.
MEDIDAS: tuple[Medida, ...] = (
    Medida("metro", ("metro",), Modo.PIE),
    Medida("tren", ("tren",), Modo.PIE),
    Medida("paradero", ("paradero",), Modo.PIE),
    Medida("supermercado", ("supermercado",), Modo.PIE),
    Medida("farmacia", ("farmacia",), Modo.PIE),
    Medida("banco", ("banco",), Modo.PIE),
    Medida("cajero", ("cajero", "banco"), Modo.PIE),
    Medida("colegio", ("colegio",), Modo.PIE),
    Medida("jardin", ("jardin",), Modo.PIE),
    Medida("cesfam", ("cesfam",), Modo.PIE),
    Medida("feria", ("feria",), Modo.PIE),
    Medida("mall", ("mall",), Modo.PIE),
    Medida("gimnasio", ("gimnasio",), Modo.PIE),
    Medida("plaza", ("plaza", "parque"), Modo.PIE),
    Medida("parque", ("parque",), Modo.PIE),
    Medida("urgencia", ("urgencia",), Modo.AUTO),
    Medida("hospital_clinica", ("hospital_clinica",), Modo.AUTO),
    Medida("bomberos", ("bomberos",), Modo.AUTO, hacia_los_puntos=False),
    Medida("policia", ("policia",), Modo.AUTO, hacia_los_puntos=False),
    Medida("acceso_autopista", ("acceso_autopista",), Modo.AUTO),
    Medida("centro_empleo", ("centro_empleo",), Modo.AUTO),
)

# Distancia en línea recta (m) a lo que molesta por estar cerca, no por tener que ir.
DESAMENIDADES: tuple[str, ...] = ("carcel", "vertedero", "planta_tratamiento")

CONTEOS_800M: dict[str, tuple[str, ...]] = {
    "colegio": ("colegio",),
    "jardin": ("jardin",),
    "supermercado": ("supermercado",),
    "farmacia": ("farmacia",),
    "paradero": ("paradero",),
    "comercio_barrio": ("restaurante", "cafe", "feria", "gimnasio"),
}
RADIO_CONTEO_M = 800.0
RADIO_BUSES_M = 400.0
# Más allá de esto el lugar se considera "no accesible".
MINUTOS_MAXIMOS = 120.0
