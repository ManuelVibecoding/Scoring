import { describe, expect, it } from "vitest";
import type { FichaPunto } from "../../shared/tipos";
import { bloquesDeComparacion, type Fila, mejores } from "./comparacion";

function ficha(puntaje: number, metro: number | null): FichaPunto {
  return {
    h3: "89b2c",
    lat: -33.45,
    lon: -70.6,
    distancia_al_hexagono_m: 0,
    cut: 13120,
    comuna: "ÑUÑOA",
    puntaje,
    letra: "B",
    percentil_rm: 80,
    percentil_comuna: 50,
    veredicto: "",
    fortalezas: [],
    debilidades: [],
    dimensiones: [
      { id: "seguridad", nombre: "Seguridad", peso: 20, nivel: "mixto", puntaje: puntaje - 5, indicadores: [] },
    ],
    cercanias: [{ id: "metro", etiqueta: "Metro", modo: "pie", minutos: metro, lugar: null }],
    barrio: {},
    datos_comunales: [{ etiqueta: "Homicidios", valor: 2.1, unidad: "por 100 mil" }],
    version_modelo: "v1",
  };
}

const fila = (sentido: Fila["sentido"], valores: (number | null)[]): Fila => ({
  id: "x",
  etiqueta: "x",
  sentido,
  formato: "numero",
  valores,
});

describe("mejores", () => {
  it("marca el máximo cuando más es mejor y el mínimo cuando menos es mejor", () => {
    expect(mejores(fila("mayor", [60, 82, 75]))).toEqual([1]);
    expect(mejores(fila("menor", [12, 4, null]))).toEqual([1]);
  });

  it("no marca nada si todos empatan, si falta comparación o si la fila es neutra", () => {
    expect(mejores(fila("mayor", [70, 70]))).toEqual([]);
    expect(mejores(fila("mayor", [70, null]))).toEqual([]);
    expect(mejores(fila("neutro", [500_000, 700_000]))).toEqual([]);
  });

  it("marca todos los empatados en el mejor valor", () => {
    expect(mejores(fila("menor", [3, 3, 9]))).toEqual([0, 1]);
  });
});

describe("bloquesDeComparacion", () => {
  it("arma una fila por medida con un valor por punto y omite las filas vacías", () => {
    const bloques = bloquesDeComparacion(
      [
        { ficha: ficha(70, 6), direccion: null },
        { ficha: ficha(85, null), direccion: "Irarrázaval 3000" },
      ],
      [null, null],
    );
    const titulos = bloques.map((b) => b.titulo);
    expect(titulos).toEqual(["Puntaje", "A pie", "En auto", "Arriendos a 800 m", "Comuna"]);
    const puntaje = bloques[0]?.filas.find((f) => f.id === "puntaje");
    expect(puntaje?.valores).toEqual([70, 85]);
    expect(bloques[1]?.filas.map((f) => f.valores)).toEqual([[6, null]]);
    expect(bloques[2]?.filas).toEqual([]);
    expect(bloques[3]?.filas).toEqual([]);
    expect(bloques[4]?.filas[0]?.unidad).toBe("por 100 mil");
  });
});
