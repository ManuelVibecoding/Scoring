import type { Map as MapaMapLibre } from "maplibre-gl";
import {
  TerraDraw,
  TerraDrawCircleMode,
  TerraDrawLineStringMode,
  TerraDrawPolygonMode,
  TerraDrawRectangleMode,
  TerraDrawRenderMode,
} from "terra-draw";
import { TerraDrawMapLibreGLAdapter } from "terra-draw-maplibre-gl-adapter";
import { PAPEL, SENAL, TINTA } from "../../styles/tokens";

export type Herramienta = "punto" | "poligono" | "rectangulo" | "circulo" | "medir";

const MODO: Record<Exclude<Herramienta, "punto">, string> = {
  poligono: "polygon",
  rectangulo: "rectangle",
  circulo: "circle",
  medir: "linestring",
};

const TINTA_HEX = TINTA as `#${string}`;
const SENAL_HEX = SENAL as `#${string}`;
const PAPEL_HEX = PAPEL as `#${string}`;

const ESTILO_AREA = {
  fillColor: TINTA_HEX,
  fillOpacity: 0.08,
  outlineColor: TINTA_HEX,
  outlineWidth: 2,
};

/** Herramientas de dibujo (Terra Draw). Solo dibuja: el resultado lo guarda la app. */
export function crearDibujo(m: MapaMapLibre): TerraDraw {
  const dibujo = new TerraDraw({
    adapter: new TerraDrawMapLibreGLAdapter({ map: m }),
    modes: [
      new TerraDrawPolygonMode({
        styles: {
          ...ESTILO_AREA,
          closingPointColor: PAPEL_HEX,
          closingPointOutlineColor: TINTA_HEX,
          closingPointWidth: 5,
          closingPointOutlineWidth: 2,
        },
      }),
      new TerraDrawRectangleMode({ styles: ESTILO_AREA }),
      new TerraDrawCircleMode({ styles: ESTILO_AREA }),
      new TerraDrawLineStringMode({
        styles: {
          lineStringColor: SENAL_HEX,
          lineStringWidth: 3,
          closingPointColor: PAPEL_HEX,
          closingPointOutlineColor: SENAL_HEX,
          closingPointWidth: 5,
          closingPointOutlineWidth: 2,
        },
      }),
      new TerraDrawRenderMode({ modeName: "quieto", styles: {} }),
    ],
  });
  dibujo.start();
  dibujo.setMode("quieto");
  return dibujo;
}

export function modoDe(herramienta: Herramienta): string {
  return herramienta === "punto" ? "quieto" : MODO[herramienta];
}
