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
│  ├─ map/            mapa (MapLibre), capas propias, panel de capas y dibujo (Terra Draw)
│  ├─ search/         búsqueda de direcciones
│  ├─ point-panel/    panel al tocar un punto: puntaje, dimensiones, cercanías, precios, comuna
│  ├─ zone/           informe y ficha de una zona dibujada
│  ├─ compare/        comparación de hasta 3 puntos
│  └─ export/         ficha 16:9, imagen satelital y exportación a PNG, PDF y PowerPoint
├─ shared/            cliente de la API, tipos, formatos es-CL y panel lateral
└─ styles/            tokens del sistema de diseño y estilos compartidos (botones, panel, diálogos)
```

## Servicios externos (sin clave)

- **Mapa base:** OpenFreeMap (estilos Liberty y Positron, datos de OpenStreetMap).
- **Satélite** (mapa e imagen de la ficha): Esri World Imagery, con atribución.
- **Búsqueda de direcciones:** Nominatim (OpenStreetMap), a través del backend.
