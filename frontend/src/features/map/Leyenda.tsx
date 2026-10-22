import { ESCALA_PUNTAJE } from "../../styles/tokens";
import type { Variable } from "./capa";
import "./leyenda.css";

export interface OpcionCapa {
  id: Variable;
  nombre: string;
}

interface Props {
  opciones: OpcionCapa[];
  variable: Variable;
  onCambiar: (variable: Variable) => void;
}

/** Selector de lo que pinta el mapa y su escala de grises. */
export function Leyenda({ opciones, variable, onCambiar }: Props) {
  return (
    <section className="leyenda" aria-label="Capa del mapa">
      <label className="etiqueta" htmlFor="selector-capa">
        Colorear por
      </label>
      <select id="selector-capa" value={variable} onChange={(e) => onCambiar(e.target.value)}>
        {opciones.map((o) => (
          <option key={o.id} value={o.id}>
            {o.nombre}
          </option>
        ))}
      </select>
      <div className="leyenda-escala" aria-hidden="true">
        {ESCALA_PUNTAJE.map(([corte, color]) => (
          <span key={corte} style={{ background: color }} />
        ))}
      </div>
      <div className="leyenda-extremos">
        <span>Peor</span>
        <span>Mejor</span>
      </div>
      <p className="leyenda-nota">Sin color: zonas sin viviendas (parques, industrias).</p>
    </section>
  );
}
