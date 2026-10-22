import { useEffect, useState } from "react";
import { nombrePropio } from "../../shared/formato";
import type { FichaPunto, ResumenPrecios } from "../../shared/tipos";
import { DialogoFicha } from "./DialogoFicha";
import { Ficha } from "./Ficha";
import { nombreArchivo } from "./exportar";
import { imagenDelPunto } from "./imagenSatelital";

interface Props {
  ficha: FichaPunto;
  direccion: string | null;
  precios: ResumenPrecios | null;
  cargandoPrecios: boolean;
  onCerrar: () => void;
}

/** Ficha de un punto: espera la imagen satelital y los arriendos antes de exportar. */
export function DialogoExportar({ ficha, direccion, precios, cargandoPrecios, onCerrar }: Props) {
  const [imagen, setImagen] = useState<string | null>(null);
  const [cargandoImagen, setCargandoImagen] = useState(true);

  useEffect(() => {
    let vigente = true;
    imagenDelPunto(ficha.lat, ficha.lon, ficha.h3)
      .then((i) => vigente && setImagen(i))
      .catch(() => vigente && setImagen(null))
      .finally(() => vigente && setCargandoImagen(false));
    return () => {
      vigente = false;
    };
  }, [ficha]);

  return (
    <DialogoFicha
      titulo="Exportar ficha"
      archivo={nombreArchivo(ficha.comuna, ficha.puntaje)}
      tituloPresentacion={`Score · ${nombrePropio(ficha.comuna)}`}
      preparando={
        cargandoImagen
          ? "Cargando la imagen satelital…"
          : cargandoPrecios
            ? "Consultando los arriendos cercanos para incluirlos…"
            : null
      }
      nota={precios ? "16:9, lista para una presentación." : "Sin arriendos para incluir: la ficha sale sin precios."}
      onCerrar={onCerrar}
    >
      <Ficha ficha={ficha} direccion={direccion} imagen={imagen} precios={precios} />
    </DialogoFicha>
  );
}
