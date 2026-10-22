import { nombrePropio, numero, pesos, porcentaje } from "../../shared/formato";
import { DIMENSIONES } from "../../shared/modelo";
import { PanelLateral } from "../../shared/PanelLateral";
import type { InformeZona } from "../../shared/tipos";
import { DistribucionLetras } from "./DistribucionLetras";
import type { EstadoZona } from "./useZona";

const UMBRAL_DEBIL = 50;
const COMUNAS_VISIBLES = 6;

interface Props {
  estado: EstadoZona;
  onExportar: () => void;
  onCerrar: () => void;
}

/** Informe de una zona dibujada: promedios ponderados por población, lo que hay y los arriendos. */
export function PanelZona({ estado, onExportar, onCerrar }: Props) {
  return (
    <PanelLateral etiqueta="Informe de la zona" onCerrar={onCerrar}>
      {estado.tipo === "cargando" && <p className="panel-nota panel-cargando">Analizando la zona…</p>}
      {estado.tipo === "error" && <p className="panel-nota panel-nota-error panel-cargando">{estado.mensaje}</p>}
      {estado.tipo === "listo" && <Informe informe={estado.informe} onExportar={onExportar} />}
    </PanelLateral>
  );
}

function Informe({ informe, onExportar }: { informe: InformeZona; onExportar: () => void }) {
  const { resumen, precios } = informe;
  if (resumen.hexagonos === 0) {
    return (
      <p className="panel-nota panel-cargando">
        La zona no tiene viviendas (parque, cerro o zona industrial). Dibuja una que incluya barrios.
      </p>
    );
  }
  const comunas = Object.entries(resumen.comunas);
  return (
    <>
      <header className="panel-cabecera">
        <p className="etiqueta">
          Zona dibujada · {numero(informe.area_km2, 1)} km²
        </p>
        <div className="panel-cifra">
          <span className="panel-numero">{numero(resumen.puntaje)}</span>
          {resumen.letra && <span className="panel-letra">{resumen.letra}</span>}
        </div>
        <p className="panel-veredicto">{informe.veredicto}</p>
        {resumen.rango_puntaje && (
          <p className="panel-percentiles">
            Puntaje promedio por habitante. La mayoría vive entre {numero(resumen.rango_puntaje[0])} y{" "}
            {numero(resumen.rango_puntaje[1])}.
          </p>
        )}
      </header>

      <div className="panel-acciones">
        <button type="button" className="boton-principal" onClick={onExportar}>
          Exportar ficha de la zona
        </button>
      </div>

      <section className="panel-seccion" aria-labelledby="titulo-letras">
        <h2 id="titulo-letras" className="etiqueta">
          Población por letra
        </h2>
        <DistribucionLetras distribucion={resumen.distribucion_letras} />
        <div className="barrio">
          <div>
            <span className="barrio-cifra">{numero(resumen.personas)}</span>
            <span className="barrio-texto">personas</span>
          </div>
          <div>
            <span className="barrio-cifra">{numero(resumen.hogares)}</span>
            <span className="barrio-texto">hogares</span>
          </div>
          <div>
            <span className="barrio-cifra">{numero(resumen.viviendas)}</span>
            <span className="barrio-texto">viviendas</span>
          </div>
        </div>
      </section>

      <section className="panel-seccion" aria-labelledby="titulo-dimensiones-zona">
        <h2 id="titulo-dimensiones-zona" className="etiqueta">
          Dimensiones
        </h2>
        <ul className="dimensiones">
          {DIMENSIONES.map((d) => {
            const valor = resumen.dimensiones[d.id] ?? null;
            const debil = valor != null && valor < UMBRAL_DEBIL;
            return (
              <li key={d.id} className={debil ? "dimension dimension-debil" : "dimension"}>
                <div className="dimension-fila">
                  <span className="dimension-nombre">{d.nombre}</span>
                  <span className="dimension-valor">{numero(valor)}</span>
                  <span className="dimension-barra" aria-hidden="true">
                    <span style={{ width: `${valor ?? 0}%` }} />
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="panel-seccion" aria-labelledby="titulo-dentro">
        <h2 id="titulo-dentro" className="etiqueta">
          Dentro de la zona
        </h2>
        <dl className="datos">
          {informe.lugares.map((l) => (
            <div key={l.id}>
              <dt>{l.etiqueta}</dt>
              <dd>{numero(l.cantidad)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="panel-seccion" aria-labelledby="titulo-arriendos-zona">
        <h2 id="titulo-arriendos-zona" className="etiqueta">
          Arriendos dentro
        </h2>
        {precios.avisos === 0 ? (
          <p className="panel-nota">No hay avisos de arriendo ubicados dentro de la zona.</p>
        ) : (
          <>
            <div className="barrio">
              <div>
                <span className="barrio-cifra">{pesos(precios.mediana_arriendo_clp)}</span>
                <span className="barrio-texto">arriendo mediano</span>
              </div>
              <div>
                <span className="barrio-cifra">{pesos(precios.mediana_clp_m2)}</span>
                <span className="barrio-texto">por m² al mes</span>
              </div>
              <div>
                <span className="barrio-cifra">{numero(precios.avisos)}</span>
                <span className="barrio-texto">avisos</span>
              </div>
            </div>
            <dl className="datos">
              {Object.entries(precios.mediana_por_dormitorios).map(([d, valor]) => (
                <div key={d}>
                  <dt>{d === "4" ? "4 o más dormitorios" : `${d} dormitorio${d === "1" ? "" : "s"}`}</dt>
                  <dd>{pesos(valor)}</dd>
                </div>
              ))}
            </dl>
          </>
        )}
      </section>

      <section className="panel-seccion" aria-labelledby="titulo-comunas-zona">
        <h2 id="titulo-comunas-zona" className="etiqueta">
          Comunas
        </h2>
        <dl className="datos">
          {comunas.slice(0, COMUNAS_VISIBLES).map(([c, fraccion]) => (
            <div key={c}>
              <dt>{nombrePropio(c)}</dt>
              <dd>{porcentaje(fraccion)} de la población</dd>
            </div>
          ))}
        </dl>
      </section>

      <p className="panel-fuente">
        Promedios de {numero(resumen.hexagonos)} hexágonos de 0,1 km² ponderados por población (Censo 2024). Arriendos
        de avisos vigentes ubicados dentro de la zona.
      </p>
    </>
  );
}
