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

## D-015 · Emergencias se miden desde el servicio hacia la casa
**Fecha:** 2026-10-22
**Decisión:** bomberos y policía se miden como viaje cuartel → casa; urgencias,
hospitales y autopistas como casa → lugar. En auto se respetan los sentidos de tránsito.
