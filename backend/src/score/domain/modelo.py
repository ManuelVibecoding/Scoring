"""Configuración del modelo de puntaje v1.1: dimensiones, indicadores, umbrales y pesos.

Cambiar un peso o un umbral es cambiar este archivo; el resto del código no se toca.
Los umbrales en minutos se eligieron con criterios de "ciudad de 15 minutos" y
estándares del SIEDU, y se revisaron contra lugares conocidos y precios de arriendo
(ver docs/modelo-puntaje.md).
"""

from score.domain.escalas import PorCantidad, PorDistanciaMinima, PorMinutos, PorPercentil
from score.domain.puntaje import Dimension, Indicador, Nivel

VERSION = "v1.1"

SEGURIDAD = Dimension(
    id="seguridad",
    nombre="Seguridad",
    peso=20,
    nivel=Nivel.COMUNA,
    indicadores=(
        # Los homicidios casi no tienen subdenuncia: es el dato policial más confiable.
        Indicador(
            "tasa_homicidios_100k_3a",
            0.50,
            PorPercentil(mayor_es_mejor=False),
            "Homicidios por 100 mil habitantes, promedio de 3 años (CEAD)",
        ),
        # Ocurre donde vive la gente: es el delito que más habla de la comuna como lugar
        # para vivir.
        Indicador(
            "robo_vivienda_por_1000_hogares",
            0.30,
            PorPercentil(mayor_es_mejor=False),
            "Robos en lugar habitado por cada 1.000 hogares (CEAD)",
        ),
        # Ocurren donde la gente trabaja y compra, pero se dividen por los residentes:
        # inflan a las comunas centrales. Pesan poco. Ley de armas no entra: mide más la
        # actividad policial que el riesgo (D-028).
        Indicador(
            "tasa_delitos_violentos_100k",
            0.20,
            PorPercentil(mayor_es_mejor=False),
            "Robos con violencia, por sorpresa, de vehículo con violencia y homicidios",
        ),
    ),
)

SOCIOECONOMICO = Dimension(
    id="socioeconomico",
    nombre="Entorno socioeconómico",
    peso=15,
    nivel=Nivel.MIXTO,
    indicadores=(
        Indicador(
            "escolaridad_hex",
            0.3,
            PorPercentil(),
            "Años de escolaridad de los adultos del sector (Censo 2024)",
        ),
        Indicador(
            "pct_hacinamiento_hex",
            0.2,
            PorPercentil(mayor_es_mejor=False),
            "Viviendas hacinadas en el sector (Censo 2024)",
        ),
        Indicador(
            "pct_pobreza_multidimensional",
            0.25,
            PorPercentil(mayor_es_mejor=False),
            "Pobreza multidimensional de la comuna (Casen 2024)",
        ),
        Indicador(
            "pct_pobreza_ingresos",
            0.25,
            PorPercentil(mayor_es_mejor=False),
            "Pobreza por ingresos de la comuna (Casen 2024)",
        ),
    ),
)

SERVICIOS = Dimension(
    id="servicios",
    nombre="Servicios cercanos",
    peso=20,
    nivel=Nivel.PUNTO,
    indicadores=(
        Indicador("min_supermercado", 0.20, PorMinutos(5, 25), "Supermercado a pie"),
        Indicador("min_farmacia", 0.10, PorMinutos(5, 25), "Farmacia a pie"),
        Indicador("min_colegio", 0.15, PorMinutos(8, 30), "Colegio a pie"),
        Indicador("min_jardin", 0.10, PorMinutos(8, 30), "Jardín infantil a pie"),
        Indicador("min_cesfam", 0.10, PorMinutos(10, 40), "CESFAM a pie"),
        Indicador("min_cajero", 0.05, PorMinutos(5, 25), "Banco o cajero a pie"),
        Indicador("min_urgencia", 0.15, PorMinutos(5, 20), "Urgencia en auto"),
        Indicador(
            "n800_comercio_barrio",
            0.15,
            PorCantidad(40),
            "Restaurantes, cafés, ferias y gimnasios a 800 m",
        ),
    ),
)

TRANSPORTE = Dimension(
    id="transporte",
    nombre="Transporte público",
    peso=15,
    nivel=Nivel.PUNTO,
    indicadores=(
        Indicador("min_metro", 0.40, PorMinutos(5, 30), "Estación de Metro a pie"),
        Indicador("min_paradero", 0.20, PorMinutos(3, 15), "Paradero de bus a pie"),
        Indicador("recorridos_400m", 0.25, PorCantidad(20), "Recorridos de bus a 400 m"),
        Indicador(
            "buses_hora_max_400m",
            0.15,
            PorCantidad(60),
            "Buses por hora en punta en el paradero más servido",
        ),
    ),
)

CONECTIVIDAD = Dimension(
    id="conectividad",
    nombre="Conectividad vial",
    peso=10,
    nivel=Nivel.PUNTO,
    indicadores=(
        Indicador("min_acceso_autopista", 0.5, PorMinutos(3, 15), "Acceso a autopista en auto"),
        Indicador(
            "min_centro_empleo",
            0.5,
            PorMinutos(15, 60),
            "Centro de empleo más cercano en auto (Centro, Providencia, El Golf, "
            "Ciudad Empresarial)",
        ),
    ),
)

AREAS_VERDES = Dimension(
    id="areas_verdes",
    nombre="Áreas verdes",
    peso=10,
    nivel=Nivel.PUNTO,
    indicadores=(
        Indicador("min_plaza", 0.5, PorMinutos(3, 15), "Plaza o área verde a pie"),
        Indicador("min_parque", 0.5, PorMinutos(8, 30), "Parque de más de 2 ha a pie"),
    ),
)

ENTORNO = Dimension(
    id="entorno",
    nombre="Ruido y molestias",
    peso=10,
    nivel=Nivel.PUNTO,
    indicadores=(
        Indicador(
            "m_via_rapida",
            0.6,
            PorDistanciaMinima(75, 800),
            "Distancia a autopistas y vías troncales (ruido de tráfico)",
        ),
        Indicador(
            "m_desamenidad",
            0.4,
            PorDistanciaMinima(300, 1500),
            "Distancia a cárceles, vertederos y plantas de tratamiento",
        ),
    ),
)

MODELO: tuple[Dimension, ...] = (
    SEGURIDAD,
    SOCIOECONOMICO,
    SERVICIOS,
    TRANSPORTE,
    CONECTIVIDAD,
    AREAS_VERDES,
    ENTORNO,
)
