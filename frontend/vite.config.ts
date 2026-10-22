import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// En desarrollo, /api se redirige al backend (FastAPI en el puerto 8000).
export default defineConfig({
  plugins: [react()],
  // MapLibre v6 carga su worker con import.meta.url; el pre-empaquetado de Vite rompe esa ruta.
  optimizeDeps: { exclude: ["maplibre-gl"] },
  // El paquete principal pesa ~1,5 MB por MapLibre; PDF y PowerPoint se cargan aparte al exportar.
  build: { chunkSizeWarningLimit: 1700 },
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "node",
  },
});
