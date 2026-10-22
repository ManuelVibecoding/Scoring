import { cellToBoundary } from "h3-js";
import type { ExpressionSpecification } from "maplibre-gl";
import type { Capa } from "../../shared/tipos";

export type Variable = "puntaje" | (string & {});

/** Convierte la capa columnar de la API en polígonos GeoJSON (un hexágono por feature). */
export function hexagonosGeoJSON(capa: Capa): GeoJSON.FeatureCollection<GeoJSON.Polygon> {
  const columnas = Object.keys(capa).filter((c) => c !== "h3");
  return {
    type: "FeatureCollection",
    features: capa.h3.map((h3, i) => {
      // Con `true`, h3-js entrega [lng, lat] y el anillo ya cerrado, como pide GeoJSON.
      const anillo = cellToBoundary(h3, true);
      const propiedades: Record<string, unknown> = { h3 };
      for (const c of columnas) propiedades[c] = capa[c]?.[i] ?? null;
      return {
        type: "Feature",
        id: i,
        properties: propiedades,
        geometry: { type: "Polygon", coordinates: [anillo] },
      };
    }),
  };
}

/** Expresión MapLibre de color según la variable elegida (sin dato → transparente). */
export function colorPorVariable(
  variable: Variable,
  escala: readonly [number, string][],
): ExpressionSpecification {
  const pares = escala.flatMap(([corte, color]) => [corte, color]);
  return [
    "case",
    ["==", ["get", variable], null],
    "rgba(0,0,0,0)",
    ["interpolate", ["linear"], ["get", variable], ...pares],
  ] as ExpressionSpecification;
}
