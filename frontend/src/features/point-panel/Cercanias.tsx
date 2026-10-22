import { minutos, nombreLugar, numero } from "../../shared/formato";
import type { Cercania } from "../../shared/tipos";

interface Props {
  cercanias: Cercania[];
  barrio: Record<string, number | null>;
}

/** Lugares más cercanos (por la red de calles) y la oferta del barrio. */
export function Cercanias({ cercanias, barrio }: Props) {
  const aPie = cercanias.filter((c) => c.modo === "pie");
  const enAuto = cercanias.filter((c) => c.modo === "auto");
  return (
    <section className="panel-seccion" aria-labelledby="titulo-cercanias">
      <h2 id="titulo-cercanias" className="etiqueta">
        Cercanías
      </h2>
      <div className="barrio">
        <div>
          <span className="barrio-cifra">{numero(barrio.recorridos_400m)}</span>
          <span className="barrio-texto">recorridos de bus a 400 m</span>
        </div>
        <div>
          <span className="barrio-cifra">{numero(barrio.n800_colegio)}</span>
          <span className="barrio-texto">colegios a 800 m</span>
        </div>
        <div>
          <span className="barrio-cifra">{numero(barrio.n800_comercio_barrio)}</span>
          <span className="barrio-texto">locales de barrio a 800 m</span>
        </div>
      </div>
      <TablaCercanias titulo="A pie" filas={aPie} />
      <TablaCercanias titulo="En auto" filas={enAuto} />
    </section>
  );
}

function TablaCercanias({ titulo, filas }: { titulo: string; filas: Cercania[] }) {
  return (
    <table className="cercanias">
      <caption>{titulo}</caption>
      <tbody>
        {filas.map((c) => (
          <tr key={c.id}>
            <th scope="row">{c.etiqueta}</th>
            <td className="cercanias-lugar">{c.minutos == null ? "" : nombreLugar(c.lugar)}</td>
            <td className="cercanias-minutos">{minutos(c.minutos)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
