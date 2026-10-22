import { useEffect, useState } from "react";
import { api } from "../../shared/api";
import type { ResultadoBusqueda } from "../../shared/tipos";
import "./buscador.css";

interface Props {
  onElegir: (resultado: ResultadoBusqueda) => void;
}

const ESPERA_MS = 450;
const LARGO_MINIMO = 4;

type Busqueda =
  | { estado: "buscando" }
  | { estado: "listo"; resultados: ResultadoBusqueda[] }
  | { estado: "error" };

/** Búsqueda de direcciones (Nominatim vía la API), con espera mientras se escribe. */
export function Buscador({ onElegir }: Props) {
  const [texto, setTexto] = useState("");
  // Cada respuesta recuerda para qué texto fue: las de textos viejos se ignoran.
  const [busqueda, setBusqueda] = useState<{ texto: string; valor: Busqueda } | null>(null);
  const [elegido, setElegido] = useState<string | null>(null);

  const consulta = texto.trim();
  const debeBuscar = consulta.length >= LARGO_MINIMO && consulta !== elegido;

  useEffect(() => {
    if (!debeBuscar) return;
    let vigente = true;
    const temporizador = setTimeout(() => {
      setBusqueda({ texto: consulta, valor: { estado: "buscando" } });
      api
        .buscar(consulta)
        .then((r) => vigente && setBusqueda({ texto: consulta, valor: { estado: "listo", resultados: r } }))
        .catch(() => vigente && setBusqueda({ texto: consulta, valor: { estado: "error" } }));
    }, ESPERA_MS);
    return () => {
      vigente = false;
      clearTimeout(temporizador);
    };
  }, [consulta, debeBuscar]);

  const actual = debeBuscar && busqueda?.texto === consulta ? busqueda.valor : null;
  const resultados = actual?.estado === "listo" ? actual.resultados : [];

  function elegir(r: ResultadoBusqueda) {
    const corto = (r.nombre.split(",")[0] ?? r.nombre).trim();
    setElegido(corto);
    setTexto(corto);
    onElegir(r);
  }

  return (
    <div className="buscador">
      <label htmlFor="buscar-direccion" className="visualmente-oculto">
        Buscar una dirección
      </label>
      <input
        id="buscar-direccion"
        type="search"
        placeholder="Irarrázaval 3450, Ñuñoa"
        value={texto}
        autoComplete="off"
        onChange={(e) => setTexto(e.target.value)}
        onKeyDown={(e) => {
          const primero = resultados[0];
          if (e.key === "Enter" && primero) elegir(primero);
        }}
      />
      {actual?.estado === "buscando" && <p className="buscador-estado">Buscando…</p>}
      {actual?.estado === "listo" && resultados.length === 0 && (
        <p className="buscador-estado">Sin resultados en la RM.</p>
      )}
      {actual?.estado === "error" && <p className="buscador-estado">El buscador no respondió. Prueba de nuevo.</p>}
      {resultados.length > 0 && (
        <ul className="buscador-resultados" role="listbox">
          {resultados.map((r) => (
            <li key={`${r.lat},${r.lon}`}>
              <button type="button" onClick={() => elegir(r)}>
                {r.nombre}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
