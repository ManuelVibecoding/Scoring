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
    fuente: string;
    tipo: "departamento" | "casa";
    precio_clp: number | null;
    superficie_m2: number | null;
    dormitorios: number | null;
    url: string;
  };
  distancia_m: number;
}

export interface EstadisticasPrecios {
  avisos: number;
  mediana_arriendo_clp: number | null;
  mediana_clp_m2: number | null;
  mediana_por_dormitorios: Record<string, number>;
  por_fuente: Record<string, number>;
}

export interface ResumenPrecios extends EstadisticasPrecios {
  radio_m: number;
  ejemplos: AvisoCercano[];
  actualizado: string | null;
  fuentes: string[];
}

/** Capa de calor: imágenes georreferenciadas con estas cuatro esquinas, una por variable. */
export interface Superficie {
  esquinas: [[number, number], [number, number], [number, number], [number, number]];
  variables: string[];
}

/** Promedios de una zona dibujada, ponderados por población. */
export interface ResumenZona {
  hexagonos: number;
  personas: number;
  hogares: number;
  viviendas: number;
  puntaje: number | null;
  letra: Letra | null;
  rango_puntaje: [number, number] | null;
  distribucion_letras: Partial<Record<Letra, number>>;
  dimensiones: Record<string, number | null>;
  fortalezas: string[];
  debilidades: string[];
  comunas: Record<string, number>;
}

export interface InformeZona {
  area_km2: number;
  resumen: ResumenZona;
  veredicto: string;
  lugares: { id: string; etiqueta: string; cantidad: number }[];
  precios: EstadisticasPrecios;
}

export interface ResultadoBusqueda {
  nombre: string;
  lat: number;
  lon: number;
}
