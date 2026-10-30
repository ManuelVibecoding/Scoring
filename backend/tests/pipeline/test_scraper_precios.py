from datetime import date
from pathlib import Path

import httpx
import pandas as pd

from score.domain.avisos import Aviso, Operacion, TipoPropiedad
from score.pipeline.precios import muestrear


class PortalFalso:
    def __init__(self, nombre: str, falla_en: set[str] | None = None, prefijo: str = "") -> None:
        self.nombre = nombre
        self.falla_en = falla_en or set()
        self.prefijo = prefijo

    def avisos_de_comuna(
        self, comuna: str, operacion: Operacion, tipo: TipoPropiedad
    ) -> list[Aviso]:
        if comuna in self.falla_en:
            raise httpx.ConnectError("sin conexión")
        return [
            Aviso(
                self.nombre,
                f"{self.prefijo}{comuna}-{tipo}",
                operacion,
                tipo,
                comuna,
                -33.45,
                -70.6,
                500_000.0,
                None,
                50.0,
                2,
                1,
                None,
                "https://x.cl",
            )
        ]


def test_guarda_un_archivo_con_la_fecha_del_dia(tmp_path: Path) -> None:
    salida = muestrear(
        [PortalFalso("toctoc")], ["ÑUÑOA", "MAIPÚ"], tmp_path, hoy=date(2026, 10, 30)
    )
    assert salida is not None
    assert salida.name == "avisos_arriendo_20261030.parquet"
    tabla = pd.read_parquet(salida)
    assert len(tabla) == 4  # 2 comunas × departamento y casa
    assert set(tabla["fecha_muestra"]) == {"2026-10-30"}


def test_si_una_comuna_falla_conserva_sus_avisos_anteriores(tmp_path: Path) -> None:
    comunas = ["ÑUÑOA", "MAIPÚ"]
    muestrear([PortalFalso("toctoc", prefijo="v-")], comunas, tmp_path, hoy=date(2026, 10, 22))

    falla = PortalFalso("toctoc", falla_en={"MAIPÚ"}, prefijo="n-")
    salida = muestrear([falla], comunas, tmp_path, hoy=date(2026, 10, 30))

    assert salida is not None
    tabla = pd.read_parquet(salida).set_index("id")
    assert sorted(tabla.index) == [
        "n-ÑUÑOA-casa",
        "n-ÑUÑOA-departamento",
        "v-MAIPÚ-casa",
        "v-MAIPÚ-departamento",
    ]
    assert tabla.loc["v-MAIPÚ-casa", "fecha_consulta"] == "2026-10-22"
    assert tabla.loc["n-ÑUÑOA-casa", "fecha_consulta"] == "2026-10-30"


def test_si_todo_falla_no_reemplaza_los_datos(tmp_path: Path) -> None:
    muestrear([PortalFalso("toctoc")], ["ÑUÑOA"], tmp_path, hoy=date(2026, 10, 22))
    caido = PortalFalso("toctoc", falla_en={"ÑUÑOA"})
    assert muestrear([caido], ["ÑUÑOA"], tmp_path / "vacia", hoy=date(2026, 10, 30)) is None
    assert [p.name for p in tmp_path.glob("*.parquet")] == ["avisos_arriendo_20261022.parquet"]
