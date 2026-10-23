# Score — Scoring de ubicaciones habitacionales (Región Metropolitana)

Tocas un punto en el mapa de la RM y la app te dice qué tan buena es esa ubicación para vivir:
un puntaje 0–100 (letra A–E), el desglose por dimensión, lo que tienes cerca, los datos de la
comuna, los arriendos comparables de la zona y una ficha exportable para presentaciones.
También puedes dibujar una zona para ver su informe, comparar hasta 3 puntos y medir
distancias.

Todo corre en tu computador. Los datos no vienen en el repositorio: se descargan de las
fuentes oficiales con el pipeline incluido (ver abajo).

## Instalar y correr en tu PC

### 1. Requisitos

- [Git](https://git-scm.com/downloads)
- [uv](https://docs.astral.sh/uv/getting-started/installation/), que instala Python 3.12 por
  su cuenta
- [Node.js](https://nodejs.org/) 20 o más nuevo
- Unos 4 GB libres en disco e internet para la primera descarga

### 2. Descargar el código e instalar dependencias

```bash
git clone https://github.com/ManuelVibecoding/Scoring.git
cd Scoring
cd backend && uv sync && cd ..
cd frontend && npm install && cd ..
```

### 3. Generar los datos (una sola vez)

```bash
cd backend
uv run score datos descargar --incluir-pesadas   # fuentes oficiales y OpenStreetMap
uv run score comunas                             # fichas de las 52 comunas
uv run score cercanias                           # red de calles y minutos a cada lugar
uv run score puntajes                            # aplica el modelo a cada hexágono
uv run score direcciones                         # índice para ubicar avisos de arriendo
```

La descarga y el cálculo toman un buen rato la primera vez (la red de calles de toda la RM
es lo más pesado). Después la app parte en segundos.

Opcional: `uv run score precios` baja una muestra de avisos de arriendo de toda la RM
(Toc Toc y Portal Inmobiliario, ~1 h) y `uv run score validar` compara el puntaje con esos
precios. Sin la muestra la app funciona igual: los arriendos de una comuna se consultan la
primera vez que los pides (puede tardar un par de minutos) y quedan guardados 7 días.

### 4. Abrir la app

En Windows, doble clic en `iniciar.bat`. En macOS o Linux, en dos terminales:

```bash
cd backend && uv run uvicorn score.entrypoints.api:app_por_defecto --factory --port 8000
```

```bash
cd frontend && npm run dev
```

Luego abre http://localhost:5173.

## Sobre los datos y el scraping

- Las fuentes, sus licencias y fechas están en el [catálogo de datos](docs/catalogo-datos.md).
  La licencia MIT de este repositorio cubre el código, no los datos de cada fuente (por
  ejemplo, OpenStreetMap se publica bajo ODbL).
- Los scrapers de avisos respetan el `robots.txt` de cada portal, esperan entre páginas y
  no evitan captchas. Úsalos con moderación y para uso personal; los avisos descargados no
  se deben volver a publicar.
- El puntaje es una herramienta de orientación, no una tasación ni una recomendación de
  inversión.

## Documentación

- [Plan del proyecto](docs/plan.md): dimensiones, fuentes de datos, metodología y fases.
- [Decisiones](docs/decisiones.md): registro de decisiones tomadas y por qué.
- [Diseño](docs/diseno.md): dirección visual, principios y lo que está prohibido.
- [Catálogo de datos](docs/catalogo-datos.md): fuentes, estado y procedencia.
- [Fichas de las 52 comunas](docs/fichas-comunas.md): indicadores comunales generados.
- [Cercanías por hexágono](docs/cercanias.md): método, columnas, validación y supuestos.
- [Modelo de puntaje](docs/modelo-puntaje.md): dimensiones, pesos, calibración y validación.
- [La app](docs/app.md): funciones, arquitectura y API.
- [Backend](backend/README.md) y [frontend](frontend/README.md): estructura y comandos de
  desarrollo.

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

## Licencia

[MIT](LICENSE) © 2026 Manuel Amenábar.
