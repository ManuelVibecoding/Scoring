"""Geocodificación con Nominatim (OpenStreetMap), respetando su límite de 1 consulta/s.

Las respuestas se guardan en memoria para no repetir consultas.
"""

import threading
import time
from typing import Any

import httpx

URL = "https://nominatim.openstreetmap.org"
# Rectángulo de la RM para limitar los resultados a Santiago.
CAJA_RM = "-71.72,-32.92,-69.77,-34.30"


class Nominatim:
    def __init__(self, cliente: httpx.Client) -> None:
        self._cliente = cliente
        self._candado = threading.Lock()
        self._ultima = 0.0
        self._busquedas: dict[str, list[dict[str, Any]]] = {}
        self._direcciones: dict[tuple[float, float], str | None] = {}

    def _get(self, ruta: str, parametros: dict[str, Any]) -> Any:
        with self._candado:
            espera = 1.0 - (time.monotonic() - self._ultima)
            if espera > 0:
                time.sleep(espera)
            respuesta = self._cliente.get(f"{URL}/{ruta}", params=parametros)
            self._ultima = time.monotonic()
        respuesta.raise_for_status()
        return respuesta.json()

    def buscar(self, texto: str) -> list[dict[str, Any]]:
        clave = " ".join(texto.lower().split())
        if clave not in self._busquedas:
            resultados = self._get(
                "search",
                {
                    "q": texto,
                    "format": "jsonv2",
                    "countrycodes": "cl",
                    "viewbox": CAJA_RM,
                    "bounded": 1,
                    "limit": 6,
                    "accept-language": "es",
                },
            )
            self._busquedas[clave] = [
                {"nombre": r["display_name"], "lat": float(r["lat"]), "lon": float(r["lon"])}
                for r in resultados
            ]
        return self._busquedas[clave]

    def direccion(self, lat: float, lon: float) -> str | None:
        clave = (round(lat, 4), round(lon, 4))
        if clave not in self._direcciones:
            r = self._get(
                "reverse",
                {
                    "lat": clave[0],
                    "lon": clave[1],
                    "format": "jsonv2",
                    "zoom": 17,
                    "accept-language": "es",
                },
            )
            a = r.get("address", {})
            calle = a.get("road") or a.get("pedestrian") or a.get("neighbourhood")
            numero = a.get("house_number")
            self._direcciones[clave] = (
                None if not calle else f"{calle} {numero}" if numero else str(calle)
            )
        return self._direcciones[clave]
