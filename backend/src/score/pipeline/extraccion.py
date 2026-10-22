"""Descompresión de archivos descargados hacia data/interim/<id>/."""

import shutil
import subprocess
import zipfile
from pathlib import Path


def extraer(archivo: Path, destino: Path) -> Path:
    """Extrae un .zip o .rar (los .rar con el tar de Windows/libarchive). Devuelve la carpeta."""
    destino.mkdir(parents=True, exist_ok=True)
    sufijo = archivo.suffix.lower()
    if sufijo == ".zip":
        with zipfile.ZipFile(archivo) as zf:
            zf.extractall(destino)
    elif sufijo == ".rar":
        tar = shutil.which("tar")
        if tar is None:
            raise RuntimeError("Se necesita 'tar' (libarchive) para extraer archivos .rar")
        subprocess.run([tar, "-xf", str(archivo), "-C", str(destino)], check=True)
    else:
        raise ValueError(f"Formato no soportado para extraer: {archivo.name}")
    return destino
