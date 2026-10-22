import { describe, expect, it } from "vitest";
import { distanciaM, formatoDistancia, largoM } from "./geometria";

describe("geometria", () => {
  it("mide distancias en metros", () => {
    // 0,0009° de latitud ≈ 100 m
    expect(distanciaM([-70.6, -33.45], [-70.6, -33.4509])).toBeCloseTo(100, -0.5);
  });

  it("suma los tramos de una línea", () => {
    const linea = [
      [-70.6, -33.45],
      [-70.6, -33.4509],
      [-70.6, -33.4518],
    ];
    expect(largoM(linea)).toBeCloseTo(200, -0.5);
  });

  it("formatea en metros o kilómetros", () => {
    expect(formatoDistancia(850.4)).toBe("850 m");
    expect(formatoDistancia(2400)).toBe("2,4 km");
  });
});
