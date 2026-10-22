// Formatos en español de Chile: punto de miles, coma decimal.

const entero = new Intl.NumberFormat("es-CL", { maximumFractionDigits: 0 });
const unDecimal = new Intl.NumberFormat("es-CL", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export const SIN_DATO = "—";

export function numero(valor: number | null | undefined, decimales: 0 | 1 = 0): string {
  if (valor == null || Number.isNaN(valor)) return SIN_DATO;
  return (decimales === 1 ? unDecimal : entero).format(valor);
}

export function pesos(valor: number | null | undefined): string {
  return valor == null ? SIN_DATO : `$${numero(valor)}`;
}

export function porcentaje(fraccion: number | null | undefined): string {
  return fraccion == null ? SIN_DATO : `${numero(fraccion * 100, 1)}%`;
}

/** "4 min", "1 h 05 min"; sin dato si no se llega. */
export function minutos(valor: number | null | undefined): string {
  if (valor == null) return SIN_DATO;
  const total = Math.round(valor);
  if (total < 1) return "<1 min";
  if (total < 60) return `${total} min`;
  return `${Math.floor(total / 60)} h ${String(total % 60).padStart(2, "0")} min`;
}

/** Valor de un indicador según su unidad, listo para mostrar. */
export function conUnidad(valor: number | string | null, unidad: string): string {
  if (valor == null) return SIN_DATO;
  if (typeof valor === "string") return valor;
  switch (unidad) {
    case "%":
      return porcentaje(valor);
    case "min":
      return minutos(valor);
    case "m":
      return `${numero(valor)} m`;
    case "años":
      return `${numero(valor, 1)} años`;
    case "por 100 mil":
    case "por 1.000 hogares":
      return `${numero(valor, 1)} ${unidad}`;
    case "personas":
      return numero(valor);
    default:
      return numero(valor, valor < 10 ? 1 : 0);
  }
}

/** "ÑUÑOA" → "Ñuñoa", "SAN JOSÉ DE MAIPO" → "San José de Maipo". */
export function nombrePropio(texto: string): string {
  const menores = new Set(["de", "del", "la", "las", "los", "y"]);
  return texto
    .toLocaleLowerCase("es-CL")
    .split(/\s+/)
    .map((p, i) => (i > 0 && menores.has(p) ? p : p.charAt(0).toLocaleUpperCase("es-CL") + p.slice(1)))
    .join(" ");
}

/** Nombre de un lugar para mostrar: los que vienen en mayúsculas se pasan a nombre propio. */
export function nombreLugar(nombre: string | null | undefined): string {
  if (!nombre?.trim()) return "sin nombre";
  const tieneLetras = /\p{L}/u.test(nombre);
  return tieneLetras && nombre === nombre.toLocaleUpperCase("es-CL") ? nombrePropio(nombre) : nombre;
}

export function coordenadas(lat: number, lon: number): string {
  return `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
}
