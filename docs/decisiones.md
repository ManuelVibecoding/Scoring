# Registro de decisiones

Cada decisión tiene fecha, qué se decidió y por qué. Si una decisión cambia, se agrega una
nueva entrada que la reemplaza (no se borra la anterior).

---

## D-001 · Alcance: las 52 comunas de la Región Metropolitana
**Fecha:** 2026-10-22
**Decisión:** el mapa y los datos cubren las 52 comunas de la RM, no solo el Gran Santiago.
**Consecuencia:** las comunas rurales (Alhué, María Pinto, San Pedro, etc.) tendrán menos
servicios y menos datos finos; el puntaje debe distinguir "dato bajo" de "sin dato".

## D-002 · Un solo puntaje, sin perfiles
**Fecha:** 2026-10-22
**Decisión:** un único puntaje general con pesos fijos y visibles. No hay perfiles
(familia, joven, inversionista).
**Por qué:** el usuario no los considera útiles; simplifica la app y la ficha exportada.
Los pesos viven en configuración, así que ajustarlos después no requiere tocar código.

## D-003 · El precio no entra en el puntaje de calidad
**Fecha:** 2026-10-22
**Decisión:** arriendo y precio de venta se muestran aparte, junto a una relación
calidad/precio.
**Por qué:** mezclar precio y calidad esconde las oportunidades (buena ubicación a precio bajo).

## D-004 · Imagen del punto: fuentes gratuitas
**Fecha:** 2026-10-22
**Decisión:** imagen a nivel de calle con Mapillary y vista satelital gratuita.
Sin Google Street View.

## D-005 · Uso personal
**Fecha:** 2026-10-22
**Decisión:** la app es de uso personal. Corre localmente, no se publica.
Se respetan igual las atribuciones de licencia (OSM, Mapillary).

## D-006 · Precios: scraping bajo demanda con caché que se acumula
**Fecha:** 2026-10-22
**Decisión:** no se hace un scraping semanal de toda la RM. Al tocar un punto:
1. Si la zona (hexágono y vecinos) se revisó hace menos de 7 días, se usan los avisos
   guardados: respuesta instantánea.
2. Si no, se lanza un trabajo en segundo plano que busca avisos en un radio alrededor del
   punto (Toc Toc y Portal Inmobiliario), los guarda en la base local y actualiza el panel.
   Meta: menos de 1 minuto.
3. Mientras tanto, el panel muestra todo lo demás al instante y un precio de referencia
   comunal (informes públicos), marcado como tal.

Todo aviso se guarda con fecha, así que la base crece sola en las zonas que se consultan
y con el tiempo da historial de precios.
**Por qué:** un barrido completo de la RM es lento y frágil; consultar solo donde se mira
es viable y la espera es aceptable para el usuario (hasta ~1 minuto).
**Límites:** ritmo moderado de consultas; si un portal bloquea con captcha no se evade,
se usa el otro portal o el precio de referencia.
**Resultado de la prueba (2026-10-22):** Toc Toc entrega coordenadas en la búsqueda por
comuna y 260 avisos por página (~20 s por comuna); será la fuente principal. Portal
Inmobiliario no trae coordenadas en la búsqueda y queda como complemento. Detalle en
[factibilidad-scraping.md](factibilidad-scraping.md).

## D-007 · Arquitectura en capas (estilo Cosmic Python)
**Fecha:** 2026-10-22
**Decisión:**
- `backend/` en Python 3.12 + FastAPI, separado en `domain` (reglas puras), `services`
  (casos de uso), `adapters` (datos, scrapers, fuentes externas) y `entrypoints` (API).
- `backend/src/score/pipeline/` para descargar, limpiar y precalcular datos por hexágono
  (H3). Vive dentro del backend para compartir adaptadores (scrapers, fuentes) sin duplicar.
- `frontend/` en React + TypeScript + Vite + MapLibre, organizado por funcionalidad.
- Base de datos local DuckDB con extensión espacial.
- Calidad: ruff, mypy, pytest; TypeScript estricto, ESLint, Vitest. Git desde el inicio.
**Por qué:** calza con la Academia de Programación del usuario (Fases 6 y 7), el dominio
queda testeable sin depender de internet, y cambiar una fuente o la base de datos no
obliga a tocar las reglas del puntaje.

## D-008 · Entorno de trabajo
**Fecha:** 2026-10-22
**Decisión:** se trabaja desde la app de escritorio de Claude (pestaña Code), con VS Code
abierto en la misma carpeta para leer el código. Python lo administra `uv`.

## D-009 · Diseño elegante, sin apariencia de plantilla de IA
**Fecha:** 2026-10-22
**Decisión:** la interfaz sigue una dirección visual definida y principios escritos en
[diseno.md](diseno.md), con una lista explícita de patrones prohibidos. Todo color y
tipografía sale de tokens CSS.
**Por qué:** el usuario quiere un producto elegante que no se note hecho 100% con Claude.
**Dirección elegida:** C · Suizo minimal (blanco, negro, rojo señal `#E2231A`, tipografía Archivo).

## D-010 · Delitos: extracto comunitario del CEAD mientras el oficial no esté disponible
**Fecha:** 2026-10-22
**Decisión:** los casos policiales se toman del Parquet que mantiene el proyecto
bastianolea/delincuencia_chile (extraído del CEAD, hasta diciembre de 2025).
**Por qué:** el sitio del CEAD respondía 502 y no ofrece descarga masiva; el extracto
cubre las 52 comunas y los 30 tipos de delito.
**Cómo revertir:** cambiar los recursos de la fuente `cead_delitos` en `fuentes.py`.

## D-011 · Indicadores comunales del censo desde la base CSV, no desde la cartografía
**Fecha:** 2026-10-22
**Decisión:** las fichas comunales suman la base manzana–entidad (CSV) incluyendo las
filas "contenedor comunal". La cartografía por manzana se usa solo para análisis espacial.
**Por qué:** el INE reserva datos de manzanas pequeñas; la cartografía suma 7,06 millones
de personas en la RM y el CSV con contenedores suma 7.400.741, el total oficial.

## D-012 · Las tasas de delitos se calculan por residente
**Fecha:** 2026-10-22
**Decisión:** por ahora las tasas se dividen por la población del Censo 2024. Santiago,
Providencia y Estación Central aparecen infladas por población flotante.
**Pendiente (Fase 3):** corregir con un indicador de población flotante (por ejemplo,
viajes atraídos según la Encuesta Origen-Destino) antes de usarlas en el puntaje.

## D-013 · Grilla H3 de resolución 9 solo sobre zonas habitadas
**Fecha:** 2026-10-22
**Decisión:** las cercanías se precalculan en hexágonos H3 de resolución 9 que contienen
al menos una manzana del Censo 2024 (9.666 hexágonos).
**Por qué:** ~174 m de lado es menos de dos cuadras; el resultado es pequeño y la
respuesta al tocar el mapa es instantánea. Fuera de las zonas habitadas no hay viviendas
que evaluar.

## D-014 · Distancias por la red de calles, con todo en DuckDB + scipy
**Fecha:** 2026-10-22
**Decisión:** OSM se lee directamente con DuckDB (ST_ReadOSM) y las distancias se
calculan con un Dijkstra multi-fuente de scipy desde un nodo virtual por categoría.
**Por qué:** sin herramientas externas (osmium, OSRM, servidores); todo el cálculo de la
RM toma ~80 s y queda en Python, testeable.
**Alternativa futura:** tiempos reales en auto con datos de congestión, si se consiguen.

## D-016 · El ICVU se usa para validar, no como insumo
**Fecha:** 2026-10-22
**Decisión:** el nivel ICVU no entra al puntaje; se usa como referencia independiente.
**Por qué:** si fuera insumo, la coherencia con él no probaría nada. Además cubre solo 42
de las 52 comunas.

## D-017 · Seguridad con homicidios y delitos con armas
**Fecha:** 2026-10-22
**Decisión:** la dimensión de seguridad combina homicidios (promedio de 3 años), robos
violentos, ley de armas y robo en vivienda por hogar (con menor peso).
**Por qué:** el robo en vivienda tiene más denuncia en comunas de mayores ingresos y los
robos violentos se inflan con la población flotante; los homicidios casi no tienen
subdenuncia. Reemplaza el pendiente de D-012.

## D-018 · Validación contra el precio, sin ajustar pesos al precio
**Fecha:** 2026-10-22
**Decisión:** el puntaje se valida contra el premio de ubicación en arriendos (Toc Toc),
pero los pesos se mantienen los del plan.
**Por qué:** el precio refleja también prestigio y escasez. Los pesos del plan ya superan
a las alternativas probadas (ρ 0,66 contra 0,62 con pesos iguales).

## D-019 · Servicios de mapa sin clave ni costo
**Fecha:** 2026-10-22
**Decisión:** mapa base OpenFreeMap (Positron, en grises), imagen satelital de Esri World
Imagery para la ficha y Nominatim para buscar direcciones.
**Por qué:** uso personal y "calle gratis" (D-004). Mapillary exige crear una cuenta y un
token; queda como mejora opcional para agregar foto a nivel de calle.

## D-020 · La ficha se exporta como imagen en los tres formatos
**Fecha:** 2026-10-22
**Decisión:** la ficha se dibuja en HTML (1600 × 900) y se convierte a PNG; el PDF y la
lámina de PowerPoint contienen esa imagen.
**Por qué:** se ve idéntica en los tres formatos y respeta la tipografía. Una lámina de
PowerPoint con texto editable queda como mejora futura.

## D-015 · Emergencias se miden desde el servicio hacia la casa
**Fecha:** 2026-10-22
**Decisión:** bomberos y policía se miden como viaje cuartel → casa; urgencias,
hospitales y autopistas como casa → lugar. En auto se respetan los sentidos de tránsito.

## D-021 · Portal Inmobiliario con geocodificación propia
**Fecha:** 2026-10-22
**Decisión:** además de Toc Toc se consulta Portal Inmobiliario (páginas `_Desde_N`, 48
avisos por página, hasta 60 páginas por comuna y tipo). Como sus tarjetas traen solo la
dirección escrita, se ubican con un índice propio de direcciones de OpenStreetMap
(`score direcciones`): número exacto, interpolado entre números de la misma calle,
mediana de la calle o cruce de dos calles.
**Por qué:** Toc Toc entrega como máximo 260 avisos por consulta y su robots.txt no
permite paginar, así que en comunas con miles de avisos los arriendos "cercanos" eran casi
los mismos en todo el sector. La vista de mapa del portal (`_DisplayType_M`) está
prohibida por robots.txt y la API de MercadoLibre responde 403. Con ambos portales la
muestra pasó de 5.933 a 14.317 avisos (Las Condes: de 260 a 1.077 bien ubicados).

## D-022 · Solo avisos bien ubicados cuentan como cercanos
**Fecha:** 2026-10-22
**Decisión:** cada aviso guarda la precisión de su ubicación (exacta, interpolada, calle o
aproximada). Los resúmenes "a 800 m", el mapa y las zonas usan solo exacta e interpolada.
Un aviso publicado en ambos portales (a menos de 80 m, mismos dormitorios y precio con
diferencia menor a 2 %) se cuenta una vez.
**Por qué:** una calle larga como Apoquindo mide kilómetros; ubicar un aviso en su
mediana lo cambia de barrio. El 56 % de los avisos del portal se ubica con número exacto
o interpolado.

## D-023 · La UF se lee del SII
**Fecha:** 2026-10-22
**Decisión:** los avisos en UF se pasan a pesos con la UF del día publicada por el SII
(`sii.cl/valores_y_fechas/uf/`).
**Por qué:** mindicador.cl falló por SSL y por tiempo de espera al probarlo; el SII es la
fuente oficial y no pide clave.

## D-024 · Mapa normal con capa de calor opcional
**Fecha:** 2026-10-22
**Decisión:** el mapa base pasa a ser un mapa de calles normal (OpenFreeMap Liberty, con
opción gris o satélite). El puntaje se muestra como una superficie suavizada (grilla de
90 m, suavizado de 200 m) que se puede apagar. Los colores se cortan en los percentiles
10, 50 y 90 de la población de la RM: rojo bajo la mediana, negro sobre ella. Los
hexágonos siguen siendo la unidad de cálculo, pero no se dibujan.
**Por qué:** los hexágonos tapaban el mapa y hacían difícil ubicarse. Cortar por
percentiles evita que la capa se vea pareja cuando la mayoría de los valores son altos.

## D-025 · El punto se evalúa en sus coordenadas exactas
**Fecha:** 2026-10-22
**Decisión:** las cercanías se calculan para el punto tocado (no para el centro de su
hexágono) con un motor precalculado: minutos desde cada nodo de la red a cada tipo de
lugar (`data/processed/motor/`, 290 MB). Lo comunal y lo del Censo se toma del hexágono.
**Por qué:** dos puntos del mismo hexágono pueden estar a 2 o a 4 minutos del Metro. El
motor responde en ~250 ms y también calcula la isócrona a pie en ~30 ms.

## D-026 · Informe de zona ponderado por población
**Fecha:** 2026-10-22
**Decisión:** una zona dibujada (polígono, rectángulo o círculo, hasta 400 km²) se
resume con el promedio de sus hexágonos ponderado por personas, el rango donde vive el
80 % central, la distribución por letra, los lugares contados dentro y los arriendos
ubicados dentro.
**Por qué:** un promedio simple daría el mismo peso a un cerro vacío que a un barrio
denso. El límite de área mantiene la respuesta rápida.

## D-027 · Comparar hasta tres puntos
**Fecha:** 2026-10-22
**Decisión:** se guardan hasta 3 puntos y se comparan en una tabla con el mejor valor de
cada fila en rojo. Los arriendos no se marcan: más caro no es mejor ni peor.
**Por qué:** más de tres columnas no caben a lo ancho de la pantalla de un notebook.

## D-028 · Seguridad v1.1: homicidios pesan la mitad, sin ley de armas
**Fecha:** 2026-10-22
**Decisión:** la seguridad pasa a ser homicidios (0,50), robo en vivienda por hogar (0,30)
y robos violentos (0,20). Se quita la ley de armas. La dimensión "Tranquilidad del
entorno" se renombra "Ruido y molestias". El modelo pasa a v1.1. Reemplaza la
ponderación de D-017.
**Por qué:** con la v1, Providencia (48) quedaba bajo Puente Alto (53) aunque tiene un
cuarto de sus homicidios. Los robos violentos y la ley de armas se dividen por residentes
pero ocurren donde la gente trabaja y compra, y la ley de armas mide sobre todo controles
policiales. Con el cambio, Providencia sube a 68 y Puente Alto baja a 47. La seguridad
explica mejor el precio (ρ 0,57 → 0,62); el puntaje total queda igual por hexágono
(0,61) y baja levemente por comuna (0,52 → 0,49) y contra el ICVU (0,66 → 0,65). El
nombre anterior hacía pensar en delincuencia, que se mide en Seguridad.

## D-029 · Código público con licencia MIT, datos fuera del repositorio
**Fecha:** 2026-10-22
**Decisión:** el código se publica en GitHub con licencia MIT para que cualquiera pueda
correrlo en su computador. Los datos no se suben: cada persona los descarga de las fuentes
oficiales con el pipeline. Los avisos de arriendo descargados nunca se versionan. Ajusta
D-005: la app sigue corriendo localmente, pero el código ya no es solo personal.
**Por qué:** los datos pesan varios GB y cada fuente tiene su propia licencia; los avisos
pertenecen a los portales y no corresponde redistribuirlos.
