import type { GeoJSONSource, ImageSource, Map as MapaMapLibre } from "maplibre-gl";
import { COLOR_LUGAR, GRIS, PAPEL, SENAL, TINTA } from "../../styles/tokens";

// Capas propias de la app, independientes del mapa base. Al cambiar el mapa base
// (setStyle) MapLibre las borra: `asegurarCapas` las vuelve a crear con su último estado.

export const VACIO: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };

export interface Calor {
  url: string;
  esquinas: [[number, number], [number, number], [number, number], [number, number]];
  opacidad: number;
}

export interface EstadoCapas {
  calor: Calor | null;
  isocrona: GeoJSON.FeatureCollection;
  zona: GeoJSON.FeatureCollection;
  medicion: GeoJSON.FeatureCollection;
  lugares: GeoJSON.FeatureCollection;
  avisos: GeoJSON.FeatureCollection;
  marcador: GeoJSON.FeatureCollection;
  comparados: GeoJSON.FeatureCollection;
  comunas: GeoJSON.FeatureCollection;
}

export const FUENTES_GEOJSON = ["isocrona", "zona", "medicion", "lugares", "avisos", "marcador", "comparados", "comunas"] as const;
export type FuenteGeoJSON = (typeof FUENTES_GEOJSON)[number];

function primeraEtiqueta(m: MapaMapLibre): string | undefined {
  return m.getStyle().layers.find((c) => c.type === "symbol")?.id;
}

/**
 * Crea fuentes y capas que falten (después de cargar o cambiar el mapa base).
 * Sobre la imagen satelital los contornos van en blanco: el negro no se ve.
 */
export function asegurarCapas(m: MapaMapLibre, estado: EstadoCapas, sobreImagen = false) {
  const contorno = sobreImagen ? PAPEL : TINTA;
  const debajoDeEtiquetas = primeraEtiqueta(m);
  for (const id of FUENTES_GEOJSON) {
    if (!m.getSource(id)) m.addSource(id, { type: "geojson", data: estado[id] });
  }
  if (!m.getLayer("comunas")) {
    m.addLayer(
      {
        id: "comunas",
        type: "line",
        source: "comunas",
        paint: {
          "line-color": contorno,
          "line-opacity": 0.55,
          "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.5, 14, 1.4],
          "line-dasharray": [3, 2],
        },
      },
      debajoDeEtiquetas,
    );
  }
  ponerCalor(m, estado.calor);
  if (!m.getLayer("isocrona")) {
    m.addLayer(
      {
        id: "isocrona",
        type: "fill",
        source: "isocrona",
        paint: {
          "fill-color": SENAL,
          "fill-opacity": ["match", ["get", "minutos"], 5, 0.22, 10, 0.14, 0.08],
        },
      },
      debajoDeEtiquetas,
    );
    m.addLayer({
      id: "isocrona-borde",
      type: "line",
      source: "isocrona",
      paint: { "line-color": SENAL, "line-width": 1.2, "line-opacity": 0.8 },
    });
  }
  if (!m.getLayer("zona")) {
    m.addLayer({ id: "zona", type: "fill", source: "zona", paint: { "fill-color": contorno, "fill-opacity": 0.08 } });
    m.addLayer({
      id: "zona-borde",
      type: "line",
      source: "zona",
      paint: { "line-color": contorno, "line-width": 2.5 },
    });
  }
  if (!m.getLayer("medicion")) {
    m.addLayer({
      id: "medicion-halo",
      type: "line",
      source: "medicion",
      paint: { "line-color": PAPEL, "line-width": 7 },
    });
    m.addLayer({
      id: "medicion",
      type: "line",
      source: "medicion",
      paint: { "line-color": SENAL, "line-width": 3, "line-dasharray": [2, 1] },
    });
  }
  if (!m.getLayer("avisos")) {
    m.addLayer({
      id: "avisos",
      type: "circle",
      source: "avisos",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 11, 2.5, 16, 6],
        // Más oscuro = más caro por m².
        "circle-color": [
          "interpolate",
          ["linear"],
          ["coalesce", ["get", "clp_m2"], 0],
          6000,
          "#D9D9D9",
          12000,
          GRIS,
          20000,
          TINTA,
        ],
        "circle-stroke-color": PAPEL,
        "circle-stroke-width": 1,
      },
    });
  }
  if (!m.getLayer("lugares")) {
    m.addLayer({
      id: "lugares",
      type: "circle",
      source: "lugares",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 11, 3.5, 16, 7],
        "circle-color": [
          "match",
          ["get", "grupo"],
          "metro",
          COLOR_LUGAR.metro ?? SENAL,
          "colegio",
          COLOR_LUGAR.colegio ?? TINTA,
          "salud",
          COLOR_LUGAR.salud ?? TINTA,
          COLOR_LUGAR.supermercado ?? GRIS,
        ],
        "circle-stroke-color": PAPEL,
        "circle-stroke-width": 1.5,
      },
    });
  }
  if (!m.getLayer("comparados")) {
    m.addLayer({
      id: "comparados",
      type: "circle",
      source: "comparados",
      paint: { "circle-radius": 10, "circle-color": TINTA, "circle-stroke-color": PAPEL, "circle-stroke-width": 2 },
    });
    m.addLayer({
      id: "comparados-numero",
      type: "symbol",
      source: "comparados",
      layout: {
        "text-field": ["to-string", ["get", "numero"]],
        "text-font": ["Noto Sans Bold"],
        "text-size": 12,
        "text-allow-overlap": true,
        "text-ignore-placement": true,
      },
      paint: { "text-color": PAPEL },
    });
  }
  if (!m.getLayer("marcador")) {
    // Anillo negro alrededor: el punto elegido no se confunde con una estación de Metro.
    m.addLayer({
      id: "marcador-anillo",
      type: "circle",
      source: "marcador",
      paint: { "circle-radius": 13, "circle-opacity": 0, "circle-stroke-color": TINTA, "circle-stroke-width": 2.5 },
    });
    m.addLayer({
      id: "marcador",
      type: "circle",
      source: "marcador",
      paint: {
        "circle-radius": 7,
        "circle-color": SENAL,
        "circle-stroke-color": PAPEL,
        "circle-stroke-width": 2.5,
      },
    });
  }
}

export function ponerDatos(m: MapaMapLibre, fuente: FuenteGeoJSON, datos: GeoJSON.FeatureCollection) {
  (m.getSource(fuente) as GeoJSONSource | undefined)?.setData(datos);
}

/** La capa de calor es una imagen georreferenciada; se crea, actualiza o quita. */
export function ponerCalor(m: MapaMapLibre, calor: Calor | null, anterior: Calor | null = null) {
  const fuente = m.getSource("calor") as ImageSource | undefined;
  if (!calor) {
    if (m.getLayer("calor")) m.removeLayer("calor");
    if (fuente) m.removeSource("calor");
    return;
  }
  if (fuente) {
    // Cambiar solo la intensidad no vuelve a pedir la imagen.
    if (anterior?.url !== calor.url) fuente.updateImage({ url: calor.url, coordinates: calor.esquinas });
  } else {
    m.addSource("calor", { type: "image", url: calor.url, coordinates: calor.esquinas });
  }
  if (!m.getLayer("calor")) {
    m.addLayer(
      {
        id: "calor",
        type: "raster",
        source: "calor",
        paint: { "raster-opacity": calor.opacidad, "raster-resampling": "linear", "raster-fade-duration": 0 },
      },
      m.getLayer("comunas") ? "comunas" : primeraEtiqueta(m),
    );
  } else {
    m.setPaintProperty("calor", "raster-opacity", calor.opacidad);
  }
}

export function punto(lat: number, lon: number): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: [{ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: [lon, lat] } }],
  };
}
