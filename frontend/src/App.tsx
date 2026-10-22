import { useCallback, useEffect, useMemo, useState } from "react";
import { BandejaComparar } from "./features/compare/BandejaComparar";
import { type Comparado, MAXIMO_COMPARADOS } from "./features/compare/comparacion";
import { DialogoComparar } from "./features/compare/DialogoComparar";
import { DialogoExportar } from "./features/export/DialogoExportar";
import { type Calor, type EstadoCapas, punto as puntoGeoJSON, VACIO } from "./features/map/capas";
import type { Herramienta } from "./features/map/dibujo";
import { largoM } from "./features/map/geometria";
import { Herramientas } from "./features/map/Herramientas";
import { Mapa } from "./features/map/Mapa";
import { type OpcionesCapas, PanelCapas } from "./features/map/PanelCapas";
import { useDatosMapa } from "./features/map/useDatosMapa";
import { Panel } from "./features/point-panel/Panel";
import { type Punto, usePunto } from "./features/point-panel/usePunto";
import { Buscador } from "./features/search/Buscador";
import { DialogoExportarZona } from "./features/zone/DialogoExportarZona";
import { PanelZona } from "./features/zone/PanelZona";
import { useZona } from "./features/zone/useZona";
import { api } from "./shared/api";
import "./app.css";

const OPCIONES_INICIALES: OpcionesCapas = {
  estiloBase: "mapa",
  calor: true,
  variable: "puntaje",
  opacidad: 0.5,
  lugares: [],
  avisos: false,
  comunas: true,
};

type Dialogo = "ficha" | "zona" | "comparar" | null;

// Un clic doble sin mover el mouse deja una figura diminuta: no se toma como zona.
const PERIMETRO_MINIMO_M = 150;

function coleccion(geometria: GeoJSON.Geometry | null, propiedades = {}): GeoJSON.FeatureCollection {
  return geometria
    ? { type: "FeatureCollection", features: [{ type: "Feature", properties: propiedades, geometry: geometria }] }
    : VACIO;
}

const mismoLugar = (a: Comparado, lat: number, lon: number) => a.ficha.lat === lat && a.ficha.lon === lon;

export function App() {
  const [opciones, setOpciones] = useState(OPCIONES_INICIALES);
  const [herramienta, setHerramienta] = useState<Herramienta>("punto");
  const [punto, setPunto] = useState<Punto | null>(null);
  const [destino, setDestino] = useState<Punto | null>(null);
  const [zona, setZona] = useState<GeoJSON.Polygon | null>(null);
  const [medicion, setMedicion] = useState<number[][] | null>(null);
  const [isocrona, setIsocrona] = useState<{ de: Punto; datos: GeoJSON.FeatureCollection | null } | null>(null);
  const [comparados, setComparados] = useState<Comparado[]>([]);
  const [dialogo, setDialogo] = useState<Dialogo>(null);

  const datos = useDatosMapa({ lugares: opciones.lugares, avisos: opciones.avisos });
  const { ficha, direccion, precios, consultarPrecios } = usePunto(punto);
  const estadoZona = useZona(zona);

  // Esc vuelve a la herramienta de punto (Terra Draw ya descarta el dibujo a medias).
  useEffect(() => {
    const alPresionar = (e: KeyboardEvent) => e.key === "Escape" && setHerramienta("punto");
    window.addEventListener("keydown", alPresionar);
    return () => window.removeEventListener("keydown", alPresionar);
  }, []);

  const elegirPunto = useCallback((lat: number, lon: number) => {
    setPunto({ lat, lon });
    setZona(null);
  }, []);

  const alDibujarZona = useCallback((geometria: GeoJSON.Polygon) => {
    if (largoM(geometria.coordinates[0] ?? []) < PERIMETRO_MINIMO_M) return;
    setZona(geometria);
    setPunto(null);
    setHerramienta("punto");
  }, []);

  const alMedir = useCallback((coordenadas: number[][]) => {
    setMedicion(coordenadas);
    setHerramienta("punto");
  }, []);

  const isocronaDelPunto = isocrona && isocrona.de === punto ? isocrona : null;
  function alternarIsocrona() {
    if (!punto) return;
    if (isocronaDelPunto) {
      setIsocrona(null);
      return;
    }
    setIsocrona({ de: punto, datos: null });
    api
      .isocrona(punto.lat, punto.lon)
      .then((d) => setIsocrona((actual) => (actual?.de === punto ? { de: punto, datos: d } : actual)))
      .catch(() => setIsocrona(null));
  }

  const fichaLista = ficha.tipo === "listo" ? ficha.ficha : null;
  const comparando = fichaLista ? comparados.some((c) => mismoLugar(c, fichaLista.lat, fichaLista.lon)) : false;
  function alternarComparar() {
    if (!fichaLista) return;
    setComparados((actual) =>
      comparando
        ? actual.filter((c) => !mismoLugar(c, fichaLista.lat, fichaLista.lon))
        : [...actual, { ficha: fichaLista, direccion }].slice(-MAXIMO_COMPARADOS),
    );
  }

  // Cada parte del estado de las capas se memoriza aparte: el mapa solo actualiza lo que cambió.
  const { superficie } = datos;
  const calor = useMemo<Calor | null>(
    () =>
      opciones.calor && superficie
        ? { url: api.urlSuperficie(opciones.variable), esquinas: superficie.esquinas, opacidad: opciones.opacidad }
        : null,
    [opciones.calor, opciones.variable, opciones.opacidad, superficie],
  );
  const zonaGeoJSON = useMemo(() => coleccion(zona), [zona]);
  const medicionGeoJSON = useMemo(
    () => coleccion(medicion ? { type: "LineString", coordinates: medicion } : null),
    [medicion],
  );
  const marcador = useMemo(() => (punto ? puntoGeoJSON(punto.lat, punto.lon) : VACIO), [punto]);
  const comparadosGeoJSON = useMemo<GeoJSON.FeatureCollection>(
    () => ({
      type: "FeatureCollection",
      features: comparados.map((c, i) => ({
        type: "Feature",
        properties: { numero: i + 1 },
        geometry: { type: "Point", coordinates: [c.ficha.lon, c.ficha.lat] },
      })),
    }),
    [comparados],
  );
  const capas = useMemo<EstadoCapas>(
    () => ({
      calor,
      isocrona: isocronaDelPunto?.datos ?? VACIO,
      zona: zonaGeoJSON,
      medicion: medicionGeoJSON,
      lugares: datos.lugares,
      avisos: datos.avisos,
      marcador,
      comparados: comparadosGeoJSON,
      comunas: opciones.comunas ? datos.comunas : VACIO,
    }),
    [
      calor,
      isocronaDelPunto?.datos,
      zonaGeoJSON,
      medicionGeoJSON,
      datos.lugares,
      datos.avisos,
      marcador,
      comparadosGeoJSON,
      opciones.comunas,
      datos.comunas,
    ],
  );

  return (
    <div className="app">
      <header className="barra">
        <h1 className="marca">
          Score<span className="marca-sub">Región Metropolitana</span>
        </h1>
        <Buscador
          onElegir={(r) => {
            setDestino({ lat: r.lat, lon: r.lon });
            elegirPunto(r.lat, r.lon);
          }}
        />
      </header>

      <main className={punto || zona ? "contenido con-punto" : "contenido"}>
        <div className="zona-mapa">
          <Mapa
            estiloBase={opciones.estiloBase}
            capas={capas}
            herramienta={herramienta}
            destino={destino}
            onTocar={elegirPunto}
            onZona={alDibujarZona}
            onMedicion={alMedir}
          />
          <Herramientas
            activa={herramienta}
            medicionM={medicion ? largoM(medicion) : null}
            onElegir={setHerramienta}
            onBorrarMedicion={() => setMedicion(null)}
          />
          <PanelCapas
            opciones={opciones}
            variables={superficie?.variables ?? ["puntaje"]}
            cantidadAvisos={datos.cantidadAvisos}
            cargando={datos.cargandoLugares || datos.cargandoAvisos}
            onCambiar={(cambio) => setOpciones((o) => ({ ...o, ...cambio }))}
          />
          <BandejaComparar
            puntos={comparados}
            onQuitar={(i) => setComparados((c) => c.filter((_, j) => j !== i))}
            onVer={() => setDialogo("comparar")}
            onVaciar={() => setComparados([])}
          />
          {datos.error && (
            <p className="aviso-carga" role="alert">
              {datos.error}{" "}
              <button type="button" className="enlace" onClick={datos.cerrarError}>
                Cerrar
              </button>
            </p>
          )}
        </div>
        {zona ? (
          <PanelZona estado={estadoZona} onExportar={() => setDialogo("zona")} onCerrar={() => setZona(null)} />
        ) : (
          <Panel
            ficha={ficha}
            direccion={direccion}
            precios={precios}
            isocrona={isocronaDelPunto ? (isocronaDelPunto.datos ? "visible" : "cargando") : "oculta"}
            comparando={comparando}
            puedeComparar={comparados.length < MAXIMO_COMPARADOS}
            onConsultarPrecios={consultarPrecios}
            onExportar={() => {
              // La ficha incluye arriendos: si aún no se consultaron, se piden al abrir.
              if (precios.tipo === "inicial") consultarPrecios();
              setDialogo("ficha");
            }}
            onIsocrona={alternarIsocrona}
            onComparar={alternarComparar}
            onCerrar={() => setPunto(null)}
          />
        )}
      </main>

      {dialogo === "ficha" && fichaLista && (
        <DialogoExportar
          ficha={fichaLista}
          direccion={direccion}
          precios={precios.tipo === "listo" ? precios.resumen : null}
          cargandoPrecios={precios.tipo === "cargando"}
          onCerrar={() => setDialogo(null)}
        />
      )}
      {dialogo === "zona" && zona && estadoZona.tipo === "listo" && (
        <DialogoExportarZona informe={estadoZona.informe} geometria={zona} onCerrar={() => setDialogo(null)} />
      )}
      {dialogo === "comparar" && comparados.length >= 2 && (
        <DialogoComparar puntos={comparados} onCerrar={() => setDialogo(null)} />
      )}
    </div>
  );
}
