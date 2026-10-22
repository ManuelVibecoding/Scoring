# Score — Scoring de ubicaciones habitacionales (Región Metropolitana)

Tocas un punto en el mapa de la RM y la app te dice qué tan buena es esa ubicación para vivir:
un puntaje 0–100 (letra A–E), el desglose por dimensión, lo que tienes cerca, los datos de la
comuna, los arriendos comparables de la zona y una ficha exportable para presentaciones.

## Documentación

- [Plan del proyecto](docs/plan.md): dimensiones, fuentes de datos, metodología y fases.
- [Decisiones](docs/decisiones.md): registro de decisiones tomadas y por qué.
- [Diseño](docs/diseno.md): dirección visual, principios y lo que está prohibido.

- [Catálogo de datos](docs/catalogo-datos.md): fuentes, estado y procedencia.
- [Fichas de las 52 comunas](docs/fichas-comunas.md): indicadores comunales generados.
- [Cercanías por hexágono](docs/cercanias.md): método, columnas, validación y supuestos.

## Estado

- **Fase 1 (datos):** 10 fuentes descargadas con el pipeline y fichas de las 52 comunas.
- **Fase 2 (cercanías):** 9.666 hexágonos con minutos a 20 tipos de lugares por la red
  de calles, conteos del barrio y oferta de buses.
- **Pendiente:** SINIM (bloqueado), SIMCE, fuentes ambientales y de riesgo, y la Fase 3
  (modelo de puntaje).

## Reproducir los datos

```bash
cd backend
uv sync
uv run score datos descargar --incluir-pesadas
uv run score comunas
uv run score cercanias
```
