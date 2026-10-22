# Frontend

React 19 + TypeScript (estricto) + Vite + MapLibre. Diseño C · Suizo minimal
([docs/diseno.md](../docs/diseno.md)).

## Correr

Primero el backend (en otra terminal):

```bash
cd backend
uv run uvicorn score.entrypoints.api:app_por_defecto --factory --port 8000
```

Luego la app:

```bash
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173. Vite redirige `/api` al backend.

## Comandos

```bash
npm run typecheck   # TypeScript
npm run lint        # ESLint
npm test            # Vitest
npm run build       # versión de producción en dist/
```

## Estructura

```
src/
├─ features/
│  ├─ map/            mapa (MapLibre), capa de hexágonos H3 y leyenda
│  ├─ search/         búsqueda de direcciones
│  ├─ point-panel/    panel al tocar un punto: puntaje, dimensiones, cercanías, precios, comuna
│  └─ export/         ficha 16:9 y exportación a PNG, PDF y PowerPoint
├─ shared/            cliente de la API, tipos y formatos es-CL
└─ styles/            tokens del sistema de diseño (única fuente de colores y tipografía)
```

## Servicios externos (sin clave)

- **Mapa base:** OpenFreeMap (estilo Positron, datos de OpenStreetMap).
- **Imagen del punto en la ficha:** Esri World Imagery (satelital, con atribución).
- **Búsqueda de direcciones:** Nominatim (OpenStreetMap), a través del backend.
