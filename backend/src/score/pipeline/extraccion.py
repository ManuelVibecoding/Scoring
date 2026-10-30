"""Descompresión de archivos descargados hacia data/interim/<id>/."""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def asegurar_extraido(raw: Path, interim: Path, fuente: str, archivo: str) -> Path:
    """Extrae data/raw/<fuente>/<archivo> a data/interim/<fuente>/ si aún no se hizo."""
    destino = interim / fuente
    if not destino.exists() or not any(destino.iterdir()):
        extraer(raw / fuente / archivo, destino)
    return destino


def extraer(archivo: Path, destino: Path) -> Path:
    """Extrae un .zip o .rar (los .rar con un tar de libarchive). Devuelve la carpeta."""
    destino.mkdir(parents=True, exist_ok=True)
    sufijo = archivo.suffix.lower()
    if sufijo == ".zip":
        with zipfile.ZipFile(archivo) as zf:
            zf.extractall(destino)
    elif sufijo == ".rar":
        subprocess.run([tar_para_rar(), "-xf", str(archivo), "-C", str(destino)], check=True)
    else:
        raise ValueError(f"Formato no soportado para extraer: {archivo.name}")
    return destino


def tar_para_rar() -> str:
    """Un tar que lea .rar (libarchive).

    En Windows se usa el del sistema: el tar de Git, que puede aparecer antes en el PATH, no
    lee .rar ni entiende rutas como C:\\.
    """
    if sys.platform == "win32":
        del_sistema = Path(os.environ.get("SYSTEMROOT", "C:/Windows")) / "System32" / "tar.exe"
        if del_sistema.exists():
            return str(del_sistema)
    for nombre in ("bsdtar", "tar"):
        if ruta := shutil.which(nombre):
            return ruta
    raise RuntimeError(
        "Se necesita bsdtar (libarchive) para extraer archivos .rar. En Linux: "
        "sudo apt install libarchive-tools. En macOS ya viene instalado."
    )
