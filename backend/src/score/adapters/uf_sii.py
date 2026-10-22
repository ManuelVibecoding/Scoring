"""Valor de la UF del día, desde la tabla pública del SII (sin clave)."""

import re
from datetime import date

import httpx

URL = "https://www.sii.cl/valores_y_fechas/uf/uf{anio}.htm"
MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def leer_uf(html: str, dia: date) -> float | None:
    """Busca el valor del día en la tabla del mes ('41.199,85' → 41199.85)."""
    inicio = html.find(f"id='mes_{MESES[dia.month - 1]}'")
    if inicio < 0:
        return None
    fin = html.find("class='meses'", inicio + 1)
    tabla = html[inicio : fin if fin > 0 else len(html)]
    coincidencia = re.search(
        rf"<strong>{dia.day}</strong></th>\s*<td[^>]*>([\d.]+,\d+)</td>", tabla
    )
    if not coincidencia:
        return None
    return float(coincidencia.group(1).replace(".", "").replace(",", "."))


def valor_uf(cliente: httpx.Client, dia: date | None = None) -> float:
    dia = dia or date.today()
    html = cliente.get(URL.format(anio=dia.year)).raise_for_status().text
    valor = leer_uf(html, dia)
    if valor is None:
        raise ValueError(f"El SII no publica la UF del {dia.isoformat()}")
    return valor
