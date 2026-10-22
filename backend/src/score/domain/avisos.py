"""Avisos de arriendo y venta, independientes del portal del que vienen."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from score.domain.direcciones import Precision


class Operacion(StrEnum):
    ARRIENDO = "arriendo"
    VENTA = "venta"


class TipoPropiedad(StrEnum):
    DEPARTAMENTO = "departamento"
    CASA = "casa"


@dataclass(frozen=True)
class Aviso:
    fuente: str
    id: str
    operacion: Operacion
    tipo: TipoPropiedad
    comuna: str
    lat: float
    lon: float
    precio_clp: float | None
    precio_uf: float | None
    superficie_m2: float | None
    dormitorios: int | None
    banos: int | None
    horas_publicado: int | None
    url: str
    precision: Precision = Precision.EXACTA

    @property
    def ubicacion_confiable(self) -> bool:
        """Sirve para comparar con un punto (exacta o interpolada), no solo con la comuna."""
        return self.precision in (Precision.EXACTA, Precision.INTERPOLADA)

    @property
    def clp_por_m2(self) -> float | None:
        if self.precio_clp and self.superficie_m2 and self.superficie_m2 > 0:
            return self.precio_clp / self.superficie_m2
        return None


class PortalDeAvisos(Protocol):
    """Puerto: cualquier portal que pueda listar avisos de una comuna."""

    nombre: str

    def avisos_de_comuna(
        self, comuna: str, operacion: Operacion, tipo: TipoPropiedad
    ) -> list[Aviso]: ...
