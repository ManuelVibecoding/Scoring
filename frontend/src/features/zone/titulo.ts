import { enumerar, nombrePropio } from "../../shared/formato";
import type { InformeZona } from "../../shared/tipos";

/** "Zona en Ñuñoa", "Zona en Ñuñoa y Providencia" o "Zona en Ñuñoa y 3 comunas más". */
export function tituloZona(informe: InformeZona): string {
  const comunas = Object.keys(informe.resumen.comunas).map(nombrePropio);
  if (comunas.length <= 2) return `Zona en ${enumerar(comunas)}`;
  return `Zona en ${comunas[0] ?? ""} y ${comunas.length - 1} comunas más`;
}
