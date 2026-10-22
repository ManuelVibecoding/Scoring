"""API HTTP de la app (FastAPI). Se arma con `crear_app` para poder probarla con dobles.

Correr en desarrollo:
    uv run uvicorn score.entrypoints.api:app_por_defecto --factory --port 8000
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Protocol

import httpx
from fastapi import Body, FastAPI, HTTPException, Path, Query, Response

from score import config
from score.domain.avisos import PortalDeAvisos
from score.domain.modelo import MODELO
from score.services.consulta_punto import consultar_punto
from score.services.precios import precios_cercanos
from score.services.puertos import (
    CacheAvisos,
    Geocodificador,
    MotorDeCercanias,
    RepositorioPuntajes,
)
from score.services.zona import ZonaInvalidaError, informe_zona

LAT = Query(..., ge=-34.4, le=-32.8, description="Latitud dentro de la RM")
GEOMETRIA = Body(..., embed=True, description="Polígono GeoJSON de la zona")
LON = Query(..., ge=-71.8, le=-69.7, description="Longitud dentro de la RM")
VARIABLES_SUPERFICIE = ("puntaje", *(d.id for d in MODELO))
CATEGORIAS_LUGARES = (
    "metro",
    "tren",
    "colegio",
    "jardin",
    "cesfam",
    "urgencia",
    "hospital_clinica",
    "supermercado",
    "farmacia",
    "banco",
    "mall",
    "policia",
    "bomberos",
)


class FuenteDeSuperficies(Protocol):
    @property
    def esquinas(self) -> list[list[float]]: ...

    def png(self, variable: str) -> bytes: ...


@dataclass
class Dependencias:
    repositorio: RepositorioPuntajes
    cache: CacheAvisos
    portales: list[PortalDeAvisos]
    geocodificador: Geocodificador
    motor: MotorDeCercanias | None = None
    superficies: FuenteDeSuperficies | None = None


def _puntos_geojson(filas: list[dict[Any, Any]]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {k: v for k, v in f.items() if k not in ("lat", "lon")},
                "geometry": {"type": "Point", "coordinates": [f["lon"], f["lat"]]},
            }
            for f in filas
        ],
    }


def crear_app(dep: Dependencias) -> FastAPI:
    app = FastAPI(title="Score", version="0.2.0")

    def ficha_o_404(lat: float, lon: float) -> Any:
        ficha = consultar_punto(dep.repositorio, lat, lon, dep.motor)
        if ficha is None:
            raise HTTPException(404, "Este punto está lejos de cualquier zona habitada.")
        return ficha

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

    @app.get("/api/superficie")
    def superficie() -> dict[str, Any]:
        if dep.superficies is None:
            raise HTTPException(503, "La capa de calor no está disponible.")
        return {"esquinas": dep.superficies.esquinas, "variables": list(VARIABLES_SUPERFICIE)}

    @app.get("/api/superficie/{variable}.png")
    def superficie_png(variable: str = Path(...)) -> Response:
        if dep.superficies is None or variable not in VARIABLES_SUPERFICIE:
            raise HTTPException(404, "Capa desconocida.")
        return Response(
            dep.superficies.png(variable),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    @app.get("/api/comunas")
    def comunas() -> dict[str, Any]:
        return dep.repositorio.contorno_comunas()

    @app.get("/api/punto")
    def punto(lat: float = LAT, lon: float = LON) -> dict[str, Any]:
        return asdict(ficha_o_404(lat, lon))

    @app.get("/api/isocrona")
    def isocrona(lat: float = LAT, lon: float = LON) -> dict[str, Any]:
        if dep.motor is None:
            raise HTTPException(503, "Las isócronas no están disponibles.")
        return dep.motor.isocrona(lat, lon, (5, 10, 15))

    @app.get("/api/precios")
    def precios(lat: float = LAT, lon: float = LON) -> dict[str, Any]:
        ficha = ficha_o_404(lat, lon)
        try:
            resumen, fecha = precios_cercanos(
                dep.cache, dep.portales, ficha.comuna, lat, lon, datetime.now()
            )
        except httpx.HTTPError as error:
            raise HTTPException(502, f"El portal de avisos no respondió: {error}") from error
        datos = asdict(resumen)
        datos["actualizado"] = fecha.isoformat() if fecha else None
        datos["fuentes"] = [p.nombre for p in dep.portales]
        return datos

    @app.post("/api/zona")
    def zona(geometria: dict[str, Any] = GEOMETRIA) -> dict[str, Any]:
        try:
            return asdict(informe_zona(dep.repositorio, dep.cache, geometria))
        except ZonaInvalidaError as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/lugares")
    def lugares(categorias: str = Query(..., max_length=300)) -> dict[str, Any]:
        pedidas = [c for c in categorias.split(",") if c in CATEGORIAS_LUGARES]
        tabla = dep.repositorio.lugares(pedidas)
        filas = tabla[["categoria", "nombre", "lat", "lon"]].astype(object)
        return _puntos_geojson(filas.where(filas.notna(), None).to_dict("records"))

    @app.get("/api/avisos")
    def avisos() -> dict[str, Any]:
        tabla = dep.cache.todos()
        tabla = tabla.astype(object).where(tabla.notna(), None)
        return _puntos_geojson(tabla.to_dict("records"))

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
    from score.adapters.motor_cercanias import MotorCercanias
    from score.adapters.nominatim import Nominatim
    from score.adapters.portales import crear_portales
    from score.adapters.repositorio_parquet import RepositorioParquet
    from score.adapters.superficie import Superficies
    from score.pipeline.precios import ultima_muestra

    cliente = httpx.Client(
        headers={"User-Agent": config.USER_AGENT}, follow_redirects=True, timeout=30.0
    )
    cartografia = next(
        (config.DATOS_INTERMEDIOS / "censo2024_cartografia_rm").glob("*_Comunal.parquet")
    )
    cache = CacheAvisosDuckDB(config.DATOS / "cache" / "avisos.duckdb")
    muestra = ultima_muestra(config.DATOS_INTERMEDIOS / "avisos")
    if muestra:
        cache.importar_muestra(muestra)
    repositorio = RepositorioParquet(config.DATOS_PROCESADOS, cartografia)
    return crear_app(
        Dependencias(
            repositorio=repositorio,
            cache=cache,
            portales=crear_portales(cliente, config.DATOS_PROCESADOS),
            geocodificador=Nominatim(cliente),
            motor=MotorCercanias.desde_carpeta(config.DATOS_PROCESADOS / "motor"),
            superficies=Superficies(repositorio.tabla()),
        )
    )
