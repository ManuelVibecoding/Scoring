import { useEffect, useRef, useState } from "react";
import type { FichaPunto, ResumenPrecios } from "../../shared/tipos";
import { nombrePropio } from "../../shared/formato";
import { Ficha } from "./Ficha";
import { ANCHO_FICHA, descargarPdf, descargarPng, descargarPptx, fichaComoPng, nombreArchivo } from "./exportar";
import { imagenDelPunto } from "./imagenDelPunto";
import "./dialogo.css";

interface Props {
  ficha: FichaPunto;
  direccion: string | null;
  precios: ResumenPrecios | null;
  cargandoPrecios: boolean;
  onCerrar: () => void;
}

type Formato = "png" | "pdf" | "pptx";

/** Vista previa de la ficha 16:9 y descarga en PNG, PDF o PowerPoint. */
export function DialogoExportar({ ficha, direccion, precios, cargandoPrecios, onCerrar }: Props) {
  const nodoFicha = useRef<HTMLDivElement>(null);
  const marco = useRef<HTMLDivElement>(null);
  const [imagen, setImagen] = useState<string | null>(null);
  const [cargandoImagen, setCargandoImagen] = useState(true);
  const [escala, setEscala] = useState(0.5);
  const [generando, setGenerando] = useState<Formato | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    imagenDelPunto(ficha.lat, ficha.lon, ficha.h3)
      .then((i) => vigente && setImagen(i))
      .catch(() => vigente && setImagen(null))
      .finally(() => vigente && setCargandoImagen(false));
    return () => {
      vigente = false;
    };
  }, [ficha]);

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
      const nombre = nombreArchivo(ficha.comuna, ficha.puntaje);
      if (formato === "png") descargarPng(png, nombre);
      if (formato === "pdf") await descargarPdf(png, nombre);
      if (formato === "pptx") await descargarPptx(png, nombre, `Score · ${nombrePropio(ficha.comuna)}`);
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
          <h2 id="titulo-exportar">Exportar ficha</h2>
          <button type="button" className="dialogo-cerrar" onClick={onCerrar} aria-label="Cerrar">
            ×
          </button>
        </header>

        <div className="dialogo-marco" ref={marco} style={{ height: `${900 * escala}px` }}>
          <div className="dialogo-escala" style={{ transform: `scale(${escala})` }}>
            <Ficha ref={nodoFicha} ficha={ficha} direccion={direccion} imagen={imagen} precios={precios} />
          </div>
        </div>

        <footer className="dialogo-pie">
          <p className="dialogo-nota">
            {cargandoImagen
              ? "Cargando la imagen satelital…"
              : cargandoPrecios
                ? "Consultando los arriendos cercanos para incluirlos…"
                : precios
                  ? "16:9, lista para una presentación."
                  : "Sin arriendos para incluir: la ficha sale sin precios."}
            {error && <span className="dialogo-error"> {error}</span>}
          </p>
          <div className="dialogo-botones">
            {(["png", "pdf", "pptx"] as const).map((f) => (
              <button
                key={f}
                type="button"
                className={f === "pptx" ? "boton-principal" : "boton-secundario"}
                disabled={cargandoImagen || cargandoPrecios || generando !== null}
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
