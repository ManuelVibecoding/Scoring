import { useEffect, useMemo, useState } from "react";
import { DialogoExportar } from "./features/export/DialogoExportar";
import { hexagonosGeoJSON, type Variable } from "./features/map/capa";
import { Leyenda, type OpcionCapa } from "./features/map/Leyenda";
import { Mapa } from "./features/map/Mapa";
import { Panel } from "./features/point-panel/Panel";
import { usePunto, type Punto } from "./features/point-panel/usePunto";
import { Buscador } from "./features/search/Buscador";
import { api } from "./shared/api";
import type { Capa } from "./shared/tipos";
import "./app.css";

const OPCIONES_CAPA: OpcionCapa[] = [
  { id: "puntaje", nombre: "Puntaje total" },
  { id: "seguridad", nombre: "Seguridad" },
  { id: "socioeconomico", nombre: "Entorno socioeconómico" },
  { id: "servicios", nombre: "Servicios cercanos" },
  { id: "transporte", nombre: "Transporte público" },
  { id: "conectividad", nombre: "Conectividad vial" },
  { id: "areas_verdes", nombre: "Áreas verdes" },
  { id: "entorno", nombre: "Tranquilidad del entorno" },
];

export function App() {
  const [capa, setCapa] = useState<Capa | null>(null);
  const [comunas, setComunas] = useState<GeoJSON.FeatureCollection | null>(null);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [variable, setVariable] = useState<Variable>("puntaje");
  const [punto, setPunto] = useState<Punto | null>(null);
  const [destino, setDestino] = useState<Punto | null>(null);
  const [exportando, setExportando] = useState(false);
  const { ficha, direccion, precios, consultarPrecios } = usePunto(punto);

  useEffect(() => {
    Promise.all([api.capa(), api.comunas()])
      .then(([c, g]) => {
        setCapa(c);
        setComunas(g);
      })
      .catch(() => setErrorCarga("No se pudo conectar con la API. ¿Está corriendo el backend?"));
  }, []);

  const hexagonos = useMemo(() => (capa ? hexagonosGeoJSON(capa) : null), [capa]);
  const seleccionado = ficha.tipo === "listo" ? ficha.ficha.h3 : null;

  return (
    <div className="app">
      <header className="barra">
        <h1 className="marca">
          Score<span className="marca-sub">Región Metropolitana</span>
        </h1>
        <Buscador
          onElegir={(r) => {
            setDestino({ lat: r.lat, lon: r.lon });
            setPunto({ lat: r.lat, lon: r.lon });
          }}
        />
      </header>

      <main className={punto ? "contenido con-punto" : "contenido"}>
        <div className="zona-mapa">
          <Mapa
            hexagonos={hexagonos}
            comunas={comunas}
            variable={variable}
            seleccionado={seleccionado}
            destino={destino}
            marcador={punto}
            onTocar={(lat, lon) => setPunto({ lat, lon })}
          />
          <Leyenda opciones={OPCIONES_CAPA} variable={variable} onCambiar={setVariable} />
          {errorCarga && <p className="aviso-carga">{errorCarga}</p>}
          {!capa && !errorCarga && <p className="aviso-carga">Cargando 9.666 hexágonos…</p>}
        </div>
        <Panel
          ficha={ficha}
          direccion={direccion}
          precios={precios}
          onConsultarPrecios={consultarPrecios}
          onExportar={() => {
            // La ficha incluye arriendos: si aún no se consultaron, se piden al abrir.
            if (precios.tipo === "inicial") consultarPrecios();
            setExportando(true);
          }}
          onCerrar={() => setPunto(null)}
        />
      </main>

      {exportando && ficha.tipo === "listo" && (
        <DialogoExportar
          ficha={ficha.ficha}
          direccion={direccion}
          precios={precios.tipo === "listo" ? precios.resumen : null}
          cargandoPrecios={precios.tipo === "cargando"}
          onCerrar={() => setExportando(false)}
        />
      )}
    </div>
  );
}
