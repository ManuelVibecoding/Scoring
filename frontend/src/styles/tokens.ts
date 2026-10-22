// Valores de tokens.css que se necesitan en JavaScript (el mapa no puede leer variables CSS).
// Si cambias uno aquí, cámbialo también en tokens.css.

export const SENAL = "#E2231A";
export const TINTA = "#111111";
export const PAPEL = "#FFFFFF";
export const GRIS = "#8A8A8A";

/** Escala de la capa de calor (la imagen la genera el backend con estos mismos colores). */
export const ESCALA_CALOR: readonly string[] = ["#E2231A", "#EEE8E2", "#111111"];

/** Colores de las capas de lugares: pocos y sobrios, distinguibles en gris. */
export const COLOR_LUGAR: Readonly<Record<string, string>> = {
  metro: "#E2231A",
  colegio: "#111111",
  salud: "#2F6FDE",
  supermercado: "#8A8A8A",
};

/** Letras de A (mejor) a E (peor): de negro a gris claro, como la escala del puntaje. */
export const COLOR_LETRA: Readonly<Record<string, string>> = {
  A: "#111111",
  B: "#3A3A3A",
  C: "#8A8A8A",
  D: "#BDBDBD",
  E: "#E3E3E3",
};
