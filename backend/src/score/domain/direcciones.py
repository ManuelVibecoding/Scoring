"""Direcciones chilenas: separar calle y número (o un cruce de calles) y normalizar nombres."""

import re
import unicodedata
from enum import StrEnum

_PREFIJOS = re.compile(
    r"^(avenida|avda|av|calle|pasaje|psje|pje|camino|cam)\.?\s+", flags=re.IGNORECASE
)
# Abreviaturas frecuentes en avisos; OSM usa la palabra completa.
_ABREVIATURAS = {
    "nte": "norte",
    "pte": "poniente",
    "ote": "oriente",
    "pdte": "presidente",
    "presid": "presidente",
    "gral": "general",
    "sta": "santa",
    "sto": "santo",
    "dr": "doctor",
    "cdte": "comandante",
    "cap": "capitan",
    "tte": "teniente",
    "mons": "monsenor",
    "avda": "avenida",
}
# El número es el último del primer tramo: "Calle 5 de Abril 120" → 120.
_CALLE_NUMERO = re.compile(
    r"^\s*(?P<calle>.*?\D)\s*(?:\bn(?:ro)?\.?\s*[°º]?\s*|#\s*)?(?P<numero>\d{1,5})\s*$",
    flags=re.IGNORECASE,
)
_RANGO = re.compile(r"(\d{1,5})\s*[-–]\s*\d{1,5}\s*$")
_CRUCE = re.compile(r"\s+(?:con|esq\.?|esquina)\s+|\s*/\s*|\s*&\s*", flags=re.IGNORECASE)


class Precision(StrEnum):
    """Qué tan bien se ubicó una dirección."""

    EXACTA = "exacta"  # coordenadas publicadas o número encontrado
    INTERPOLADA = "interpolada"  # entre dos números conocidos, o cruce de dos calles
    CALLE = "calle"  # solo se conoce la calle
    APROXIMADA = "aproximada"  # sector o comuna


def normalizar_calle(nombre: str) -> str:
    """'Av. Manquehue Nte.' y 'AVENIDA MANQUEHUE NORTE' quedan iguales: 'manquehue norte'."""
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    palabras = sin_tildes.lower().replace("'", "").replace(".", ". ").split()
    texto = " ".join(_ABREVIATURAS.get(p.rstrip("."), p) for p in palabras).replace(".", "")
    texto = " ".join(texto.split())
    anterior = None
    while anterior != texto:  # "Avenida Calle Larga" → "larga"
        anterior, texto = texto, _PREFIJOS.sub("", texto)
    return texto.strip(" .")


def _primer_tramo(direccion: str) -> str:
    tramo = direccion.split(",")[0].strip()
    return re.sub(r"^nuevo:\s*", "", tramo, flags=re.IGNORECASE)


def separar_calle_y_numero(direccion: str) -> tuple[str, int] | None:
    """'Asturias 77, Las Condes' → ('asturias', 77); 'Alcántara 900 - 1200' → ('alcantara', 900)."""
    tramo = _RANGO.sub(r"\1", _primer_tramo(direccion))
    coincidencia = _CALLE_NUMERO.match(tramo)
    if not coincidencia:
        return None
    return normalizar_calle(coincidencia["calle"]), int(coincidencia["numero"])


def separar_cruce(direccion: str) -> tuple[str, str] | None:
    """'Presidente Errázuriz / Burgos' → ('presidente errazuriz', 'burgos')."""
    partes = _CRUCE.split(_primer_tramo(direccion))
    if len(partes) != 2 or any(re.search(r"\d", p) for p in partes):
        return None
    a, b = (normalizar_calle(p) for p in partes)
    return (a, b) if a and b else None
