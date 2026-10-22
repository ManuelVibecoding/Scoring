import type { ReactNode } from "react";

interface Props {
  etiqueta: string;
  children: ReactNode;
  onCerrar?: () => void;
}

/** Columna derecha de la app: muestra el punto o la zona elegida. */
export function PanelLateral({ etiqueta, children, onCerrar }: Props) {
  return (
    <aside className="panel" aria-label={etiqueta}>
      {onCerrar && (
        <button type="button" className="panel-cerrar" onClick={onCerrar} aria-label="Cerrar">
          ×
        </button>
      )}
      {children}
    </aside>
  );
}
