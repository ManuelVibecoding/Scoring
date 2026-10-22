import { conUnidad, nombrePropio } from "../../shared/formato";
import type { DatoComunal } from "../../shared/tipos";

interface Props {
  comuna: string;
  datos: DatoComunal[];
}

export function Comuna({ comuna, datos }: Props) {
  return (
    <section className="panel-seccion" aria-labelledby="titulo-comuna">
      <h2 id="titulo-comuna" className="etiqueta">
        La comuna · {nombrePropio(comuna)}
      </h2>
      <dl className="datos">
        {datos.map((d) => (
          <div key={d.etiqueta}>
            <dt>{d.etiqueta}</dt>
            <dd>{conUnidad(d.valor, d.unidad)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
