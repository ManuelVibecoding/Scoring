import { porcentaje } from "../../shared/formato";
import { LETRAS } from "../../shared/modelo";
import type { ResumenZona } from "../../shared/tipos";
import { COLOR_LETRA } from "../../styles/tokens";
import "./zona.css";

/** Qué parte de la población de la zona vive en cada letra (A mejor, E peor). */
export function DistribucionLetras({ distribucion }: { distribucion: ResumenZona["distribucion_letras"] }) {
  return (
    <div className="letras">
      <div className="letras-barra" aria-hidden="true">
        {LETRAS.map((l) => (
          <span key={l} style={{ flexGrow: distribucion[l] ?? 0, background: COLOR_LETRA[l] }} />
        ))}
      </div>
      <ul className="letras-leyenda">
        {LETRAS.map((l) => (
          <li key={l}>
            <span className="letras-muestra" style={{ background: COLOR_LETRA[l] }} aria-hidden="true" />
            {l} {porcentaje(distribucion[l] ?? 0)}
          </li>
        ))}
      </ul>
    </div>
  );
}
