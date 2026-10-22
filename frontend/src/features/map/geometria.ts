// Medidas sobre el mapa (distancia de una línea, área de un polígono) sin dependencias.

const RADIO_TIERRA_M = 6_371_000;

function radianes(grados: number): number {
  return (grados * Math.PI) / 180;
}

/** Distancia en metros entre dos puntos [lon, lat] (haversine). */
export function distanciaM([lon1, lat1]: number[], [lon2, lat2]: number[]): number {
  if (lon1 === undefined || lat1 === undefined || lon2 === undefined || lat2 === undefined) return 0;
  const dLat = radianes(lat2 - lat1);
  const dLon = radianes(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(radianes(lat1)) * Math.cos(radianes(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * RADIO_TIERRA_M * Math.asin(Math.sqrt(a));
}

/** Largo total de una línea en metros. */
export function largoM(coordenadas: number[][]): number {
  let total = 0;
  for (let i = 1; i < coordenadas.length; i++) {
    const a = coordenadas[i - 1];
    const b = coordenadas[i];
    if (a && b) total += distanciaM(a, b);
  }
  return total;
}

/** "850 m" o "2,4 km". */
export function formatoDistancia(metros: number): string {
  if (metros < 1000) return `${Math.round(metros)} m`;
  return `${(metros / 1000).toLocaleString("es-CL", { maximumFractionDigits: 1 })} km`;
}
