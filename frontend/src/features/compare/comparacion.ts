import type { FichaPunto, ResumenPrecios } from "../../shared/tipos";

export const MAXIMO_COMPARADOS = 3;

export interface Comparado {
  ficha: FichaPunto;
  direccion: string | null;
}

/** Hacia dónde es mejor una fila: más puntaje es mejor, más minutos es peor. */
export type Sentido = "mayor" | "menor" | "neutro";

export interface Fila {
  id: string;
  etiqueta: string;
  sentido: Sentido;
  valores: (number | null)[];
  formato: "puntaje" | "minutos" | "pesos" | "porcentaje" | "numero" | "dato";
  /** Unidad del dato comunal (formato "dato"). */
  unidad?: string;
}

export interface Bloque {
  titulo: string;
  filas: Fila[];
}

const CERCANIAS = ["metro", "paradero", "supermercado", "farmacia", "colegio", "cesfam", "plaza", "parque"];
const CERCANIAS_AUTO = ["urgencia", "acceso_autopista", "centro_empleo"];
const DATOS_COMUNA: { etiqueta: string; sentido: Sentido }[] = [
  { etiqueta: "Homicidios", sentido: "menor" },
  { etiqueta: "Pobreza por ingresos", sentido: "menor" },
  { etiqueta: "Escolaridad promedio", sentido: "mayor" },
  { etiqueta: "Delitos de mayor connotación", sentido: "menor" },
];

function numeroOnulo(valor: number | string | null | undefined): number | null {
  return typeof valor === "number" ? valor : null;
}

/**
 * Arma la tabla comparativa (filas en el mismo orden para todos los puntos).
 * Una fila que ningún punto tiene se omite.
 */
export function bloquesDeComparacion(puntos: Comparado[], precios: (ResumenPrecios | null)[]): Bloque[] {
  const fichas = puntos.map((p) => p.ficha);
  const primera = fichas[0];
  if (!primera) return [];

  const cercania = (id: string): Fila | null => {
    const muestra = primera.cercanias.find((c) => c.id === id);
    if (!muestra) return null;
    return {
      id,
      etiqueta: muestra.etiqueta,
      sentido: "menor",
      formato: "minutos",
      valores: fichas.map((f) => f.cercanias.find((c) => c.id === id)?.minutos ?? null),
    };
  };

  const bloques: Bloque[] = [
    {
      titulo: "Puntaje",
      filas: [
        { id: "puntaje", etiqueta: "Puntaje total", sentido: "mayor", formato: "puntaje", valores: fichas.map((f) => f.puntaje) },
        {
          id: "percentil",
          etiqueta: "Mejor que la RM en",
          sentido: "mayor",
          formato: "porcentaje",
          valores: fichas.map((f) => f.percentil_rm),
        },
        ...primera.dimensiones.map(
          (d): Fila => ({
            id: d.id,
            etiqueta: d.nombre,
            sentido: "mayor",
            formato: "puntaje",
            valores: fichas.map((f) => f.dimensiones.find((x) => x.id === d.id)?.puntaje ?? null),
          }),
        ),
      ],
    },
    { titulo: "A pie", filas: CERCANIAS.map(cercania).filter((f) => f !== null) },
    { titulo: "En auto", filas: CERCANIAS_AUTO.map(cercania).filter((f) => f !== null) },
    {
      titulo: "Arriendos a 800 m",
      filas: [
        {
          id: "arriendo",
          etiqueta: "Arriendo mediano",
          sentido: "neutro",
          formato: "pesos",
          valores: precios.map((p) => p?.mediana_arriendo_clp ?? null),
        },
        {
          id: "clp_m2",
          etiqueta: "Por m² al mes",
          sentido: "neutro",
          formato: "pesos",
          valores: precios.map((p) => p?.mediana_clp_m2 ?? null),
        },
        { id: "avisos", etiqueta: "Avisos", sentido: "neutro", formato: "numero", valores: precios.map((p) => p?.avisos ?? null) },
      ],
    },
    {
      titulo: "Comuna",
      filas: DATOS_COMUNA.map(({ etiqueta, sentido }) => ({
        id: etiqueta,
        etiqueta,
        sentido,
        formato: "dato" as const,
        unidad: primera.datos_comunales.find((d) => d.etiqueta === etiqueta)?.unidad ?? "",
        valores: fichas.map((f) => numeroOnulo(f.datos_comunales.find((d) => d.etiqueta === etiqueta)?.valor)),
      })),
    },
  ];
  return bloques.map((b) => ({ ...b, filas: b.filas.filter((f) => f.valores.some((v) => v != null)) }));
}

/** Índices de los puntos con el mejor valor de la fila (puede haber empate); ninguno si es neutra. */
export function mejores(fila: Fila): number[] {
  if (fila.sentido === "neutro") return [];
  const validos = fila.valores.filter((v): v is number => v != null);
  if (validos.length < 2) return [];
  const mejor = fila.sentido === "mayor" ? Math.max(...validos) : Math.min(...validos);
  if (validos.every((v) => v === mejor)) return [];
  return fila.valores.flatMap((v, i) => (v === mejor ? [i] : []));
}
