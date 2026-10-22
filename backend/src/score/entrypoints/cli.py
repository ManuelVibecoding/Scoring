"""Comandos de consola: `uv run score <comando>`."""

import argparse
import sys
from collections.abc import Sequence

import httpx

from score import config
from score.pipeline.descarga import descargar_fuente
from score.pipeline.fuentes import FUENTES, Fuente, buscar_fuente


def _cliente() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": config.USER_AGENT},
        follow_redirects=True,
        timeout=httpx.Timeout(60.0, connect=20.0),
    )


def _seleccionar(ids: Sequence[str], incluir_pesadas: bool) -> list[Fuente]:
    if ids:
        return [buscar_fuente(i) for i in ids]
    return [f for f in FUENTES if incluir_pesadas or not f.pesada]


def _listar(_: argparse.Namespace) -> int:
    for f in FUENTES:
        marca = " (pesada)" if f.pesada else ""
        print(f"{f.id:<28} {f.nombre}{marca}")
    return 0


def _descargar(args: argparse.Namespace) -> int:
    fallidas: list[str] = []
    with _cliente() as cliente:
        for fuente in _seleccionar(args.fuentes, args.incluir_pesadas):
            print(f"→ {fuente.id}")
            try:
                for a in descargar_fuente(fuente, config.DATOS_CRUDOS, cliente, args.forzar):
                    print(f"   {a.archivo}  {a.bytes / 1e6:.1f} MB")
            except httpx.HTTPError as error:
                print(f"   ERROR: {error}")
                fallidas.append(fuente.id)
    if fallidas:
        print(f"\nFallaron: {', '.join(fallidas)}")
    return 1 if fallidas else 0


def _comunas(_: argparse.Namespace) -> int:
    from score.pipeline import reporte_comunas
    from score.pipeline.comunas import construir_fichas

    ruta = construir_fichas(config.DATOS_CRUDOS, config.DATOS_INTERMEDIOS, config.DATOS_PROCESADOS)
    reporte = reporte_comunas.generar(ruta, config.RAIZ_PROYECTO / "docs" / "fichas-comunas.md")
    print(f"Fichas comunales: {ruta}\nReporte: {reporte}")
    return 0


def _cercanias(_: argparse.Namespace) -> int:
    from score.pipeline.cercanias import construir_cercanias

    ruta = construir_cercanias(
        config.DATOS_CRUDOS, config.DATOS_INTERMEDIOS, config.DATOS_PROCESADOS
    )
    print(f"Cercanías por hexágono: {ruta}")
    return 0


def _puntajes(_: argparse.Namespace) -> int:
    from score.pipeline.puntajes import construir_puntajes

    print(f"Puntajes por hexágono: {construir_puntajes(config.DATOS_PROCESADOS)}")
    return 0


def _precios(_: argparse.Namespace) -> int:
    import pandas as pd

    from score.adapters.portales import crear_portales
    from score.pipeline.precios import muestrear

    comunas = pd.read_parquet(config.DATOS_PROCESADOS / "comunas.parquet")["comuna"].tolist()
    with _cliente() as cliente:
        portales = crear_portales(cliente, config.DATOS_PROCESADOS)
        ruta = muestrear(portales, comunas, config.DATOS_INTERMEDIOS / "avisos")
    print(f"Muestra de avisos: {ruta}")
    return 0


def _direcciones(_: argparse.Namespace) -> int:
    from score.pipeline.direcciones import construir_indice
    from score.pipeline.osm import extraer_osm_rm

    osm = extraer_osm_rm(
        config.DATOS_CRUDOS / "osm_chile" / "chile-latest.osm.pbf",
        config.DATOS_INTERMEDIOS / "osm_rm",
    )
    comunal = next(
        (config.DATOS_INTERMEDIOS / "censo2024_cartografia_rm").glob("*_Comunal.parquet")
    )
    rutas = construir_indice(osm, comunal, config.DATOS_PROCESADOS)
    print("Índice de direcciones:", *rutas)
    return 0


def _validar(_: argparse.Namespace) -> int:
    import json
    from dataclasses import asdict

    import pandas as pd

    from score.pipeline.precios import ultima_muestra
    from score.pipeline.validacion import lugares_de_referencia, validar

    datos = pd.read_parquet(config.DATOS_PROCESADOS / "puntajes.parquet").set_index("h3")
    muestra = ultima_muestra(config.DATOS_INTERMEDIOS / "avisos")
    if muestra is None:
        print("No hay muestra de avisos: corre primero `uv run score precios`.")
        return 1
    resultado, _comparados = validar(datos, pd.read_parquet(muestra))
    salida = config.DATOS_PROCESADOS / "validacion.json"
    salida.write_text(json.dumps(asdict(resultado), indent=2, ensure_ascii=False), "utf-8")
    print(json.dumps(asdict(resultado), indent=2, ensure_ascii=False))
    print(lugares_de_referencia(datos).to_string())
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="score")
    sub = parser.add_subparsers(dest="comando", required=True)

    datos = sub.add_parser("datos", help="Fuentes de datos").add_subparsers(
        dest="accion", required=True
    )
    datos.add_parser("listar", help="Lista las fuentes registradas").set_defaults(func=_listar)

    descargar = datos.add_parser("descargar", help="Descarga fuentes a data/raw")
    descargar.add_argument("fuentes", nargs="*", help="IDs de fuentes (vacío: todas las livianas)")
    descargar.add_argument("--incluir-pesadas", action="store_true", help="Incluye OSM y ruido")
    descargar.add_argument("--forzar", action="store_true", help="Vuelve a descargar lo existente")
    descargar.set_defaults(func=_descargar)

    sub.add_parser("comunas", help="Construye las fichas de las 52 comunas").set_defaults(
        func=_comunas
    )

    sub.add_parser(
        "cercanias", help="Calcula cercanías por hexágono (red de calles + puntos de interés)"
    ).set_defaults(func=_cercanias)

    sub.add_parser("puntajes", help="Aplica el modelo de puntaje a cada hexágono").set_defaults(
        func=_puntajes
    )

    sub.add_parser(
        "precios", help="Avisos de arriendo de toda la RM (Toc Toc y Portal Inmobiliario)"
    ).set_defaults(func=_precios)

    sub.add_parser(
        "direcciones", help="Índice de direcciones de OSM para ubicar avisos"
    ).set_defaults(func=_direcciones)

    sub.add_parser(
        "validar", help="Compara el puntaje con precios de arriendo y con el ICVU"
    ).set_defaults(func=_validar)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
