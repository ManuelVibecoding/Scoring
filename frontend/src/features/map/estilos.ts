import type { StyleSpecification } from "maplibre-gl";

export type EstiloBase = "mapa" | "gris" | "satelite";

// OpenFreeMap: estilos vectoriales gratuitos con datos de OpenStreetMap.
const LIBERTY = "https://tiles.openfreemap.org/styles/liberty";
const POSITRON = "https://tiles.openfreemap.org/styles/positron";

// Imagen satelital de Esri (gratuita con atribución), con nombres de calles encima.
const SATELITE: StyleSpecification = {
  version: 8,
  glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
  sources: {
    satelite: {
      type: "raster",
      tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
      tileSize: 256,
      maxzoom: 19,
      attribution: "Imagen © Esri, Maxar, Earthstar Geographics",
    },
    etiquetas: {
      type: "raster",
      tiles: [
        "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}",
      ],
      tileSize: 256,
      maxzoom: 19,
    },
  },
  layers: [
    { id: "satelite", type: "raster", source: "satelite" },
    { id: "etiquetas", type: "raster", source: "etiquetas", paint: { "raster-opacity": 0.7 } },
  ],
};

export const ESTILOS: Record<EstiloBase, string | StyleSpecification> = {
  mapa: LIBERTY,
  gris: POSITRON,
  satelite: SATELITE,
};

export const NOMBRES_ESTILO: Record<EstiloBase, string> = {
  mapa: "Mapa",
  gris: "Gris",
  satelite: "Satélite",
};
