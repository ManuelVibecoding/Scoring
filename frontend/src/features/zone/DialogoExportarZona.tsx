import { useEffect, useState } from "react";
import type { InformeZona } from "../../shared/tipos";
import { DialogoFicha } from "../export/DialogoFicha";
import { nombreArchivo } from "../export/exportar";
import { imagenDeZona } from "../export/imagenSatelital";
import { FichaZona } from "./FichaZona";
import { tituloZona } from "./titulo";

interface Props {
  informe: InformeZona;
  geometria: GeoJSON.Polygon;
  onCerrar: () => void;
}

export function DialogoExportarZona({ informe, geometria, onCerrar }: Props) {
  const [imagen, setImagen] = useState<string | null>(null);
  const [cargandoImagen, setCargandoImagen] = useState(true);

  useEffect(() => {
    let vigente = true;
    imagenDeZona(geometria)
      .then((i) => vigente && setImagen(i))
      .catch(() => vigente && setImagen(null))
      .finally(() => vigente && setCargandoImagen(false));
    return () => {
      vigente = false;
    };
  }, [geometria]);

  const comunaPrincipal = Object.keys(informe.resumen.comunas)[0] ?? "rm";
  return (
    <DialogoFicha
      titulo="Exportar ficha de la zona"
      archivo={nombreArchivo(`zona ${comunaPrincipal}`, informe.resumen.puntaje)}
      tituloPresentacion={`Score · ${tituloZona(informe)}`}
      preparando={cargandoImagen ? "Cargando la imagen satelital…" : null}
      nota="16:9, lista para una presentación."
      onCerrar={onCerrar}
    >
      <FichaZona informe={informe} imagen={imagen} />
    </DialogoFicha>
  );
}
