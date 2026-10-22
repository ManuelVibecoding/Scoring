import type { FichaPunto, InformeZona, ResultadoBusqueda, ResumenPrecios, Superficie } from "./tipos";

export class ErrorApi extends Error {
  constructor(
    mensaje: string,
    readonly estado: number,
  ) {
    super(mensaje);
  }
}

async function leer<T>(respuesta: Response): Promise<T> {
  if (!respuesta.ok) {
    const cuerpo = (await respuesta.json().catch(() => null)) as { detail?: unknown } | null;
    const detalle = typeof cuerpo?.detail === "string" ? cuerpo.detail : "No se pudo obtener la información.";
    throw new ErrorApi(detalle, respuesta.status);
  }
  return (await respuesta.json()) as T;
}

async function obtener<T>(ruta: string, parametros: Record<string, string | number> = {}): Promise<T> {
  const consulta = new URLSearchParams(Object.entries(parametros).map(([k, v]) => [k, String(v)]));
  return leer<T>(await fetch(`/api/${ruta}${consulta.size ? `?${consulta}` : ""}`));
}

async function enviar<T>(ruta: string, cuerpo: unknown): Promise<T> {
  const respuesta = await fetch(`/api/${ruta}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  return leer<T>(respuesta);
}

export const api = {
  superficie: () => obtener<Superficie>("superficie"),
  urlSuperficie: (variable: string) => `/api/superficie/${encodeURIComponent(variable)}.png`,
  comunas: () => obtener<GeoJSON.FeatureCollection>("comunas"),
  punto: (lat: number, lon: number) => obtener<FichaPunto>("punto", { lat, lon }),
  isocrona: (lat: number, lon: number) => obtener<GeoJSON.FeatureCollection>("isocrona", { lat, lon }),
  precios: (lat: number, lon: number) => obtener<ResumenPrecios>("precios", { lat, lon }),
  zona: (geometria: GeoJSON.Polygon) => enviar<InformeZona>("zona", { geometria }),
  lugares: (categorias: readonly string[]) =>
    obtener<GeoJSON.FeatureCollection<GeoJSON.Point>>("lugares", { categorias: categorias.join(",") }),
  avisos: () => obtener<GeoJSON.FeatureCollection<GeoJSON.Point>>("avisos"),
  buscar: (q: string) => obtener<ResultadoBusqueda[]>("buscar", { q }),
  direccion: (lat: number, lon: number) => obtener<{ direccion: string | null }>("direccion", { lat, lon }),
};
