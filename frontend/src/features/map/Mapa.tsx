import {
  type MapGeoJSONFeature,
  Map as MapaMapLibre,
  type MapMouseEvent,
  NavigationControl,
  Popup,
  ScaleControl,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";
import type { TerraDraw } from "terra-draw";
import { nombreFuente, nombreLugar, numero, pesos } from "../../shared/formato";
import { asegurarCapas, type EstadoCapas, FUENTES_GEOJSON, ponerCalor, ponerDatos } from "./capas";
import { crearDibujo, type Herramienta, modoDe } from "./dibujo";
import { ESTILOS, type EstiloBase } from "./estilos";
import "./mapa.css";

const CENTRO_SANTIAGO: [number, number] = [-70.62, -33.47];
const CAPAS_CON_DETALLE = ["avisos", "lugares"];
// El clic que cierra un dibujo también llega como clic al mapa: se ignora por este lapso.
const PAUSA_TRAS_DIBUJO_MS = 400;

interface Props {
  estiloBase: EstiloBase;
  capas: EstadoCapas;
  herramienta: Herramienta;
  destino: { lat: number; lon: number } | null;
  onTocar: (lat: number, lon: number) => void;
  onZona: (geometria: GeoJSON.Polygon) => void;
  onMedicion: (coordenadas: number[][]) => void;
}

export function Mapa({ estiloBase, capas, herramienta, destino, onTocar, onZona, onMedicion }: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<MapaMapLibre | null>(null);
  const dibujo = useRef<TerraDraw | null>(null);
  const listo = useRef(false);
  // Último estado pedido: se reaplica completo cuando cambia el mapa base.
  const estado = useRef(capas);
  const herramientaActual = useRef(herramienta);
  const callbacks = useRef({ onTocar, onZona, onMedicion });
  const estiloActual = useRef(estiloBase);
  const finDelDibujo = useRef(0);

  useEffect(() => {
    callbacks.current = { onTocar, onZona, onMedicion };
  }, [onTocar, onZona, onMedicion]);

  // Crear el mapa una sola vez.
  useEffect(() => {
    if (!contenedor.current) return;
    const m = new MapaMapLibre({
      container: contenedor.current,
      style: ESTILOS[estiloActual.current],
      center: CENTRO_SANTIAGO,
      zoom: 10.6,
      minZoom: 8,
      maxZoom: 18,
      attributionControl: { compact: true },
    });
    m.addControl(new NavigationControl({ showCompass: false }), "bottom-right");
    m.addControl(new ScaleControl({ unit: "metric" }), "bottom-left");

    m.on("style.load", () => {
      asegurarCapas(m, estado.current, estiloActual.current === "satelite");
      dibujo.current?.stop();
      dibujo.current = crearDibujo(m);
      dibujo.current.setMode(modoDe(herramientaActual.current));
      dibujo.current.on("finish", (id) => {
        const d = dibujo.current;
        const figura = d?.getSnapshotFeature(id);
        if (!d || !figura) return;
        finDelDibujo.current = performance.now();
        if (figura.geometry.type === "Polygon") callbacks.current.onZona(figura.geometry);
        if (figura.geometry.type === "LineString") callbacks.current.onMedicion(figura.geometry.coordinates);
        d.clear();
      });
      listo.current = true;
    });

    m.on("click", (e: MapMouseEvent) => {
      if (herramientaActual.current !== "punto") return;
      if (performance.now() - finDelDibujo.current < PAUSA_TRAS_DIBUJO_MS) return;
      const presentes = CAPAS_CON_DETALLE.filter((c) => m.getLayer(c));
      const [tocado] = presentes.length ? m.queryRenderedFeatures(e.point, { layers: presentes }) : [];
      if (tocado) {
        mostrarDetalle(m, tocado);
        return;
      }
      callbacks.current.onTocar(e.lngLat.lat, e.lngLat.lng);
    });
    for (const capa of CAPAS_CON_DETALLE) {
      m.on("mouseenter", capa, () => (m.getCanvas().style.cursor = "pointer"));
      m.on("mouseleave", capa, () => (m.getCanvas().style.cursor = ""));
    }
    mapa.current = m;
    return () => {
      listo.current = false;
      dibujo.current?.stop();
      dibujo.current = null;
      m.remove();
      mapa.current = null;
    };
  }, []);

  // Mapa base.
  useEffect(() => {
    const m = mapa.current;
    if (!m || estiloActual.current === estiloBase) return;
    estiloActual.current = estiloBase;
    listo.current = false;
    m.setStyle(ESTILOS[estiloBase]);
  }, [estiloBase]);

  // Datos de las capas: se guardan siempre y se aplican si el mapa está listo.
  useEffect(() => {
    const anterior = estado.current;
    estado.current = capas;
    const m = mapa.current;
    if (!m || !listo.current) return;
    for (const f of FUENTES_GEOJSON) if (anterior[f] !== capas[f]) ponerDatos(m, f, capas[f]);
    if (anterior.calor !== capas.calor) ponerCalor(m, capas.calor, anterior.calor);
  }, [capas]);

  // Herramienta activa.
  useEffect(() => {
    herramientaActual.current = herramienta;
    if (listo.current) dibujo.current?.setMode(modoDe(herramienta));
    const lienzo = mapa.current?.getCanvas();
    if (lienzo) lienzo.style.cursor = herramienta === "punto" ? "crosshair" : "";
  }, [herramienta]);

  useEffect(() => {
    if (!destino) return;
    const m = mapa.current;
    m?.flyTo({ center: [destino.lon, destino.lat], zoom: Math.max(m.getZoom(), 15), duration: 600 });
  }, [destino]);

  return <div ref={contenedor} className="mapa" role="application" aria-label="Mapa de la Región Metropolitana" />;
}

/** Ventanita con el detalle de un lugar o un aviso (armada con nodos, sin HTML externo). */
function mostrarDetalle(m: MapaMapLibre, rasgo: MapGeoJSONFeature) {
  const p = rasgo.properties as Record<string, string | number | null>;
  const caja = document.createElement("div");
  caja.className = "detalle";
  const titulo = document.createElement("strong");
  const sub = document.createElement("span");
  if (rasgo.layer.id === "avisos") {
    titulo.textContent = `${pesos(Number(p.precio_clp))} al mes`;
    const m2 = p.superficie_m2 ? ` · ${numero(Number(p.superficie_m2))} m²` : "";
    const dorm = p.dormitorios ? ` · ${String(p.dormitorios)}D` : "";
    sub.textContent = `${String(p.tipo)}${m2}${dorm} · ${nombreFuente(String(p.fuente))}`;
    caja.append(titulo, sub);
    if (typeof p.url === "string" && p.url.startsWith("https://")) {
      const enlace = document.createElement("a");
      enlace.href = p.url;
      enlace.target = "_blank";
      enlace.rel = "noreferrer";
      enlace.textContent = "Ver aviso";
      caja.append(enlace);
    }
  } else {
    titulo.textContent = nombreLugar(typeof p.nombre === "string" ? p.nombre : null);
    sub.textContent = String(p.etiqueta ?? p.categoria ?? "");
    caja.append(titulo, sub);
  }
  const geometria = rasgo.geometry;
  if (geometria.type !== "Point") return;
  new Popup({ closeButton: false, offset: 10 })
    .setLngLat(geometria.coordinates as [number, number])
    .setDOMContent(caja)
    .addTo(m);
}
