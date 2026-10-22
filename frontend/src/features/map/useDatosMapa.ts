import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../shared/api";
import type { Superficie } from "../../shared/tipos";
import { VACIO } from "./capas";

/** Capas de lugares que se pueden prender, cada una con sus categorías del catálogo. */
export const GRUPOS_LUGARES = [
  { id: "metro", nombre: "Metro y tren", categorias: ["metro", "tren"] },
  { id: "colegio", nombre: "Colegios", categorias: ["colegio"] },
  { id: "salud", nombre: "Salud", categorias: ["cesfam", "urgencia", "hospital_clinica"] },
  { id: "supermercado", nombre: "Supermercados", categorias: ["supermercado"] },
] as const;

export type GrupoLugares = (typeof GRUPOS_LUGARES)[number]["id"];

const ETIQUETA_CATEGORIA: Record<string, string> = {
  metro: "Estación de Metro",
  tren: "Estación de tren",
  colegio: "Colegio",
  cesfam: "CESFAM",
  urgencia: "Urgencia",
  hospital_clinica: "Hospital o clínica",
  supermercado: "Supermercado",
};

export interface OpcionesDatos {
  lugares: readonly GrupoLugares[];
  avisos: boolean;
}

type Coleccion = GeoJSON.FeatureCollection<GeoJSON.Point>;

/** Agrega a cada aviso su precio por m² (lo usa el color de la capa). */
function conPrecioPorM2(avisos: Coleccion): Coleccion {
  return {
    ...avisos,
    features: avisos.features.map((f) => {
      const p = f.properties ?? {};
      const precio = Number(p.precio_clp);
      const superficie = Number(p.superficie_m2);
      return { ...f, properties: { ...p, clp_m2: superficie > 0 ? precio / superficie : null } };
    }),
  };
}

function conGrupo(grupo: GrupoLugares, lugares: Coleccion): Coleccion {
  return {
    ...lugares,
    features: lugares.features.map((f) => {
      const categoria = String(f.properties?.categoria ?? "");
      return { ...f, properties: { ...f.properties, grupo, etiqueta: ETIQUETA_CATEGORIA[categoria] ?? categoria } };
    }),
  };
}

/**
 * Datos de referencia del mapa: contorno de comunas y capa de calor al partir; lugares y
 * avisos recién cuando se prenden (y una sola vez: después quedan guardados).
 */
export function useDatosMapa({ lugares, avisos }: OpcionesDatos) {
  const [superficie, setSuperficie] = useState<Superficie | null>(null);
  const [comunas, setComunas] = useState<GeoJSON.FeatureCollection>(VACIO);
  const [porGrupo, setPorGrupo] = useState<Partial<Record<GrupoLugares, Coleccion>>>({});
  const [todosLosAvisos, setTodosLosAvisos] = useState<Coleccion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pedidos = useRef(new Set<string>());

  useEffect(() => {
    Promise.all([api.superficie(), api.comunas()])
      .then(([s, c]) => {
        setSuperficie(s);
        setComunas(c);
      })
      .catch(() => setError("No se pudo conectar con la API. ¿Está corriendo el backend?"));
  }, []);

  useEffect(() => {
    for (const grupo of GRUPOS_LUGARES) {
      if (!lugares.includes(grupo.id) || pedidos.current.has(grupo.id)) continue;
      pedidos.current.add(grupo.id);
      api
        .lugares(grupo.categorias)
        .then((datos) => setPorGrupo((previo) => ({ ...previo, [grupo.id]: conGrupo(grupo.id, datos) })))
        .catch(() => {
          pedidos.current.delete(grupo.id);
          setError(`No se pudieron cargar los lugares (${grupo.nombre}).`);
        });
    }
  }, [lugares]);

  useEffect(() => {
    if (!avisos || pedidos.current.has("avisos")) return;
    pedidos.current.add("avisos");
    api
      .avisos()
      .then((datos) => setTodosLosAvisos(conPrecioPorM2(datos)))
      .catch(() => {
        pedidos.current.delete("avisos");
        setError("No se pudieron cargar los avisos de arriendo.");
      });
  }, [avisos]);

  const lugaresVisibles = useMemo<GeoJSON.FeatureCollection>(
    () => ({
      type: "FeatureCollection",
      features: lugares.flatMap((g) => porGrupo[g]?.features ?? []),
    }),
    [lugares, porGrupo],
  );

  return {
    superficie,
    comunas,
    lugares: lugaresVisibles,
    avisos: avisos && todosLosAvisos ? todosLosAvisos : VACIO,
    cantidadAvisos: todosLosAvisos?.features.length ?? null,
    cargandoLugares: lugares.some((g) => !porGrupo[g]),
    cargandoAvisos: avisos && !todosLosAvisos,
    error,
    cerrarError: () => setError(null),
  };
}
