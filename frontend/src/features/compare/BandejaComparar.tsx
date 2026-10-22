import { nombrePropio, numero } from "../../shared/formato";
import type { Comparado } from "./comparacion";
import "./comparar.css";

interface Props {
  puntos: Comparado[];
  onQuitar: (indice: number) => void;
  onVer: () => void;
  onVaciar: () => void;
}

/** Barra al pie del mapa con los puntos guardados para comparar. */
export function BandejaComparar({ puntos, onQuitar, onVer, onVaciar }: Props) {
  if (puntos.length === 0) return null;
  return (
    <div className="bandeja" role="region" aria-label="Puntos para comparar">
      <ol className="bandeja-puntos">
        {puntos.map((p, i) => (
          <li key={`${p.ficha.lat},${p.ficha.lon}`}>
            <span className="comparar-numero">{i + 1}</span>
            {nombrePropio(p.ficha.comuna)} <strong>{numero(p.ficha.puntaje)}</strong>
            <button type="button" className="bandeja-quitar" onClick={() => onQuitar(i)} aria-label={`Quitar punto ${i + 1}`}>
              ×
            </button>
          </li>
        ))}
      </ol>
      <button type="button" className="boton-principal" disabled={puntos.length < 2} onClick={onVer}>
        {puntos.length < 2 ? "Agrega otro punto" : "Comparar"}
      </button>
      <button type="button" className="enlace" onClick={onVaciar}>
        Vaciar
      </button>
    </div>
  );
}
