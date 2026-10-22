import { enumerar, nombreFuente, numero, pesos } from "../../shared/formato";
import type { ResumenPrecios } from "../../shared/tipos";

export type EstadoPrecios =
  | { tipo: "inicial" }
  | { tipo: "cargando" }
  | { tipo: "listo"; resumen: ResumenPrecios }
  | { tipo: "error"; mensaje: string };

interface Props {
  estado: EstadoPrecios;
  onConsultar: () => void;
}

const fecha = new Intl.DateTimeFormat("es-CL", { day: "numeric", month: "short" });

/** Arriendos alrededor del punto. Se consultan a pedido porque pueden tardar. */
export function Precios({ estado, onConsultar }: Props) {
  return (
    <section className="panel-seccion" aria-labelledby="titulo-precios" aria-live="polite">
      <h2 id="titulo-precios" className="etiqueta">
        Arriendos cercanos
      </h2>
      {estado.tipo === "inicial" && (
        <button type="button" className="boton-secundario" onClick={onConsultar}>
          Ver arriendos a 800 m
        </button>
      )}
      {estado.tipo === "cargando" && (
        <p className="panel-nota">Consultando avisos… si la comuna no está en caché puede tardar hasta un minuto.</p>
      )}
      {estado.tipo === "error" && (
        <p className="panel-nota panel-nota-error">
          {estado.mensaje}{" "}
          <button type="button" className="enlace" onClick={onConsultar}>
            Reintentar
          </button>
        </p>
      )}
      {estado.tipo === "listo" && <Resumen resumen={estado.resumen} />}
    </section>
  );
}

function Resumen({ resumen }: { resumen: ResumenPrecios }) {
  if (resumen.avisos === 0) {
    return <p className="panel-nota">No hay avisos de arriendo a menos de {numero(resumen.radio_m)} m.</p>;
  }
  const dormitorios = Object.entries(resumen.mediana_por_dormitorios);
  return (
    <>
      <div className="barrio">
        <div>
          <span className="barrio-cifra">{pesos(resumen.mediana_arriendo_clp)}</span>
          <span className="barrio-texto">arriendo mediano</span>
        </div>
        <div>
          <span className="barrio-cifra">{pesos(resumen.mediana_clp_m2)}</span>
          <span className="barrio-texto">por m² al mes</span>
        </div>
        <div>
          <span className="barrio-cifra">{numero(resumen.avisos)}</span>
          <span className="barrio-texto">avisos a {numero(resumen.radio_m)} m</span>
        </div>
      </div>
      {dormitorios.length > 0 && (
        <dl className="datos">
          {dormitorios.map(([d, valor]) => (
            <div key={d}>
              <dt>{d === "4" ? "4 o más dormitorios" : `${d} dormitorio${d === "1" ? "" : "s"}`}</dt>
              <dd>{pesos(valor)}</dd>
            </div>
          ))}
        </dl>
      )}
      <ul className="avisos">
        {resumen.ejemplos.map(({ aviso, distancia_m }) => (
          <li key={aviso.id}>
            <a href={aviso.url} target="_blank" rel="noreferrer">
              {pesos(aviso.precio_clp)}
              {aviso.superficie_m2 ? ` · ${numero(aviso.superficie_m2)} m²` : ""}
              {aviso.dormitorios ? ` · ${aviso.dormitorios}D` : ""} · {aviso.tipo} · {nombreFuente(aviso.fuente)}
            </a>
            <span>{numero(distancia_m)} m</span>
          </li>
        ))}
      </ul>
      <p className="panel-fuente">
        {textoFuentes(resumen)}
        {resumen.actualizado && `, avisos al ${fecha.format(new Date(resumen.actualizado))}`}.
      </p>
    </>
  );
}

/** "Fuentes: Toc Toc (120) y Portal Inmobiliario (85)", sin repetir avisos publicados en ambos. */
function textoFuentes(resumen: ResumenPrecios): string {
  const partes = resumen.fuentes.map((f) => `${nombreFuente(f)} (${numero(resumen.por_fuente[f] ?? 0)})`);
  return `Fuente${partes.length === 1 ? "" : "s"}: ${enumerar(partes)}`;
}
