import { describe, expect, it } from "vitest";
import {
  conUnidad,
  enumerar,
  minutos,
  nombreFuente,
  nombreLugar,
  nombrePropio,
  numero,
  pesos,
  porcentaje,
} from "./formato";

describe("formato es-CL", () => {
  it("usa punto de miles y coma decimal", () => {
    expect(numero(241467)).toBe("241.467");
    expect(numero(12.34, 1)).toBe("12,3");
    expect(pesos(659198)).toBe("$659.198");
    expect(porcentaje(0.0571)).toBe("5,7%");
  });

  it("muestra guion cuando no hay dato", () => {
    expect(numero(null)).toBe("—");
    expect(minutos(null)).toBe("—");
  });

  it("formatea minutos", () => {
    expect(minutos(0.4)).toBe("<1 min");
    expect(minutos(7.1)).toBe("7 min");
    expect(minutos(65)).toBe("1 h 05 min");
  });

  it("formatea según la unidad del indicador", () => {
    expect(conUnidad(0.12, "%")).toBe("12,0%");
    expect(conUnidad(3.24, "por 100 mil")).toBe("3,2 por 100 mil");
    expect(conUnidad("Alto", "nivel")).toBe("Alto");
  });

  it("normaliza nombres de lugares", () => {
    expect(nombreLugar("ESCUELA BÁSICA JOSÉ TORIBIO MEDINA")).toBe("Escuela Básica José Toribio Medina");
    expect(nombreLugar("Plaza Ñuñoa")).toBe("Plaza Ñuñoa");
    expect(nombreLugar(null)).toBe("sin nombre");
    expect(nombreLugar("  ")).toBe("sin nombre");
  });

  it("escribe nombres propios de comunas", () => {
    expect(nombrePropio("ÑUÑOA")).toBe("Ñuñoa");
    expect(nombrePropio("SAN JOSÉ DE MAIPO")).toBe("San José de Maipo");
    expect(nombrePropio("LA FLORIDA")).toBe("La Florida");
  });

  it("nombra las fuentes de avisos y enumera en español", () => {
    expect(nombreFuente("portalinmobiliario")).toBe("Portal Inmobiliario");
    expect(nombreFuente("otra")).toBe("otra");
    expect(enumerar(["Toc Toc"])).toBe("Toc Toc");
    expect(enumerar(["a", "b", "c"])).toBe("a, b y c");
  });
});
