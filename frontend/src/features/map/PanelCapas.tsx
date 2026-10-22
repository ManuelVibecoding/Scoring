import { useState } from "react";
import { numero } from "../../shared/formato";
import { nombreVariable } from "../../shared/modelo";
import { COLOR_LUGAR, ESCALA_CALOR } from "../../styles/tokens";
import { type EstiloBase, NOMBRES_ESTILO } from "./estilos";
import { GRUPOS_LUGARES, type GrupoLugares } from "./useDatosMapa";
import "./panelCapas.css";

export interface OpcionesCapas {
  estiloBase: EstiloBase;
  calor: boolean;
  variable: string;
  opacidad: number;
  lugares: GrupoLugares[];
  avisos: boolean;
  comunas: boolean;
}

interface Props {
  opciones: OpcionesCapas;
  variables: string[];
  cantidadAvisos: number | null;
  cargando: boolean;
  onCambiar: (cambio: Partial<OpcionesCapas>) => void;
}

const abiertoAlPartir = () => typeof window === "undefined" || window.matchMedia("(min-width: 761px)").matches;

/** Qué se ve en el mapa: mapa base, capa de calor, lugares y avisos de arriendo. */
export function PanelCapas({ opciones, variables, cantidadAvisos, cargando, onCambiar }: Props) {
  const [abierto, setAbierto] = useState(abiertoAlPartir);
  const alternarLugar = (id: GrupoLugares) =>
    onCambiar({
      lugares: opciones.lugares.includes(id) ? opciones.lugares.filter((g) => g !== id) : [...opciones.lugares, id],
    });

  return (
    <section className="capas" aria-label="Capas del mapa">
      <button type="button" className="capas-cabecera" aria-expanded={abierto} onClick={() => setAbierto(!abierto)}>
        <span className="etiqueta">Capas</span>
        <span aria-hidden="true">{abierto ? "−" : "+"}</span>
      </button>

      {abierto && (
        <div className="capas-cuerpo">
          <div className="capas-segmentos" role="radiogroup" aria-label="Mapa base">
            {(Object.keys(NOMBRES_ESTILO) as EstiloBase[]).map((e) => (
              <button
                key={e}
                type="button"
                role="radio"
                aria-checked={opciones.estiloBase === e}
                onClick={() => onCambiar({ estiloBase: e })}
              >
                {NOMBRES_ESTILO[e]}
              </button>
            ))}
          </div>

          <fieldset className="capas-grupo">
            <label className="capas-opcion">
              <input
                type="checkbox"
                checked={opciones.calor}
                onChange={(e) => onCambiar({ calor: e.target.checked })}
              />
              Calor
            </label>
            {opciones.calor && (
              <>
                <select
                  aria-label="Variable de la capa de calor"
                  value={opciones.variable}
                  onChange={(e) => onCambiar({ variable: e.target.value })}
                >
                  {variables.map((v) => (
                    <option key={v} value={v}>
                      {nombreVariable(v)}
                    </option>
                  ))}
                </select>
                <div
                  className="capas-escala"
                  aria-hidden="true"
                  style={{ background: `linear-gradient(90deg, ${ESCALA_CALOR.join(", ")})` }}
                />
                <div className="capas-extremos">
                  <span>Peor</span>
                  <span>Mediana RM</span>
                  <span>Mejor</span>
                </div>
                <label className="capas-intensidad">
                  Intensidad
                  <input
                    type="range"
                    min={0.2}
                    max={0.9}
                    step={0.05}
                    value={opciones.opacidad}
                    onChange={(e) => onCambiar({ opacidad: Number(e.target.value) })}
                  />
                </label>
              </>
            )}
          </fieldset>

          <fieldset className="capas-grupo">
            <legend className="etiqueta">Lugares</legend>
            {GRUPOS_LUGARES.map((g) => (
              <label key={g.id} className="capas-opcion">
                <input
                  type="checkbox"
                  checked={opciones.lugares.includes(g.id)}
                  onChange={() => alternarLugar(g.id)}
                />
                <span className="capas-punto" style={{ background: COLOR_LUGAR[g.id] }} aria-hidden="true" />
                {g.nombre}
              </label>
            ))}
          </fieldset>

          <fieldset className="capas-grupo">
            <legend className="etiqueta">Más</legend>
            <label className="capas-opcion">
              <input type="checkbox" checked={opciones.avisos} onChange={(e) => onCambiar({ avisos: e.target.checked })} />
              Avisos de arriendo
              {opciones.avisos && cantidadAvisos != null && <span className="capas-cuenta">{numero(cantidadAvisos)}</span>}
            </label>
            {opciones.avisos && (
              <p className="capas-nota">Más oscuro, más caro por m². Toca uno para ver el aviso.</p>
            )}
            <label className="capas-opcion">
              <input
                type="checkbox"
                checked={opciones.comunas}
                onChange={(e) => onCambiar({ comunas: e.target.checked })}
              />
              Límites comunales
            </label>
          </fieldset>
          {cargando && <p className="capas-nota">Cargando…</p>}
        </div>
      )}
    </section>
  );
}
