import type { ReactNode } from "react";
import { Cercanias } from "./Cercanias";
import { Comuna } from "./Comuna";
import { Dimensiones } from "./Dimensiones";
import { Precios, type EstadoPrecios } from "./Precios";
import { Puntaje } from "./Puntaje";
import type { EstadoFicha } from "./usePunto";
import "./panel.css";

interface Props {
  ficha: EstadoFicha;
  direccion: string | null;
  precios: EstadoPrecios;
  onConsultarPrecios: () => void;
  onExportar: () => void;
  onCerrar: () => void;
}

export function Panel({ ficha, direccion, precios, onConsultarPrecios, onExportar, onCerrar }: Props) {
  if (ficha.tipo === "vacio") {
    return (
      <Contenedor>
        <div className="panel-vacio">
          <p className="panel-vacio-titulo">Toca un punto del mapa.</p>
          <p>
            Verás qué tan buena es esa ubicación para vivir: un puntaje de 0 a 100, lo que tiene cerca, los datos de su
            comuna y los arriendos del sector.
          </p>
          <p className="panel-nota">También puedes buscar una dirección arriba.</p>
        </div>
      </Contenedor>
    );
  }
  if (ficha.tipo === "cargando") {
    return (
      <Contenedor>
        <p className="panel-nota panel-cargando">Calculando…</p>
      </Contenedor>
    );
  }
  if (ficha.tipo === "error") {
    return (
      <Contenedor onCerrar={onCerrar}>
        <p className="panel-nota panel-nota-error">{ficha.mensaje}</p>
      </Contenedor>
    );
  }
  const f = ficha.ficha;
  return (
    <Contenedor onCerrar={onCerrar}>
      <Puntaje ficha={f} direccion={direccion} />
      <div className="panel-acciones">
        <button type="button" className="boton-principal" onClick={onExportar}>
          Exportar ficha
        </button>
      </div>
      <Dimensiones dimensiones={f.dimensiones} />
      <Cercanias cercanias={f.cercanias} barrio={f.barrio} />
      <Precios estado={precios} onConsultar={onConsultarPrecios} />
      <Comuna comuna={f.comuna} datos={f.datos_comunales} />
      <p className="panel-fuente">
        Modelo {f.version_modelo}. Fuentes: Censo 2024, Casen 2024, CEAD, Minsal, Mineduc, DTPM, OpenStreetMap.
      </p>
    </Contenedor>
  );
}

function Contenedor({ children, onCerrar }: { children: ReactNode; onCerrar?: () => void }) {
  return (
    <aside className="panel" aria-label="Evaluación del punto">
      {onCerrar && (
        <button type="button" className="panel-cerrar" onClick={onCerrar} aria-label="Cerrar">
          ×
        </button>
      )}
      {children}
    </aside>
  );
}
