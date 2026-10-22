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

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
