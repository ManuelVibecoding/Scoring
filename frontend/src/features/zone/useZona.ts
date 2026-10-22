import { useEffect, useState } from "react";
import { api, ErrorApi } from "../../shared/api";
import type { InformeZona } from "../../shared/tipos";

export type EstadoZona =
  | { tipo: "vacio" }
  | { tipo: "cargando" }
  | { tipo: "listo"; informe: InformeZona }
  | { tipo: "error"; mensaje: string };

/** Informe de la zona dibujada; un resultado viejo no pisa el de una zona más nueva. */
export function useZona(geometria: GeoJSON.Polygon | null): EstadoZona {
  const [resultado, setResultado] = useState<{ de: GeoJSON.Polygon; estado: EstadoZona } | null>(null);

  useEffect(() => {
    if (!geometria) return;
    let vigente = true;
    api
      .zona(geometria)
      .then((informe) => vigente && setResultado({ de: geometria, estado: { tipo: "listo", informe } }))
      .catch(
        (e: unknown) =>
          vigente &&
          setResultado({
            de: geometria,
            estado: { tipo: "error", mensaje: e instanceof ErrorApi ? e.message : "Sin conexión con la API." },
          }),
      );
    return () => {
      vigente = false;
    };
  }, [geometria]);

  if (!geometria) return { tipo: "vacio" };
  return resultado?.de === geometria ? resultado.estado : { tipo: "cargando" };
}
