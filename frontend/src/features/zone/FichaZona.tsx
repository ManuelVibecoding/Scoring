import { enumerar, nombreFuente, nombrePropio, numero, pesos, porcentaje } from "../../shared/formato";
import { DIMENSIONES } from "../../shared/modelo";
import type { InformeZona } from "../../shared/tipos";
import "../export/ficha.css";
import { ATRIBUCION_SATELITE } from "../export/imagenSatelital";
import { DistribucionLetras } from "./DistribucionLetras";
import { tituloZona } from "./titulo";

const UMBRAL_DEBIL = 50;
const COMUNAS_FICHA = 5;

interface Props {
  informe: InformeZona;
  imagen: string | null;
}

/** Ficha de una zona dibujada, con la misma grilla de cuatro cuadrantes que la de un punto. */
export function FichaZona({ informe, imagen }: Props) {
  const { resumen, precios } = informe;
  const hoy = new Intl.DateTimeFormat("es-CL", { day: "numeric", month: "long", year: "numeric" }).format(new Date());
  const fuentesAvisos = Object.keys(precios.por_fuente).map(nombreFuente);

  return (
    <div className="ficha">
      <header className="ficha-cabecera">
        <span className="ficha-marca">Score</span>
        <span className="ficha-titulo">{tituloZona(informe)}</span>
        <span className="ficha-fecha">{hoy}</span>
      </header>

      <div className="ficha-grilla">
        {/* 1. La zona */}
        <section className="ficha-cuadrante ficha-punto">
          <h2 className="ficha-etiqueta">01 · La zona</h2>
          {imagen ? (
            <img src={imagen} alt="Vista satelital de la zona" />
          ) : (
            <div className="ficha-sin-imagen">Imagen satelital no disponible</div>
          )}
          <p className="ficha-pie">
            {numero(informe.area_km2, 1)} km² · {numero(resumen.personas)} personas · {numero(resumen.hogares)} hogares
            · {numero(resumen.viviendas)} viviendas
          </p>
        </section>

        {/* 2. Qué hay dentro */}
        <section className="ficha-cuadrante">
          <h2 className="ficha-etiqueta">02 · Dentro de la zona</h2>
          <dl className="ficha-conteos">
            {informe.lugares.map((l) => (
              <div key={l.id}>
                <dt>{l.etiqueta}</dt>
                <dd>{numero(l.cantidad)}</dd>
              </div>
            ))}
          </dl>
          <div className="ficha-letras">
            <span className="ficha-subtitulo">Población por letra</span>
            <DistribucionLetras distribucion={resumen.distribucion_letras} />
          </div>
        </section>

        {/* 3. Comunas y arriendos */}
        <section className="ficha-cuadrante">
          <h2 className="ficha-etiqueta">03 · Comunas y arriendos</h2>
          <div className="ficha-precios">
            <div>
              <span className="ficha-cifra-media">{precios.avisos ? pesos(precios.mediana_arriendo_clp) : "—"}</span>
              <span>arriendo mediano dentro de la zona</span>
            </div>
            <div>
              <span className="ficha-cifra-media">{precios.avisos ? pesos(precios.mediana_clp_m2) : "—"}</span>
              <span>por m² al mes · {numero(precios.avisos)} avisos</span>
            </div>
          </div>
          <table className="ficha-tabla">
            <tbody>
              {Object.entries(resumen.comunas)
                .slice(0, COMUNAS_FICHA)
                .map(([c, fraccion]) => (
                  <tr key={c}>
                    <th>{nombrePropio(c)}</th>
                    <td className="ficha-tabla-valor">
                      {porcentaje(fraccion)}
                      <span> de la población</span>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </section>

        {/* 4. Veredicto */}
        <section className="ficha-cuadrante ficha-veredicto">
          <h2 className="ficha-etiqueta">04 · Veredicto</h2>
          <div className="ficha-veredicto-cuerpo">
            <div className="ficha-veredicto-resumen">
              <div className="ficha-cifra">
                <span className="ficha-numero">{numero(resumen.puntaje)}</span>
                {resumen.letra && <span className="ficha-letra">{resumen.letra}</span>}
              </div>
              <p className="ficha-percentil">
                Promedio por habitante
                {resumen.rango_puntaje &&
                  ` · la mayoría entre ${numero(resumen.rango_puntaje[0])} y ${numero(resumen.rango_puntaje[1])}`}
              </p>
              <p className="ficha-texto">{informe.veredicto}</p>
            </div>
            <ul className="ficha-dimensiones">
              {DIMENSIONES.map((d) => {
                const valor = resumen.dimensiones[d.id] ?? null;
                return (
                  <li key={d.id} className={valor != null && valor < UMBRAL_DEBIL ? "ficha-debil" : ""}>
                    <span>{d.nombre}</span>
                    <span className="ficha-barra">
                      <span style={{ width: `${valor ?? 0}%` }} />
                    </span>
                    <span>{numero(valor)}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        </section>
      </div>

      <footer className="ficha-fuentes">
        Promedios de {numero(resumen.hexagonos)} hexágonos ponderados por población. Fuentes: Censo 2024 (INE), Casen
        2024 (MDSF), CEAD, Minsal, Mineduc, DTPM, OpenStreetMap
        {fuentesAvisos.length > 0 ? `; avisos de ${enumerar(fuentesAvisos)}` : ""}. {ATRIBUCION_SATELITE}.
      </footer>
    </div>
  );
}
