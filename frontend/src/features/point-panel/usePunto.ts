import { useCallback, useEffect, useState } from "react";
import { api, ErrorApi } from "../../shared/api";
import type { FichaPunto } from "../../shared/tipos";
import type { EstadoPrecios } from "./Precios";

export interface Punto {
  lat: number;
  lon: number;
}

export type EstadoFicha =
  | { tipo: "vacio" }
  | { tipo: "cargando" }
  | { tipo: "listo"; ficha: FichaPunto }
  | { tipo: "error"; mensaje: string };

/** Un resultado recuerda a qué punto pertenece: si el punto cambió, el resultado ya no vale. */
interface De<T> {
  punto: Punto;
  valor: T;
}

function mensaje(e: unknown, porDefecto: string): string {
  return e instanceof ErrorApi ? e.message : porDefecto;
}

/** Todo lo que se consulta al tocar un punto: ficha, dirección y (a pedido) precios. */
export function usePunto(punto: Punto | null) {
  const [ficha, setFicha] = useState<De<EstadoFicha> | null>(null);
  const [direccion, setDireccion] = useState<De<string | null> | null>(null);
  const [precios, setPrecios] = useState<De<EstadoPrecios> | null>(null);

  useEffect(() => {
    if (!punto) return;
    let vigente = true;
    api
      .punto(punto.lat, punto.lon)
      .then((f) => vigente && setFicha({ punto, valor: { tipo: "listo", ficha: f } }))
      .catch(
        (e: unknown) =>
          vigente &&
          setFicha({ punto, valor: { tipo: "error", mensaje: mensaje(e, "Sin conexión con la API.") } }),
      );
    api
      .direccion(punto.lat, punto.lon)
      .then((r) => vigente && setDireccion({ punto, valor: r.direccion }))
      .catch(() => undefined);
    return () => {
      vigente = false;
    };
  }, [punto]);

  const consultarPrecios = useCallback(() => {
    if (!punto) return;
    setPrecios({ punto, valor: { tipo: "cargando" } });
    api
      .precios(punto.lat, punto.lon)
      .then((resumen) => setPrecios({ punto, valor: { tipo: "listo", resumen } }))
      .catch((e: unknown) =>
        setPrecios({
          punto,
          valor: { tipo: "error", mensaje: mensaje(e, "No se pudieron obtener los precios.") },
        }),
      );
  }, [punto]);

  return {
    ficha: !punto
      ? ({ tipo: "vacio" } as const)
      : ficha?.punto === punto
        ? ficha.valor
        : ({ tipo: "cargando" } as const),
    direccion: direccion?.punto === punto ? direccion.valor : null,
    precios: precios?.punto === punto ? precios.valor : ({ tipo: "inicial" } as const),
    consultarPrecios,
  };
}
