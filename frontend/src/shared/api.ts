import type { Capa, FichaPunto, ResultadoBusqueda, ResumenPrecios } from "./tipos";

export class ErrorApi extends Error {
  constructor(
    mensaje: string,
    readonly estado: number,
  ) {
    super(mensaje);
  }
}

async function obtener<T>(ruta: string, parametros: Record<string, string | number> = {}): Promise<T> {
  const consulta = new URLSearchParams(Object.entries(parametros).map(([k, v]) => [k, String(v)]));
  const respuesta = await fetch(`/api/${ruta}${consulta.size ? `?${consulta}` : ""}`);
  if (!respuesta.ok) {
    const cuerpo = (await respuesta.json().catch(() => null)) as { detail?: string } | null;
    throw new ErrorApi(cuerpo?.detail ?? "No se pudo obtener la información.", respuesta.status);
  }
  return (await respuesta.json()) as T;
}

export const api = {
  capa: () => obtener<Capa>("capa"),
  comunas: () => obtener<GeoJSON.FeatureCollection>("comunas"),
  punto: (lat: number, lon: number) => obtener<FichaPunto>("punto", { lat, lon }),
  precios: (lat: number, lon: number) => obtener<ResumenPrecios>("precios", { lat, lon }),
  buscar: (q: string) => obtener<ResultadoBusqueda[]>("buscar", { q }),
  direccion: (lat: number, lon: number) =>
    obtener<{ direccion: string | null }>("direccion", { lat, lon }),
};
