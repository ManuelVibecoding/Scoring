# Backend

Python 3.12, administrado con `uv`. Arquitectura en capas (estilo Cosmic Python):

```
src/score/
├─ domain/       Reglas del puntaje y modelos. Puro: sin red, sin archivos, sin base de datos.
├─ services/     Casos de uso (evaluar un punto, buscar comparables, exportar ficha).
│                Orquestan el dominio usando interfaces (puertos), no implementaciones.
├─ adapters/     Implementaciones concretas: repositorios DuckDB, scrapers, fuentes externas.
├─ entrypoints/  Puertas de entrada: API HTTP (FastAPI) y comandos de consola.
└─ pipeline/     Trabajos de datos: descargar, limpiar y precalcular por hexágono.
```

Regla de dependencias: `entrypoints → services → domain`; `adapters` implementa las
interfaces que define `services`. El dominio nunca importa nada de las otras capas.

## Comandos

```bash
uv sync                 # instala dependencias
uv run pytest           # pruebas
uv run ruff check .     # estilo
uv run mypy             # tipos

uv run score datos listar                       # fuentes registradas
uv run score datos descargar                    # baja las fuentes livianas a data/raw
uv run score datos descargar --incluir-pesadas  # también OSM y ruido (~570 MB)
uv run score comunas                            # fichas de las 52 comunas
uv run score cercanias                          # cercanías por hexágono (~80 s)
```
