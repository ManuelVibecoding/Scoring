import { toPng } from "html-to-image";

export const ANCHO_FICHA = 1600;
export const ALTO_FICHA = 900;
const RESOLUCION = 1.5; // 2400 × 1350 px: nítida en una presentación a pantalla completa.

export async function fichaComoPng(nodo: HTMLElement): Promise<string> {
  // Se espera a que la tipografía esté cargada para que la imagen no salga con otra fuente.
  await document.fonts.ready;
  return toPng(nodo, {
    width: ANCHO_FICHA,
    height: ALTO_FICHA,
    pixelRatio: RESOLUCION,
    backgroundColor: "#ffffff",
    style: { transform: "none" },
  });
}

function descargar(url: string, nombre: string) {
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre;
  enlace.click();
}

export function descargarPng(png: string, nombre: string) {
  descargar(png, `${nombre}.png`);
}

export async function descargarPdf(png: string, nombre: string) {
  const { jsPDF } = await import("jspdf");
  const pdf = new jsPDF({ orientation: "landscape", unit: "px", format: [ANCHO_FICHA, ALTO_FICHA] });
  pdf.addImage(png, "PNG", 0, 0, ANCHO_FICHA, ALTO_FICHA);
  pdf.save(`${nombre}.pdf`);
}

export async function descargarPptx(png: string, nombre: string, titulo: string) {
  const { default: PptxGenJS } = await import("pptxgenjs");
  const presentacion = new PptxGenJS();
  presentacion.layout = "LAYOUT_WIDE"; // 13,33 × 7,5 pulgadas = 16:9
  presentacion.title = titulo;
  const lamina = presentacion.addSlide();
  lamina.addImage({ data: png, x: 0, y: 0, w: 13.333, h: 7.5, altText: titulo });
  await presentacion.writeFile({ fileName: `${nombre}.pptx` });
}

/** "score-nunoa-85" para nombrar los archivos. */
export function nombreArchivo(comuna: string, puntaje: number | null): string {
  const base = comuna
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
  return `score-${base}-${puntaje == null ? "sd" : Math.round(puntaje)}`;
}
