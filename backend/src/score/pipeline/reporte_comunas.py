"""Genera docs/fichas-comunas.md a partir de data/processed/comunas.parquet."""

from collections.abc import Callable
from datetime import date
from pathlib import Path

import pandas as pd


def _miles(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def _pct(x: float) -> str:
    return "—" if pd.isna(x) else f"{x * 100:.1f}%".replace(".", ",")


def _decimal(x: float) -> str:
    return "—" if pd.isna(x) else f"{x:.1f}".replace(".", ",")


def _titulo(nombre: object) -> str:
    """'SAN JOSÉ DE MAIPO' → 'San José de Maipo'."""
    menores = {"De", "Del", "La", "Las", "Los", "Y"}
    palabras = str(nombre).title().split()
    return " ".join(p.lower() if i > 0 and p in menores else p for i, p in enumerate(palabras))


def _texto(x: object) -> str:
    return "—" if pd.isna(x) else str(x)  # type: ignore[call-overload]


COLUMNAS: list[tuple[str, str, Callable[[float], str]]] = [
    ("poblacion", "Población", _miles),
    ("densidad_hab_km2", "Hab/km²", _miles),
    ("escolaridad_promedio", "Escolaridad (años)", _decimal),
    ("pct_pobreza_ingresos", "Pobreza ingresos", _pct),
    ("pct_pobreza_multidimensional", "Pobreza multidim.", _pct),
    ("tasa_dmcs_100k", "DMCS /100 mil", _miles),
    ("tasa_delitos_violentos_100k", "Violentos /100 mil", _miles),
    ("pct_hogares_arrendatarios", "Hogares arrendatarios", _pct),
    ("estaciones_metro", "Metro", _miles),
    ("paraderos_bus", "Paraderos", _miles),
    ("servicios_urgencia", "Urgencias", _miles),
    ("establecimientos_educacionales", "Colegios", _miles),
    ("icvu_nivel", "ICVU 2025", _texto),
]


def generar(comunas: Path, destino: Path) -> Path:
    f = pd.read_parquet(comunas).sort_values(["provincia", "comuna"])
    anio = int(f["anio_delitos"].max())
    encabezado = "| Comuna | Provincia | " + " | ".join(t for _, t, _ in COLUMNAS) + " |"
    separador = "|---|---|" + "|".join("---:" for _ in COLUMNAS) + "|"
    filas = [
        f"| {_titulo(r.comuna)} | {_titulo(r.provincia)} | "
        + " | ".join(fmt(getattr(r, col)) for col, _, fmt in COLUMNAS)
        + " |"
        for r in f.itertuples()
    ]
    texto = (
        f"""# Fichas de las 52 comunas de la Región Metropolitana

Generado automáticamente el {date.today().isoformat()} con `uv run score comunas`.
Datos completos (43 indicadores por comuna) en `data/processed/comunas.csv`.

**Fuentes:** Censo 2024 (INE), pobreza comunal SAE Casen 2024 (MDSF), casos policiales
{anio} (CEAD), establecimientos de salud (Minsal, jun-2026), directorio de establecimientos
educacionales 2025 (Mineduc), GTFS Red Metropolitana (DTPM, oct-2026), ICVU 2025
(CChC + IEUT UC).

**Cómo leerla:**
- **DMCS:** delitos de mayor connotación social por cada 100 mil habitantes en {anio}.
  Las comunas con mucho comercio u oficinas (Santiago, Providencia, Estación Central)
  aparecen infladas porque se divide por residentes, no por la gente que circula.
- **Violentos:** robos con violencia o intimidación, robo violento de vehículo, robo por
  sorpresa y homicidios.
- **Paraderos:** solo la red RED/Transantiago; las comunas rurales tienen buses rurales
  que no están en el GTFS, por eso aparecen con 0.
- **ICVU:** el informe publica niveles, no puntajes; cubre 42 comunas de la RM. "—" = sin dato.

{encabezado}
{separador}
"""
        + "\n".join(filas)
        + "\n"
    )
    destino.write_text(texto, encoding="utf-8")
    return destino
