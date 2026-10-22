"""Verifica que las capas respeten la regla de dependencias.

entrypoints → services → domain; adapters implementa puertos de services.
Si alguien importa una capa prohibida, esta prueba falla.
"""

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1] / "src" / "score"

# Capas que cada capa NO puede importar.
PROHIBIDAS: dict[str, set[str]] = {
    "domain": {"services", "adapters", "entrypoints", "pipeline"},
    "services": {"adapters", "entrypoints", "pipeline"},
    "adapters": {"entrypoints"},
}


def _capas_importadas(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    capas: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos = [alias.name for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            modulos = [nodo.module]
        else:
            continue
        for modulo in modulos:
            partes = modulo.split(".")
            if partes[0] == "score" and len(partes) > 1:
                capas.add(partes[1])
    return capas


@pytest.mark.parametrize("capa", sorted(PROHIBIDAS))
def test_capa_no_importa_capas_prohibidas(capa: str) -> None:
    violaciones = [
        f"{archivo.relative_to(RAIZ)} importa score.{importada}"
        for archivo in (RAIZ / capa).rglob("*.py")
        for importada in _capas_importadas(archivo) & PROHIBIDAS[capa]
    ]
    assert not violaciones, "\n".join(violaciones)
