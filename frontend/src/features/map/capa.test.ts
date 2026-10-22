import { latLngToCell } from "h3-js";
import { describe, expect, it } from "vitest";
import type { Capa } from "../../shared/tipos";
import { colorPorVariable, hexagonosGeoJSON } from "./capa";

describe("hexagonosGeoJSON", () => {
  it("arma un polígono cerrado por hexágono con sus propiedades", () => {
    const h3 = latLngToCell(-33.456, -70.5975, 9);
    const capa: Capa = { h3: [h3], puntaje: [85.2], letra: ["A"], seguridad: [63.4] };

    const [feature] = hexagonosGeoJSON(capa).features;

    expect(feature?.properties).toEqual({ h3, puntaje: 85.2, letra: "A", seguridad: 63.4 });
    const anillo = feature?.geometry.coordinates[0] ?? [];
    expect(anillo).toHaveLength(7);
    expect(anillo[0]).toEqual(anillo[6]);
    // [lng, lat]: la longitud de Santiago es ~-70,6.
    expect(anillo[0]?.[0]).toBeCloseTo(-70.6, 1);
  });
});

describe("colorPorVariable", () => {
  it("interpola la escala y deja transparente lo que no tiene dato", () => {
    const expresion = colorPorVariable("seguridad", [
      [0, "#fff"],
      [100, "#000"],
    ]);
    expect(expresion[2]).toBe("rgba(0,0,0,0)");
    expect(expresion[3]).toEqual(["interpolate", ["linear"], ["get", "seguridad"], 0, "#fff", 100, "#000"]);
  });
});
