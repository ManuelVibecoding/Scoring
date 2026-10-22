// Contratos de la API (espejo de backend/src/score/services/consulta_punto.py).

export type Letra = "A" | "B" | "C" | "D" | "E";

export interface Indicador {
  descripcion: string;
  valor: number | null;
  unidad: string;
}

export interface Dimension {
  id: string;
  nombre: string;
  peso: number;
  nivel: "punto" | "comuna" | "mixto";
  puntaje: number | null;
  indicadores: Indicador[];
}

export interface Cercania {
  id: string;
  etiqueta: string;
  modo: "pie" | "auto";
  minutos: number | null;
  lugar: string | null;
}

export interface DatoComunal {
  etiqueta: string;
  valor: number | string | null;
  unidad: string;
}

export interface FichaPunto {
  h3: string;
  lat: number;
  lon: number;
  distancia_al_hexagono_m: number;
  cut: number;
  comuna: string;
  puntaje: number | null;
  letra: Letra | null;
  percentil_rm: number | null;
  percentil_comuna: number | null;
  veredicto: string;
  fortalezas: string[];
  debilidades: string[];
  dimensiones: Dimension[];
  cercanias: Cercania[];
  barrio: Record<string, number | null>;
  datos_comunales: DatoComunal[];
  version_modelo: string;
}

export interface AvisoCercano {
  aviso: {
    id: string;
    tipo: "departamento" | "casa";
    precio_clp: number | null;
    superficie_m2: number | null;
    dormitorios: number | null;
    url: string;
  };
  distancia_m: number;
}

export interface ResumenPrecios {
  radio_m: number;
  avisos: number;
  mediana_arriendo_clp: number | null;
  mediana_clp_m2: number | null;
  mediana_por_dormitorios: Record<string, number>;
  ejemplos: AvisoCercano[];
  actualizado: string | null;
  fuente: string;
}

/** Capa del mapa en formato columnar: una lista por columna. */
export interface Capa {
  h3: string[];
  puntaje: (number | null)[];
  letra: (Letra | null)[];
  [dimension: string]: (number | string | null)[];
}

export interface ResultadoBusqueda {
  nombre: string;
  lat: number;
  lon: number;
}
