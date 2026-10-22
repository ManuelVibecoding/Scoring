"""Utilidades para cruzar fuentes que nombran las comunas de formas distintas."""

import unicodedata


def normalizar_nombre(nombre: str) -> str:
    """'Ñuñoa', 'NUNOA' y ' ñuñoa ' quedan iguales: sin tildes, minúsculas, sin espacios extra."""
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.lower().replace("'", "").split())


def a_numero(texto: str | None) -> float | None:
    """Convierte '-33,4448' o ' 12 ' a número. Vacío o '*' (dato reservado) devuelve None."""
    if texto is None:
        return None
    limpio = texto.strip().replace(",", ".")
    if not limpio or limpio == "*":
        return None
    try:
        return float(limpio)
    except ValueError:
        return None
