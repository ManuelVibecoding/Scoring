"""API HTTP de la app (FastAPI). Se arma con `crear_app` para poder probarla con dobles.

Correr en desarrollo:
    uv run uvicorn score.entrypoints.api:app_por_defecto --factory --port 8000
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query

from score import config
from score.domain.avisos import PortalDeAvisos
from score.services.consulta_punto import consultar_punto
from score.services.precios import precios_cercanos
from score.services.puertos import CacheAvisos, Geocodificador, RepositorioPuntajes

LAT = Query(..., ge=-34.4, le=-32.8, description="Latitud dentro de la RM")
LON = Query(..., ge=-71.8, le=-69.7, description="Longitud dentro de la RM")


@dataclass
class Dependencias:
    repositorio: RepositorioPuntajes
    cache: CacheAvisos
    portal: PortalDeAvisos
    geocodificador: Geocodificador


def crear_app(dep: Dependencias) -> FastAPI:
    app = FastAPI(title="Score", version="0.1.0")

    @app.get("/api/salud")
    def salud() -> dict[str, str]:
        return {"estado": "ok"}

    @app.get("/api/capa")
    def capa() -> dict[str, Any]:
        """Puntajes de todos los hexágonos en formato columnar (más liviano que una lista)."""
        tabla = dep.repositorio.capa()
        return {
            "h3": tabla.index.tolist(),
            **{c: tabla[c].where(tabla[c].notna(), None).tolist() for c in tabla.columns},
        }

    @app.get("/api/comunas")
    def comunas() -> dict[str, Any]:
        return dep.repositorio.contorno_comunas()

    @app.get("/api/punto")
    def punto(lat: float = LAT, lon: float = LON) -> dict[str, Any]:
        ficha = consultar_punto(dep.repositorio, lat, lon)
        if ficha is None:
            raise HTTPException(404, "Este punto está lejos de cualquier zona habitada.")
        return asdict(ficha)

    @app.get("/api/precios")
    def precios(lat: float = LAT, lon: float = LON) -> dict[str, Any]:
        ficha = consultar_punto(dep.repositorio, lat, lon)
        if ficha is None:
            raise HTTPException(404, "Este punto está lejos de cualquier zona habitada.")
        try:
            resumen, fecha = precios_cercanos(
                dep.cache, dep.portal, ficha.comuna, lat, lon, datetime.now()
            )
        except httpx.HTTPError as error:
            raise HTTPException(502, f"El portal de avisos no respondió: {error}") from error
        datos = asdict(resumen)
        datos["actualizado"] = fecha.isoformat() if fecha else None
        datos["fuente"] = dep.portal.nombre
        return datos

    @app.get("/api/buscar")
    def buscar(q: str = Query(..., min_length=3, max_length=120)) -> list[dict[str, Any]]:
        try:
            return dep.geocodificador.buscar(q)
        except httpx.HTTPError as error:
            raise HTTPException(502, "El buscador de direcciones no respondió.") from error

    @app.get("/api/direccion")
    def direccion(lat: float = LAT, lon: float = LON) -> dict[str, str | None]:
        try:
            return {"direccion": dep.geocodificador.direccion(lat, lon)}
        except httpx.HTTPError:
            return {"direccion": None}

    return app


def app_por_defecto() -> FastAPI:
    """Arma la app con los datos reales del pipeline y los adaptadores de producción."""
    from score.adapters.cache_avisos import CacheAvisosDuckDB
    from score.adapters.nominatim import Nominatim
    from score.adapters.repositorio_parquet import RepositorioParquet
    from score.adapters.toctoc import TocToc

    cliente = httpx.Client(
        headers={"User-Agent": config.USER_AGENT}, follow_redirects=True, timeout=30.0
    )
    cartografia = next(
        (config.DATOS_INTERMEDIOS / "censo2024_cartografia_rm").glob("*_Comunal.parquet")
    )
    cache = CacheAvisosDuckDB(config.DATOS / "cache" / "avisos.duckdb")
    muestras = sorted((config.DATOS_INTERMEDIOS / "avisos").glob("toctoc_arriendo_*.parquet"))
    if muestras:
        cache.importar_muestra(muestras[-1])
    return crear_app(
        Dependencias(
            repositorio=RepositorioParquet(config.DATOS_PROCESADOS, cartografia),
            cache=cache,
            portal=TocToc(cliente),
            geocodificador=Nominatim(cliente),
        )
    )
