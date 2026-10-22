import type { ReactNode } from "react";
import { PanelLateral } from "../../shared/PanelLateral";
import { Cercanias } from "./Cercanias";
import { Comuna } from "./Comuna";
import { Dimensiones } from "./Dimensiones";
import { Precios, type EstadoPrecios } from "./Precios";
import { Puntaje } from "./Puntaje";
import type { EstadoFicha } from "./usePunto";

interface Props {
  ficha: EstadoFicha;
  direccion: string | null;
  precios: EstadoPrecios;
  isocrona: "oculta" | "cargando" | "visible";
  comparando: boolean;
  puedeComparar: boolean;
  onConsultarPrecios: () => void;
  onExportar: () => void;
  onIsocrona: () => void;
  onComparar: () => void;
  onCerrar: () => void;
}

export function Panel(props: Props) {
  const { ficha, direccion, precios, onConsultarPrecios, onCerrar } = props;
  if (ficha.tipo === "vacio") {
    return (
      <Contenedor>
        <div className="panel-vacio">
          <p className="panel-vacio-titulo">Toca un punto del mapa.</p>
          <p>
            Verás qué tan buena es esa ubicación para vivir: un puntaje de 0 a 100, lo que tiene cerca, los datos de su
            comuna y los arriendos del sector.
          </p>
          <p>O dibuja una zona con el polígono, el rectángulo o el círculo para ver su informe.</p>
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
      <Acciones {...props} />
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

function Acciones({ isocrona, comparando, puedeComparar, onExportar, onIsocrona, onComparar }: Props) {
  return (
    <div className="panel-acciones">
      <button type="button" className="boton-principal" onClick={onExportar}>
        Exportar ficha
      </button>
      <button
        type="button"
        className="boton-secundario"
        aria-pressed={isocrona === "visible"}
        disabled={isocrona === "cargando"}
        onClick={onIsocrona}
      >
        {isocrona === "visible" ? "Ocultar isócrona" : isocrona === "cargando" ? "Calculando…" : "A pie: 5·10·15 min"}
      </button>
      <button
        type="button"
        className="boton-secundario"
        aria-pressed={comparando}
        disabled={!comparando && !puedeComparar}
        onClick={onComparar}
        title={!comparando && !puedeComparar ? "Puedes comparar hasta 3 puntos" : undefined}
      >
        {comparando ? "Quitar de comparar" : "Comparar"}
      </button>
    </div>
  );
}

function Contenedor({ children, onCerrar }: { children: ReactNode; onCerrar?: () => void }) {
  return (
    <PanelLateral etiqueta="Evaluación del punto" onCerrar={onCerrar}>
      {children}
    </PanelLateral>
  );
}
