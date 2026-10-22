import { describe, expect, it } from "vitest";
import { nombreArchivo } from "./exportar";

describe("nombreArchivo", () => {
  it("quita tildes y espacios", () => {
    expect(nombreArchivo("ÑUÑOA", 85.2)).toBe("score-nunoa-85");
    expect(nombreArchivo("San José de Maipo", 37)).toBe("score-san-jose-de-maipo-37");
  });

  it("marca sin dato", () => {
    expect(nombreArchivo("Alhué", null)).toBe("score-alhue-sd");
  });
});
