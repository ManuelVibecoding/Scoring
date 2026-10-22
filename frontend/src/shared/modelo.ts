// Dimensiones del modelo (espejo de backend/src/score/domain/modelo.py), para nombrarlas
// donde la API solo entrega el id: la capa de calor y el informe de una zona.

export interface DimensionModelo {
  id: string;
  nombre: string;
}

export const DIMENSIONES: readonly DimensionModelo[] = [
  { id: "seguridad", nombre: "Seguridad" },
  { id: "socioeconomico", nombre: "Entorno socioeconómico" },
  { id: "servicios", nombre: "Servicios cercanos" },
  { id: "transporte", nombre: "Transporte público" },
  { id: "conectividad", nombre: "Conectividad vial" },
  { id: "areas_verdes", nombre: "Áreas verdes" },
  { id: "entorno", nombre: "Tranquilidad del entorno" },
];

export const LETRAS = ["A", "B", "C", "D", "E"] as const;

export function nombreVariable(id: string): string {
  return id === "puntaje" ? "Puntaje total" : (DIMENSIONES.find((d) => d.id === id)?.nombre ?? id);
}
