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
- [Modelo de puntaje](docs/modelo-puntaje.md): dimensiones, pesos, calibración y validación.
- [La app](docs/app.md): funciones, arquitectura y API.

## Usar la app

```bash
cd backend
uv run uvicorn score.entrypoints.api:app_por_defecto --factory --port 8000
```

```bash
cd frontend
npm run dev
```

Luego abre http://localhost:5173 (los datos tienen que estar generados; ver más abajo).

## Estado

- **Fase 1 (datos):** 10 fuentes descargadas con el pipeline y fichas de las 52 comunas.
- **Fase 2 (cercanías):** 9.666 hexágonos con minutos a 20 tipos de lugares por la red
  de calles, conteos del barrio y oferta de buses.
- **Fase 3 (puntaje):** modelo de 7 dimensiones, validado contra precios de arriendo
  (ρ 0,61 por hexágono, con 11.440 avisos) y contra el ICVU (ρ 0,65).
- **Fase 4 (app):** mapa, búsqueda, panel al tocar un punto, arriendos bajo demanda y
  ficha exportable a PNG, PDF y PowerPoint.
- **Fase 4b:** mapa de calles con capa de calor opcional, evaluación en el punto exacto,
  isócronas, capas de lugares y avisos, zonas dibujadas con su informe y ficha, regla,
  comparación de hasta 3 puntos y avisos de Toc Toc y Portal Inmobiliario (14.317).
- **Pendiente (Fase 5):** búsqueda inversa, plusvalía. Datos
  faltantes: SINIM (bloqueado), SIMCE, riesgos naturales y proyección futura.

## Reproducir los datos

```bash
cd backend
uv sync
uv run score datos descargar --incluir-pesadas
uv run score comunas
uv run score cercanias
uv run score puntajes
uv run score direcciones
uv run score precios     # muestra de arriendos de ambos portales (~1 h)
uv run score validar
```
