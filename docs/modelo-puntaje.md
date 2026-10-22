# Modelo de puntaje v1

Código: `backend/src/score/domain/modelo.py` (configuración) y `domain/puntaje.py`
(reglas). Se aplica con `uv run score puntajes` y se valida con `uv run score validar`.
Resultado: `data/processed/puntajes.parquet`, un hexágono por fila.

## Cómo se calcula

1. Cada indicador se lleva a una escala de **0 a 100** (100 = lo mejor):
   - **Por minutos:** 100 hasta un tiempo ideal, baja en línea recta y llega a 0 en un
     límite. Si no se alcanza en 120 minutos, vale 0.
   - **Por cantidad:** más es mejor hasta un punto de saturación.
   - **Por distancia mínima:** para lo que molesta estando cerca (autopistas, cárceles).
   - **Por percentil:** posición dentro de la RM ponderada por población. Un 70 significa
     que el 70% de los habitantes vive en un lugar peor en ese indicador.
2. Cada **dimensión** es el promedio ponderado de sus indicadores. Si a un indicador le
   falta el dato, su peso se reparte entre los demás.
3. El **puntaje** es el promedio ponderado de las dimensiones. La columna `cobertura`
   dice qué fracción del modelo se pudo evaluar (hoy es 100% en todos los hexágonos).
4. **Letra:** A ≥ 80 · B ≥ 65 · C ≥ 50 · D ≥ 35 · E < 35.
5. Se agrega el **percentil en la RM** y el **percentil dentro de su comuna**.

## Dimensiones

| Dimensión | Peso | Nivel | Indicadores (peso interno) |
|---|---:|---|---|
| Seguridad | 20 | Comuna | Homicidios por 100 mil, promedio de 3 años (0,30) · robos violentos por 100 mil (0,30) · ley de armas por 100 mil (0,15) · robo en vivienda por 1.000 hogares (0,25) |
| Entorno socioeconómico | 15 | Mixto | Escolaridad de adultos del hexágono (0,30) · hacinamiento del hexágono (0,20) · pobreza multidimensional comunal (0,25) · pobreza por ingresos comunal (0,25) |
| Servicios cercanos | 20 | Punto | Supermercado 5→25 min (0,20) · farmacia 5→25 (0,10) · colegio 8→30 (0,15) · jardín 8→30 (0,10) · CESFAM 10→40 (0,10) · cajero 5→25 (0,05) · urgencia en auto 5→20 (0,15) · comercio de barrio a 800 m, satura en 40 (0,15) |
| Transporte público | 15 | Punto | Metro 5→30 min (0,40) · paradero 3→15 (0,20) · recorridos a 400 m, satura en 20 (0,25) · buses por hora en punta, satura en 60 (0,15) |
| Conectividad vial | 10 | Punto | Acceso a autopista en auto 3→15 min (0,5) · centro de empleo en auto 15→60 min (0,5) |
| Áreas verdes | 10 | Punto | Plaza 3→15 min (0,5) · parque de más de 2 ha 8→30 min (0,5) |
| Tranquilidad del entorno | 10 | Punto | Distancia a autopistas y troncales, 75 m → 800 m (0,6) · distancia a cárceles, vertederos y plantas de tratamiento, 300 m → 1.500 m (0,4) |
| Proyección futura | — | — | Pendiente (sin datos de proyectos aún) |

"5→25 min" significa: 100 puntos hasta 5 minutos y 0 desde 25.

## Calibración

Se partió con los pesos del plan aprobado y umbrales de "ciudad de 15 minutos". Hubo dos
ajustes después de revisar los resultados:

1. **Seguridad.** La primera versión usaba robo en vivienda y robos violentos, y dejaba a
   La Reina (32) por debajo de Cerro Navia (68). La causa es que el robo en vivienda se
   denuncia más en comunas de mayores ingresos, y los robos violentos se inflan en
   comunas comerciales. Se agregaron los homicidios (casi sin subdenuncia, promediados en
   3 años) y los delitos con armas, y se bajó el peso del robo en vivienda. La coherencia
   con el ICVU subió de 0,62 a 0,66.
2. **Tranquilidad del entorno.** Con un radio de 400 m la mediana era 100 y la dimensión
   casi no distinguía lugares. Se amplió a 800 m, que es el alcance típico del ruido de
   una autopista.

Los pesos de las dimensiones **no se ajustaron para maximizar la correlación con el
precio**: el precio también mide prestigio y escasez, y eso no es lo mismo que calidad
de vida. Por ejemplo, el transporte público no se refleja en el arriendo, pero sí importa
para vivir.

## Validación

Los resultados de esta sección se calcularon con una muestra de 5.933 avisos de arriendo
de Toc Toc del 22-10-2026. Después de limpiar precios y superficies imposibles quedaron
3.454 avisos.

Para cada aviso se descuenta lo que explica la propiedad (casa o departamento, tamaño,
dormitorios) y queda un **premio de ubicación**: cuánto más (o menos) se paga por m² por
estar en ese lugar.

| Prueba | Correlación (Spearman) |
|---|---:|
| Puntaje vs. premio de ubicación, por hexágono (302 con 3+ avisos) | **0,66** |
| Puntaje vs. premio de ubicación, por comuna | **0,62** |
| Puntaje comunal vs. nivel ICVU 2025 (42 comunas, índice independiente) | **0,66** |

**Sensibilidad a los pesos** (correlación con el premio por hexágono):

| Ponderación | ρ |
|---|---:|
| v1 (pesos del plan) | **0,66** |
| Pesos iguales | 0,62 |
| Sin seguridad | 0,46 |
| Solo dimensiones medidas en el punto | 0,15 |

Los pesos del plan funcionan mejor que las alternativas. Lo que más explica el precio es
el entorno socioeconómico (0,72) y la seguridad (0,56); servicios (0,25) y áreas verdes
(0,19) aportan algo; transporte (0,01) y tranquilidad (−0,01) no se reflejan en el precio.

**Lugares conocidos:**

| Lugar | Puntaje | Letra | Lo más bajo |
|---|---:|:---:|---|
| Tobalaba (Providencia) | 92 | A | — |
| Plaza de Maipú | 86 | A | Seguridad 64 |
| Plaza Ñuñoa | 85 | A | Seguridad 63 |
| Colón con Tomás Moro (Las Condes) | 83 | A | Áreas verdes 55 |
| La Dehesa (Lo Barnechea) | 80 | B | Transporte 39 |
| Plaza de Puente Alto | 79 | B | Socioeconómico 47 |
| Plaza de Armas (Santiago) | 77 | B | Seguridad 36 |
| Bajos de Mena (Puente Alto) | 63 | C | Socioeconómico 28 |
| La Pintana centro | 59 | C | Socioeconómico 8 |
| Melipilla centro | 49 | D | Transporte 0 |

**Distribución en la RM** (por población): A 8% · B 40% · C 41% · D 10% · E 2%.

## Limitaciones conocidas

- **Seguridad comunal:** todos los hexágonos de una comuna comparten el mismo valor. No hay
  datos públicos de delitos por cuadra.
- **Ruido:** el mapa de ruido del MMA solo se publica como informe en PDF, sin datos
  geográficos. Se usa la distancia a autopistas y troncales como aproximación.
- **Colegios:** aún no se ponderan por SIMCE.
- **Proyección futura:** no incluida. Faltan los trazados de nuevas líneas de Metro y de
  autopistas.
- **Comunas rurales:** tienen menos datos de OpenStreetMap y no tienen buses en el GTFS, así
  que su transporte queda en 0 aunque existan buses rurales.
- **Muestra de precios:** es la primera página de resultados por comuna y tipo (hasta 260
  avisos). Faltó "casas en Las Condes" por un error 502 del portal, y algunas comunas
  rurales no tenían oferta.
