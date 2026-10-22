import { cellToBoundary } from "h3-js";
import { Map as MapaMapLibre, type ErrorEvent } from "maplibre-gl";
import { SENAL } from "../../styles/tokens";

// Imagen satelital gratuita (Esri World Imagery); requiere atribución en la ficha.
const SATELITE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
export const ATRIBUCION_SATELITE = "Imagen: Esri, Maxar, Earthstar Geographics";

// Misma proporción que el cuadrante 01 de la ficha (≈ 2,67 : 1), al doble de resolución.
const ANCHO = 1440;
const ALTO = 540;
const ZOOM = 16.4;
const ESPERA_MAXIMA_MS = 15_000;

/**
 * Dibuja fuera de pantalla una vista satelital del punto con su hexágono marcado en rojo
 * y la devuelve como imagen PNG (data URL). Así la ficha no depende del mapa visible.
 */
export async function imagenDelPunto(lat: number, lon: number, h3: string): Promise<string> {
  const contenedor = document.createElement("div");
  Object.assign(contenedor.style, {
    position: "fixed",
    left: "-10000px",
    top: "0",
    width: `${ANCHO}px`,
    height: `${ALTO}px`,
  });
  document.body.appendChild(contenedor);

  const anillo = cellToBoundary(h3, true); // [lng, lat], anillo cerrado

  const mapa = new MapaMapLibre({
    container: contenedor,
    center: [lon, lat],
    zoom: ZOOM,
    interactive: false,
    attributionControl: false,
    canvasContextAttributes: { preserveDrawingBuffer: true },
    style: {
      version: 8,
      sources: {
        satelite: { type: "raster", tiles: [SATELITE], tileSize: 256, maxzoom: 19 },
        hexagono: {
          type: "geojson",
          data: { type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [anillo] } },
        },
        punto: {
          type: "geojson",
          data: { type: "Feature", properties: {}, geometry: { type: "Point", coordinates: [lon, lat] } },
        },
      },
      layers: [
        { id: "satelite", type: "raster", source: "satelite" },
        { id: "hexagono", type: "line", source: "hexagono", paint: { "line-color": SENAL, "line-width": 7 } },
        {
          id: "punto",
          type: "circle",
          source: "punto",
          paint: { "circle-radius": 7, "circle-color": SENAL, "circle-stroke-color": "#ffffff", "circle-stroke-width": 2 },
        },
      ],
    },
  });

  try {
    await new Promise<void>((resolver, rechazar) => {
      const limite = setTimeout(() => rechazar(new Error("La imagen satelital tardó demasiado.")), ESPERA_MAXIMA_MS);
      mapa.once("idle", () => {
        clearTimeout(limite);
        resolver();
      });
      mapa.once("error", (e: ErrorEvent) => {
        clearTimeout(limite);
        rechazar(e.error instanceof Error ? e.error : new Error("No se pudo cargar la imagen satelital."));
      });
    });
    return mapa.getCanvas().toDataURL("image/png");
  } finally {
    mapa.remove();
    contenedor.remove();
  }
}
