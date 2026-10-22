# La app

## Qué hace

1. **Mapa de la RM** con calles (OpenFreeMap), en versión normal, gris o satélite, y los
   límites comunales.
2. **Capa de calor** opcional del puntaje o de cualquiera de las 7 dimensiones: rojo bajo
   la mediana de la RM, negro sobre ella, con intensidad ajustable (D-024).
3. **Capas de lugares:** Metro y tren, colegios, salud (CESFAM, urgencias, hospitales y
   clínicas) y supermercados. **Avisos de arriendo** como puntos (más oscuro, más caro
   por m²); al tocar uno se ve el precio y el enlace al aviso.
4. **Búsqueda de direcciones** (Nominatim, limitada a la RM).
5. **Al tocar un punto**, el panel muestra (calculado en las coordenadas exactas, D-025):
   - puntaje 0–100, letra, veredicto en una frase y percentil en la RM y en la comuna;
   - las 7 dimensiones con barra (en rojo si están bajo 50) y sus indicadores;
   - cercanías a pie y en auto con el lugar más cercano, y la oferta del barrio;
   - **arriendos a 800 m:** mediana, precio por m², por dormitorios y 5 avisos con
     enlace, de Toc Toc y Portal Inmobiliario (D-021, D-022);
   - datos de la comuna;
   - **isócrona a pie** de 5, 10 y 15 minutos sobre el mapa.
6. **Herramientas de dibujo:** polígono, rectángulo y círculo para una **zona**, y una
   regla para **medir** distancias. La zona abre su informe (D-026): puntaje promedio por
   habitante, rango, población por letra, dimensiones, lugares dentro, arriendos dentro y
   comunas.
7. **Comparar** hasta 3 puntos lado a lado (D-027), numerados en el mapa.
8. **Exportar ficha** 16:9 de un punto o de una zona, en cuatro cuadrantes, a **PNG**
   (2400 × 1350), **PDF** o **PowerPoint**.

## Arquitectura

```
Navegador (React + MapLibre + Terra Draw)
   │  /api/...
   ▼
FastAPI  (entrypoints/api.py)
   ├─ services/consulta_punto.py   ficha del punto exacto
   ├─ services/precios.py          arriendos con caché
   ├─ services/zona.py             informe de una zona dibujada
   └─ puertos (services/puertos.py)
        ├─ adapters/repositorio_parquet.py    puntajes, lugares y comunas en memoria
        ├─ adapters/motor_cercanias.py        minutos por la red desde cualquier punto
        ├─ adapters/superficie.py             capa de calor (PNG georreferenciado)
        ├─ adapters/cache_avisos.py           caché DuckDB (data/cache/avisos.duckdb)
        ├─ adapters/toctoc.py                 portal de avisos con coordenadas
        ├─ adapters/portal_inmobiliario.py    portal de avisos con dirección escrita
        ├─ adapters/geocodificador_local.py   direcciones de OSM → coordenadas
        └─ adapters/nominatim.py              buscador de direcciones (1 consulta/s)
```

| Ruta | Qué devuelve |
|---|---|
| `GET /api/superficie` | Esquinas de la capa de calor y variables disponibles |
| `GET /api/superficie/{variable}.png` | Imagen de la capa de calor (1373 × 1351, ~0,4 MB) |
| `GET /api/comunas` | Límites comunales simplificados (GeoJSON) |
| `GET /api/punto?lat&lon` | Ficha completa del punto |
| `GET /api/isocrona?lat&lon` | Áreas a 5, 10 y 15 minutos a pie (GeoJSON) |
| `GET /api/precios?lat&lon` | Arriendos a 800 m |
| `POST /api/zona` | Informe de la zona; cuerpo `{"geometria": <Polygon GeoJSON>}` |
| `GET /api/lugares?categorias=metro,colegio` | Lugares del catálogo (GeoJSON) |
| `GET /api/avisos` | Avisos bien ubicados de la caché (GeoJSON) |
| `GET /api/buscar?q` | Direcciones en la RM |
| `GET /api/direccion?lat&lon` | Calle y número del punto |
| `GET /api/capa` | Puntajes por hexágono en formato columnar (el mapa ya no lo usa) |

La caché de avisos parte cargada con la última muestra de `uv run score precios`
(`data/interim/avisos/avisos_arriendo_*.parquet`); desde ahí, cada comuna y portal se
vuelve a consultar si su dato tiene más de 7 días. Si cambia el formato de la caché,
basta con borrar `data/cache/avisos.duckdb`: se vuelve a crear desde la muestra.

## Probado

- Recorrido en el navegador (1440 × 900): capa de calor, cambio a satélite, capas de
  Metro y de avisos (12.795 puntos), ventana de un aviso, punto con isócrona, arriendos
  de ambos portales, comparación de dos puntos, rectángulo y círculo con su informe,
  ficha de zona y regla de medir. No se descargaron archivos durante la prueba; la
  exportación usa el mismo código de la Fase 4.
- 127 pruebas del backend (incluida la API con dobles) y 16 del frontend.
