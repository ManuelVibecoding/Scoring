import { type ReactNode, useEffect, useRef, useState } from "react";
import { ALTO_FICHA, ANCHO_FICHA, descargarPdf, descargarPng, descargarPptx, fichaComoPng } from "./exportar";

interface Props {
  titulo: string;
  /** Nombre de los archivos, sin extensión. */
  archivo: string;
  tituloPresentacion: string;
  /** Mientras falte algo (imagen, precios) no se puede exportar; se explica en la nota. */
  preparando: string | null;
  nota: string;
  onCerrar: () => void;
  /** La ficha de 1600 × 900 px; se exporta tal cual se ve. */
  children: ReactNode;
}

type Formato = "png" | "pdf" | "pptx";

/** Vista previa de una ficha 16:9 y descarga en PNG, PDF o PowerPoint. */
export function DialogoFicha({ titulo, archivo, tituloPresentacion, preparando, nota, onCerrar, children }: Props) {
  const nodoFicha = useRef<HTMLDivElement>(null);
  const marco = useRef<HTMLDivElement>(null);
  const [escala, setEscala] = useState(0.5);
  const [generando, setGenerando] = useState<Formato | null>(null);
  const [error, setError] = useState<string | null>(null);

  // La vista previa se escala para caber en la ventana; la exportación usa el tamaño real.
  useEffect(() => {
    const elemento = marco.current;
    if (!elemento) return;
    const observador = new ResizeObserver(([entrada]) => {
      if (entrada) setEscala(entrada.contentRect.width / ANCHO_FICHA);
    });
    observador.observe(elemento);
    return () => observador.disconnect();
  }, []);

  useEffect(() => {
    const alPresionar = (e: KeyboardEvent) => e.key === "Escape" && onCerrar();
    window.addEventListener("keydown", alPresionar);
    return () => window.removeEventListener("keydown", alPresionar);
  }, [onCerrar]);

  async function exportar(formato: Formato) {
    if (!nodoFicha.current) return;
    setGenerando(formato);
    setError(null);
    try {
      const png = await fichaComoPng(nodoFicha.current);
      if (formato === "png") descargarPng(png, archivo);
      if (formato === "pdf") await descargarPdf(png, archivo);
      if (formato === "pptx") await descargarPptx(png, archivo, tituloPresentacion);
    } catch {
      setError("No se pudo generar el archivo. Prueba de nuevo.");
    } finally {
      setGenerando(null);
    }
  }

  return (
    <div className="dialogo-fondo" role="dialog" aria-modal="true" aria-labelledby="titulo-exportar">
      <div className="dialogo">
        <header className="dialogo-cabecera">
          <h2 id="titulo-exportar">{titulo}</h2>
          <button type="button" className="dialogo-cerrar" onClick={onCerrar} aria-label="Cerrar">
            ×
          </button>
        </header>

        <div className="dialogo-marco" ref={marco} style={{ height: `${ALTO_FICHA * escala}px` }}>
          <div className="dialogo-escala" style={{ transform: `scale(${escala})` }}>
            <div ref={nodoFicha}>{children}</div>
          </div>
        </div>

        <footer className="dialogo-pie">
          <p className="dialogo-nota">
            {preparando ?? nota}
            {error && <span className="dialogo-error"> {error}</span>}
          </p>
          <div className="dialogo-botones">
            {(["png", "pdf", "pptx"] as const).map((f) => (
              <button
                key={f}
                type="button"
                className={f === "pptx" ? "boton-principal" : "boton-secundario"}
                disabled={preparando !== null || generando !== null}
                onClick={() => void exportar(f)}
              >
                {generando === f ? "Generando…" : f === "pptx" ? "PowerPoint" : f.toUpperCase()}
              </button>
            ))}
          </div>
        </footer>
      </div>
    </div>
  );
}
