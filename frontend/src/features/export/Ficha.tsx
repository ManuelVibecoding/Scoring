import {
  conUnidad,
  coordenadas,
  enumerar,
  minutos,
  nombreFuente,
  nombreLugar,
  nombrePropio,
  numero,
  pesos,
} from "../../shared/formato";
import type { FichaPunto, ResumenPrecios } from "../../shared/tipos";
import { ATRIBUCION_SATELITE } from "./imagenSatelital";
import "./ficha.css";

// Las cercanías que caben en el cuadrante, en orden de importancia.
const CERCANIAS_FICHA = [
  "metro",
  "paradero",
  "supermercado",
  "farmacia",
  "colegio",
  "cesfam",
  "plaza",
  "urgencia",
  "acceso_autopista",
];
const DATOS_COMUNA_FICHA = [
  "Población",
  "Pobreza por ingresos",
  "Homicidios",
  "Escolaridad promedio",
  "Calidad de vida urbana (ICVU)",
];
const UMBRAL_DEBIL = 50;

interface Props {
  ficha: FichaPunto;
  direccion: string | null;
  imagen: string | null;
  precios: ResumenPrecios | null;
}

/** Ficha de 1600 × 900 px (16:9) en cuatro cuadrantes, lista para una presentación. */
export function Ficha({ ficha, direccion, imagen, precios }: Props) {
  const comuna = nombrePropio(ficha.comuna);
  const cercanias = CERCANIAS_FICHA.map((id) => ficha.cercanias.find((c) => c.id === id)).filter(
    (c) => c !== undefined,
  );
  const datosComuna = DATOS_COMUNA_FICHA.map((e) => ficha.datos_comunales.find((d) => d.etiqueta === e)).filter(
    (d) => d !== undefined,
  );
  const hoy = new Intl.DateTimeFormat("es-CL", { day: "numeric", month: "long", year: "numeric" }).format(new Date());

  return (
    <div className="ficha">
      <header className="ficha-cabecera">
        <span className="ficha-marca">Score</span>
        <span className="ficha-titulo">
          {direccion ? `${direccion}, ` : ""}
          {comuna}
        </span>
        <span className="ficha-fecha">{hoy}</span>
      </header>

      <div className="ficha-grilla">
        {/* 1. El punto */}
        <section className="ficha-cuadrante ficha-punto">
          <h2 className="ficha-etiqueta">01 · El punto</h2>
          {imagen ? (
            <img src={imagen} alt={`Vista satelital del punto en ${comuna}`} />
          ) : (
            <div className="ficha-sin-imagen">Imagen satelital no disponible</div>
          )}
          <p className="ficha-pie">{coordenadas(ficha.lat, ficha.lon)}</p>
        </section>

        {/* 2. Cercanías */}
        <section className="ficha-cuadrante">
          <h2 className="ficha-etiqueta">02 · Cercanías</h2>
          <table className="ficha-tabla">
            <tbody>
              {cercanias.map((c) => (
                <tr key={c.id}>
                  <th>{c.etiqueta}</th>
                  <td className="ficha-tabla-lugar">{nombreLugar(c.lugar)}</td>
                  <td className="ficha-tabla-valor">
                    {minutos(c.minutos)}
                    <span>{c.modo === "auto" ? " auto" : ""}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="ficha-pie">
            Minutos por la red de calles. {numero(ficha.barrio.recorridos_400m)} recorridos de bus a 400 m.
          </p>
        </section>

        {/* 3. La comuna y el precio */}
        <section className="ficha-cuadrante">
          <h2 className="ficha-etiqueta">03 · {comuna} y arriendos</h2>
          <div className="ficha-precios">
            <div>
              <span className="ficha-cifra-media">{precios ? pesos(precios.mediana_arriendo_clp) : "—"}</span>
              <span>arriendo mediano a 800 m</span>
            </div>
            <div>
              <span className="ficha-cifra-media">{precios ? pesos(precios.mediana_clp_m2) : "—"}</span>
              <span>por m² al mes{precios ? ` · ${numero(precios.avisos)} avisos` : ""}</span>
            </div>
          </div>
          <table className="ficha-tabla">
            <tbody>
              {datosComuna.map((d) => (
                <tr key={d.etiqueta}>
                  <th>{d.etiqueta}</th>
                  <td className="ficha-tabla-valor">{conUnidad(d.valor, d.unidad)}</td>
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
                <span className="ficha-numero">{numero(ficha.puntaje)}</span>
                {ficha.letra && <span className="ficha-letra">{ficha.letra}</span>}
              </div>
              <p className="ficha-percentil">Mejor que el {numero(ficha.percentil_rm)}% de la RM</p>
              <p className="ficha-texto">{ficha.veredicto}</p>
            </div>
            <ul className="ficha-dimensiones">
            {ficha.dimensiones.map((d) => (
              <li key={d.id} className={d.puntaje != null && d.puntaje < UMBRAL_DEBIL ? "ficha-debil" : ""}>
                <span>{d.nombre}</span>
                <span className="ficha-barra">
                  <span style={{ width: `${d.puntaje ?? 0}%` }} />
                </span>
                <span>{numero(d.puntaje)}</span>
              </li>
            ))}
            </ul>
          </div>
        </section>
      </div>

      <footer className="ficha-fuentes">
        Puntaje 0–100, modelo {ficha.version_modelo}. Fuentes: Censo 2024 (INE), Casen 2024 (MDSF), CEAD, Minsal,
        Mineduc, DTPM, OpenStreetMap{precios ? `; avisos de ${enumerar(precios.fuentes.map(nombreFuente))}` : ""}.{" "}
        {ATRIBUCION_SATELITE}.
      </footer>
    </div>
  );
}
