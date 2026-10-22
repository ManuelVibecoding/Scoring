"""Rutas y parámetros globales. Se pueden sobrescribir con variables de entorno."""

import os
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
DATOS = Path(os.environ.get("SCORE_DATOS", RAIZ_PROYECTO / "data"))

DATOS_CRUDOS = DATOS / "raw"
DATOS_INTERMEDIOS = DATOS / "interim"
DATOS_PROCESADOS = DATOS / "processed"

# Código CUT de la Región Metropolitana: las comunas de la RM empiezan con 13.
REGION_METROPOLITANA = 13

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Score/0.1 (uso personal)"
