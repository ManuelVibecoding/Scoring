import type { ReactNode } from "react";
import type { Herramienta } from "./dibujo";
import { formatoDistancia } from "./geometria";

interface Props {
  activa: Herramienta;
  medicionM: number | null;
  onElegir: (herramienta: Herramienta) => void;
  onBorrarMedicion: () => void;
}

// Íconos de trazo, dibujados a mano para que calcen con el filete de 2 px de la app.
const ICONOS: Record<Herramienta, ReactNode> = {
  punto: <circle cx="8" cy="8" r="3.5" fill="currentColor" />,
  poligono: <path d="M3 5.5 8.5 2 14 6.5 11.5 14 4 12.5Z" />,
  rectangulo: <rect x="2.5" y="3.5" width="11" height="9" />,
  circulo: <circle cx="8" cy="8" r="5.5" />,
  medir: <path d="M2 13 14 3M5 13v-3M8 10.5V8M11 8V5.5" />,
};

const HERRAMIENTAS: { id: Herramienta; nombre: string; ayuda: string }[] = [
  { id: "punto", nombre: "Punto", ayuda: "" },
  { id: "poligono", nombre: "Polígono", ayuda: "Clic en cada vértice; clic en el primero o Enter para cerrar." },
  { id: "rectangulo", nombre: "Rectángulo", ayuda: "Clic en una esquina y clic en la opuesta." },
  { id: "circulo", nombre: "Círculo", ayuda: "Clic en el centro y clic para fijar el radio." },
  { id: "medir", nombre: "Medir", ayuda: "Clic en cada punto; clic otra vez en el último o Enter para terminar." },
];

/** Barra de herramientas del mapa: evaluar un punto, dibujar una zona o medir. */
export function Herramientas({ activa, medicionM, onElegir, onBorrarMedicion }: Props) {
  const ayuda = HERRAMIENTAS.find((h) => h.id === activa)?.ayuda;
  return (
    <div className="herramientas">
      <div className="herramientas-botones" role="toolbar" aria-label="Herramientas del mapa">
        {HERRAMIENTAS.map((h) => (
          <button
            key={h.id}
            type="button"
            aria-pressed={activa === h.id}
            title={h.nombre}
            onClick={() => onElegir(h.id)}
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
              {ICONOS[h.id]}
            </svg>
            <span>{h.nombre}</span>
          </button>
        ))}
      </div>
      {ayuda && <p className="herramientas-ayuda">{ayuda} Esc para cancelar.</p>}
      {medicionM != null && (
        <p className="herramientas-medida" aria-live="polite">
          <strong>{formatoDistancia(medicionM)}</strong>
          en línea recta por tramos
          <button type="button" className="enlace" onClick={onBorrarMedicion}>
            Borrar
          </button>
        </p>
      )}
    </div>
  );
}
