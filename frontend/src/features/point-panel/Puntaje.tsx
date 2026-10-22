import { coordenadas, nombrePropio, numero } from "../../shared/formato";
import type { FichaPunto } from "../../shared/tipos";

interface Props {
  ficha: FichaPunto;
  direccion: string | null;
}

/** Cabecera del panel: dónde estoy, el número grande, la letra y el veredicto. */
export function Puntaje({ ficha, direccion }: Props) {
  return (
    <header className="panel-cabecera">
      <p className="etiqueta">
        {nombrePropio(ficha.comuna)}
        {direccion ? ` — ${direccion}` : ""}
      </p>
      <div className="panel-cifra">
        <span className="panel-numero">{numero(ficha.puntaje)}</span>
        {ficha.letra && (
          <span className="panel-letra" aria-label={`Letra ${ficha.letra}`}>
            {ficha.letra}
          </span>
        )}
      </div>
      <p className="panel-veredicto">{ficha.veredicto}</p>
      <p className="panel-percentiles">
        Mejor que el {numero(ficha.percentil_rm)}% de la RM · que el {numero(ficha.percentil_comuna)}% de{" "}
        {nombrePropio(ficha.comuna)}
      </p>
      <p className="panel-coordenadas">
        {coordenadas(ficha.lat, ficha.lon)}
        {ficha.distancia_al_hexagono_m > 0 && ` · zona habitada más cercana a ${numero(ficha.distancia_al_hexagono_m)} m`}
      </p>
    </header>
  );
}
