import { cellToBoundary } from "h3-js";
import { type ErrorEvent, LngLatBounds, Map as MapaMapLibre, type StyleSpecification } from "maplibre-gl";
import { SENAL } from "../../styles/tokens";

// Imagen satelital gratuita (Esri World Imagery); requiere atribución en la ficha.
const SATELITE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
export const ATRIBUCION_SATELITE = "Imagen: Esri, Maxar, Earthstar Geographics";

// Misma proporción que el cuadrante 01 de la ficha (≈ 2,67 : 1), al doble de resolución.
const ANCHO = 1440;
const ALTO = 540;
const ZOOM_PUNTO = 16.4;
const MARGEN_ZONA_PX = 48;
const ESPERA_MAXIMA_MS = 15_000;

type Vista = { centro: [number, number]; zoom: number } | { limites: LngLatBounds };

/** Satélite con una figura marcada en rojo encima (el contorno y, si hay, un punto). */
function estiloConFigura(contorno: GeoJSON.Polygon, punto: [number, number] | null): StyleSpecification {
  return {
    version: 8,
    sources: {
      satelite: { type: "raster", tiles: [SATELITE], tileSize: 256, maxzoom: 19 },
      contorno: { type: "geojson", data: { type: "Feature", properties: {}, geometry: contorno } },
      punto: {
        type: "geojson",
        data: punto
          ? { type: "Feature", properties: {}, geometry: { type: "Point", coordinates: punto } }
          : { type: "FeatureCollection", features: [] },
      },
    },
    layers: [
      { id: "satelite", type: "raster", source: "satelite" },
      { id: "contorno", type: "line", source: "contorno", paint: { "line-color": SENAL, "line-width": 7 } },
      {
        id: "punto",
        type: "circle",
        source: "punto",
        paint: { "circle-radius": 7, "circle-color": SENAL, "circle-stroke-color": "#ffffff", "circle-stroke-width": 2 },
      },
    ],
  };
}

/**
 * Dibuja el mapa fuera de pantalla y lo devuelve como imagen PNG (data URL).
 * Así la ficha no depende de lo que se esté viendo en el mapa de la app.
 */
async function dibujarFueraDePantalla(estilo: StyleSpecification, vista: Vista): Promise<string> {
  const contenedor = document.createElement("div");
  Object.assign(contenedor.style, {
    position: "fixed",
    left: "-10000px",
    top: "0",
    width: `${ANCHO}px`,
    height: `${ALTO}px`,
  });
  document.body.appendChild(contenedor);

  const mapa = new MapaMapLibre({
    container: contenedor,
    ...("centro" in vista
      ? { center: vista.centro, zoom: vista.zoom }
      : { bounds: vista.limites, fitBoundsOptions: { padding: MARGEN_ZONA_PX, maxZoom: 17 } }),
    interactive: false,
    attributionControl: false,
    canvasContextAttributes: { preserveDrawingBuffer: true },
    style: estilo,
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

/** Vista satelital del punto con su hexágono marcado. */
export function imagenDelPunto(lat: number, lon: number, h3: string): Promise<string> {
  const hexagono: GeoJSON.Polygon = { type: "Polygon", coordinates: [cellToBoundary(h3, true)] };
  return dibujarFueraDePantalla(estiloConFigura(hexagono, [lon, lat]), { centro: [lon, lat], zoom: ZOOM_PUNTO });
}

/** Vista satelital de una zona dibujada, encuadrada con un margen. */
export function imagenDeZona(zona: GeoJSON.Polygon): Promise<string> {
  const limites = new LngLatBounds();
  for (const [lon, lat] of zona.coordinates[0] ?? []) {
    if (lon !== undefined && lat !== undefined) limites.extend([lon, lat]);
  }
  return dibujarFueraDePantalla(estiloConFigura(zona, null), { limites });
}
