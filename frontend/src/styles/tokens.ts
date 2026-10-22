// Valores de tokens.css que se necesitan en JavaScript (el mapa no puede leer variables CSS).
// Si cambias uno aquí, cámbialo también en tokens.css.

export const SENAL = "#E2231A";
export const TINTA = "#111111";
export const PAPEL = "#FFFFFF";

/** Escala del mapa por puntaje: de gris claro (peor) a negro (mejor). */
// El extremo claro no es blanco: "sin color" queda reservado para zonas sin viviendas.
export const ESCALA_PUNTAJE: readonly [number, string][] = [
  [20, "#E3E3E3"],
  [45, "#BDBDBD"],
  [62, "#8A8A8A"],
  [78, "#3A3A3A"],
  [92, "#111111"],
];
