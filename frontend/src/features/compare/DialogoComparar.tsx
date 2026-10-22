import { useEffect, useState } from "react";
import { api } from "../../shared/api";
import { conUnidad, minutos, nombrePropio, numero, pesos, SIN_DATO } from "../../shared/formato";
import type { ResumenPrecios } from "../../shared/tipos";
import { bloquesDeComparacion, type Comparado, type Fila, mejores } from "./comparacion";
import "./comparar.css";

interface Props {
  puntos: Comparado[];
  onCerrar: () => void;
}

function formatear(fila: Fila, valor: number | null): string {
  if (valor == null) return SIN_DATO;
  switch (fila.formato) {
    case "puntaje":
    case "numero":
      return numero(valor);
    case "porcentaje":
      return `${numero(valor)}%`;
    case "minutos":
      return minutos(valor);
    case "pesos":
      return pesos(valor);
    case "dato":
      return conUnidad(valor, fila.unidad ?? "");
  }
}

/** Tabla lado a lado de 2 o 3 puntos; marca el mejor valor de cada fila. */
export function DialogoComparar({ puntos, onCerrar }: Props) {
  // Los arriendos se piden al abrir (están en caché casi siempre, así que es rápido).
  const [precios, setPrecios] = useState<(ResumenPrecios | null)[]>(() => puntos.map(() => null));
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    let vigente = true;
    Promise.all(puntos.map((p) => api.precios(p.ficha.lat, p.ficha.lon).catch(() => null)))
      .then((r) => vigente && setPrecios(r))
      .finally(() => vigente && setCargando(false));
    return () => {
      vigente = false;
    };
  }, [puntos]);

  useEffect(() => {
    const alPresionar = (e: KeyboardEvent) => e.key === "Escape" && onCerrar();
    window.addEventListener("keydown", alPresionar);
    return () => window.removeEventListener("keydown", alPresionar);
  }, [onCerrar]);

  const bloques = bloquesDeComparacion(puntos, precios);
  return (
    <div className="dialogo-fondo" role="dialog" aria-modal="true" aria-labelledby="titulo-comparar">
      <div className="dialogo dialogo-comparar">
        <header className="dialogo-cabecera">
          <h2 id="titulo-comparar">Comparar puntos</h2>
          <button type="button" className="dialogo-cerrar" onClick={onCerrar} aria-label="Cerrar">
            ×
          </button>
        </header>

        <div className="comparar-marco">
          <table className="comparar">
            <thead>
              <tr>
                <td />
                {puntos.map((p, i) => (
                  <th key={`${p.ficha.lat},${p.ficha.lon}`} scope="col">
                    <span className="comparar-numero">{i + 1}</span>
                    <span className="comparar-lugar">
                      <strong>{nombrePropio(p.ficha.comuna)}</strong>
                      <span>{p.direccion ?? `${p.ficha.lat.toFixed(4)}, ${p.ficha.lon.toFixed(4)}`}</span>
                    </span>
                    <span className="comparar-cifra">
                      {numero(p.ficha.puntaje)}
                      {p.ficha.letra && <span className="comparar-letra">{p.ficha.letra}</span>}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            {bloques.map((b) => (
              <tbody key={b.titulo}>
                <tr className="comparar-bloque">
                  <th scope="rowgroup" colSpan={puntos.length + 1}>
                    {b.titulo}
                    {b.titulo.startsWith("Arriendos") && cargando && " · consultando…"}
                  </th>
                </tr>
                {b.filas.map((f) => {
                  const ganadores = mejores(f);
                  return (
                    <tr key={f.id}>
                      <th scope="row">{f.etiqueta}</th>
                      {f.valores.map((v, i) => (
                        <td key={i} className={ganadores.includes(i) ? "comparar-mejor" : undefined}>
                          {formatear(f, v)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            ))}
          </table>
        </div>

        <footer className="dialogo-pie">
          <p className="dialogo-nota">En rojo, el mejor valor de cada fila. Minutos por la red de calles.</p>
        </footer>
      </div>
    </div>
  );
}
