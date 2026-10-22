# La app (Fase 4)

## Qué hace

1. **Mapa de la RM** coloreado por puntaje (o por cualquiera de las 7 dimensiones), con
   los límites comunales. Gris claro = peor, negro = mejor; sin color = zona sin viviendas.
2. **Búsqueda de direcciones** (Nominatim, limitada a la RM).
3. **Al tocar un punto**, el panel muestra:
   - puntaje 0–100, letra, veredicto en una frase y percentil en la RM y en la comuna;
   - las 7 dimensiones con barra (en rojo si están bajo 50) y, al abrirlas, sus indicadores
     con el valor real y el peso;
   - cercanías a pie y en auto con el nombre del lugar más cercano, y la oferta del barrio;
   - **arriendos cercanos a pedido:** mediana, precio por m², por dormitorios y 5 avisos
     con enlace. Usa la caché de 7 días o consulta Toc Toc en el momento;
   - datos de la comuna.
4. **Exportar ficha** 16:9 en cuatro cuadrantes (el punto con imagen satelital,
   cercanías, comuna y arriendos, veredicto) a **PNG** (2400 × 1350), **PDF** o
   **PowerPoint**. Si no se habían consultado los arriendos, se consultan al abrir.

## Arquitectura

```
Navegador (React + MapLibre)
   │  /api/...
   ▼
FastAPI  (entrypoints/api.py)
   ├─ services/consulta_punto.py   ficha del punto
   ├─ services/precios.py          arriendos con caché
   └─ puertos (services/puertos.py)
        ├─ adapters/repositorio_parquet.py   puntajes y comunas en memoria
        ├─ adapters/cache_avisos.py          caché DuckDB (data/cache/avisos.duckdb)
        ├─ adapters/toctoc.py                portal de avisos
        └─ adapters/nominatim.py             direcciones (1 consulta/s)
```

| Ruta | Qué devuelve |
|---|---|
| `GET /api/capa` | Puntaje y dimensiones de los 9.666 hexágonos (formato columnar, 0,6 MB) |
| `GET /api/comunas` | Límites comunales simplificados (GeoJSON) |
| `GET /api/punto?lat&lon` | Ficha completa del punto |
| `GET /api/precios?lat&lon` | Arriendos a 800 m |
| `GET /api/buscar?q` | Direcciones en la RM |
| `GET /api/direccion?lat&lon` | Calle y número del punto |

La caché de avisos parte cargada con la muestra de `uv run score precios`; desde ahí,
cada comuna se vuelve a consultar en el portal si su dato tiene más de 7 días.

## Probado

- Recorrido completo en el navegador: carga del mapa, clic en el mapa, búsqueda de
  "Plaza Ñuñoa", cambio de capa, arriendos, ficha y generación del PNG (2400 × 1350,
  ~0,3 s). PDF y PowerPoint usan esa misma imagen; se verificó que compilan en la
  versión de producción, pero no se descargaron archivos durante la prueba.
- Vista de teléfono (375 px): el mapa arriba y el panel abajo.
- 79 pruebas del backend (incluida la API con dobles) y 10 del frontend.
