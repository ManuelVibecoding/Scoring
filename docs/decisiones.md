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
**Por investigar en Fase 1:** si los portales tienen búsqueda por mapa (rectángulo de
coordenadas) que devuelva avisos con ubicación en una sola consulta.

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
