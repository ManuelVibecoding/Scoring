import {
  type GeoJSONSource,
  type LayerSpecification,
  Map as MapaMapLibre,
  type MapMouseEvent,
  NavigationControl,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";
import { ESCALA_PUNTAJE, SENAL, TINTA } from "../../styles/tokens";
import { colorPorVariable, type Variable } from "./capa";
import "./mapa.css";

// Mapa base gris y sin color (OpenFreeMap, datos de OpenStreetMap): no compite con la capa.
const ESTILO_BASE = "https://tiles.openfreemap.org/styles/positron";
const CENTRO_SANTIAGO: [number, number] = [-70.62, -33.47];

interface Props {
  hexagonos: GeoJSON.FeatureCollection | null;
  comunas: GeoJSON.FeatureCollection | null;
  variable: Variable;
  seleccionado: string | null;
  destino: { lat: number; lon: number } | null;
  marcador: { lat: number; lon: number } | null;
  onTocar: (lat: number, lon: number) => void;
}

type Accion = (m: MapaMapLibre) => void;

export function Mapa({ hexagonos, comunas, variable, seleccionado, destino, marcador, onTocar }: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<MapaMapLibre | null>(null);
  const listo = useRef(false);
  // Lo que se pidió antes de que el estilo terminara de cargar; se aplica al cargar.
  const pendientes = useRef<Accion[]>([]);
  const alTocar = useRef(onTocar);

  useEffect(() => {
    alTocar.current = onTocar;
  }, [onTocar]);

  // Crear el mapa una sola vez.
  useEffect(() => {
    if (!contenedor.current) return;
    const m = new MapaMapLibre({
      container: contenedor.current,
      style: ESTILO_BASE,
      center: CENTRO_SANTIAGO,
      zoom: 10.3,
      minZoom: 8,
      maxZoom: 17,
      attributionControl: { compact: true },
    });
    m.addControl(new NavigationControl({ showCompass: false }), "bottom-right");
    m.on("load", () => {
      agregarCapas(m);
      listo.current = true;
      for (const accion of pendientes.current.splice(0)) accion(m);
    });
    m.on("click", (e: MapMouseEvent) => alTocar.current(e.lngLat.lat, e.lngLat.lng));
    m.getCanvas().style.cursor = "crosshair";
    mapa.current = m;
    return () => {
      listo.current = false;
      pendientes.current = [];
      m.remove();
      mapa.current = null;
    };
  }, []);

  function cuandoEsteListo(accion: Accion) {
    const m = mapa.current;
    if (m && listo.current) accion(m);
    else pendientes.current.push(accion);
  }

  useEffect(() => {
    if (hexagonos) cuandoEsteListo((m) => fuente(m, "hexagonos").setData(hexagonos));
  }, [hexagonos]);

  useEffect(() => {
    if (comunas) cuandoEsteListo((m) => fuente(m, "comunas").setData(comunas));
  }, [comunas]);

  useEffect(() => {
    cuandoEsteListo((m) =>
      m.setPaintProperty("hexagonos", "fill-color", colorPorVariable(variable, ESCALA_PUNTAJE)),
    );
  }, [variable]);

  useEffect(() => {
    cuandoEsteListo((m) => m.setFilter("seleccion", ["==", ["get", "h3"], seleccionado ?? ""]));
  }, [seleccionado]);

  useEffect(() => {
    const datos: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: marcador
        ? [{ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: [marcador.lon, marcador.lat] } }]
        : [],
    };
    cuandoEsteListo((m) => fuente(m, "marcador").setData(datos));
  }, [marcador]);

  useEffect(() => {
    if (!destino) return;
    cuandoEsteListo((m) =>
      m.flyTo({ center: [destino.lon, destino.lat], zoom: Math.max(m.getZoom(), 14.5), duration: 600 }),
    );
  }, [destino]);

  return <div ref={contenedor} className="mapa" role="application" aria-label="Mapa de la Región Metropolitana" />;
}

function fuente(m: MapaMapLibre, id: string): GeoJSONSource {
  return m.getSource(id) as GeoJSONSource;
}

function agregarCapas(m: MapaMapLibre) {
  const vacia: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
  m.addSource("hexagonos", { type: "geojson", data: vacia });
  m.addSource("comunas", { type: "geojson", data: vacia });
  m.addSource("marcador", { type: "geojson", data: vacia });
  // Los hexágonos y límites van debajo de las etiquetas del mapa base para que se lean.
  const primeraEtiqueta = m.getStyle().layers.find((c: LayerSpecification) => c.type === "symbol")?.id;
  m.addLayer(
    {
      id: "hexagonos",
      type: "fill",
      source: "hexagonos",
      paint: {
        "fill-color": colorPorVariable("puntaje", ESCALA_PUNTAJE),
        // Al acercarse, la capa se aclara para dejar ver las calles.
        "fill-opacity": ["interpolate", ["linear"], ["zoom"], 10, 0.75, 13, 0.6, 16, 0.38],
      },
    },
    primeraEtiqueta,
  );
  m.addLayer(
    {
      id: "comunas",
      type: "line",
      source: "comunas",
      paint: { "line-color": TINTA, "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.4, 14, 1.2] },
    },
    primeraEtiqueta,
  );
  m.addLayer({
    id: "seleccion",
    type: "line",
    source: "hexagonos",
    filter: ["==", ["get", "h3"], ""],
    paint: { "line-color": SENAL, "line-width": 3 },
  });
  m.addLayer({
    id: "marcador",
    type: "circle",
    source: "marcador",
    paint: {
      "circle-radius": 6,
      "circle-color": SENAL,
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": 2,
    },
  });
}
