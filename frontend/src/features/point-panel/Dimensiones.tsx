import { useState } from "react";
import { conUnidad, numero } from "../../shared/formato";
import type { Dimension } from "../../shared/tipos";

const UMBRAL_DEBIL = 50;

/** Las dimensiones del puntaje, con barra y detalle de indicadores al abrir. */
export function Dimensiones({ dimensiones }: { dimensiones: Dimension[] }) {
  const [abierta, setAbierta] = useState<string | null>(null);
  return (
    <section className="panel-seccion" aria-labelledby="titulo-dimensiones">
      <h2 id="titulo-dimensiones" className="etiqueta">
        Dimensiones
      </h2>
      <ul className="dimensiones">
        {dimensiones.map((d) => {
          const debil = d.puntaje != null && d.puntaje < UMBRAL_DEBIL;
          const abiertaEsta = abierta === d.id;
          return (
            <li key={d.id} className={debil ? "dimension dimension-debil" : "dimension"}>
              <button
                type="button"
                className="dimension-fila"
                aria-expanded={abiertaEsta}
                onClick={() => setAbierta(abiertaEsta ? null : d.id)}
              >
                <span className="dimension-nombre">
                  {d.nombre}
                  {d.nivel !== "punto" && <span className="dimension-nivel">{d.nivel}</span>}
                </span>
                <span className="dimension-valor">{numero(d.puntaje)}</span>
                <span className="dimension-barra" aria-hidden="true">
                  <span style={{ width: `${d.puntaje ?? 0}%` }} />
                </span>
              </button>
              {abiertaEsta && (
                <dl className="dimension-detalle">
                  {d.indicadores.map((i) => (
                    <div key={i.descripcion}>
                      <dt>{i.descripcion}</dt>
                      <dd>{conUnidad(i.valor, i.unidad)}</dd>
                    </div>
                  ))}
                  <div className="dimension-peso">
                    <dt>Peso en el puntaje</dt>
                    <dd>{d.peso}%</dd>
                  </div>
                </dl>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
