# Frontend

React + TypeScript + Vite + MapLibre. Se crea en la Fase 4, una vez elegida la dirección
visual (ver [docs/diseno.md](../docs/diseno.md)).

Estructura prevista, organizada por funcionalidad:

```
src/
├─ features/
│  ├─ map/            mapa, capas y selección de punto
│  ├─ point-panel/    puntaje, dimensiones, cercanías, comuna y precios
│  └─ export/         ficha 16:9 (PNG, PDF, PPTX)
├─ shared/            componentes y utilidades comunes
└─ styles/tokens.css  colores, tipografía y espaciado: única fuente de estilos
```
