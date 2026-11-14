"""Contrato público de extracción técnica."""
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Criticidad(StrEnum):
    baja = 'baja'
    media = 'media'
    alta = 'alta'


class ExtraccionTecnica(BaseModel):
    """Información técnica explícita, sin inferir tecnologías ausentes."""
    model_config = ConfigDict(extra='forbid')

    tecnologias: list[NonEmptyString] = Field(description='Tecnologías explícitas; [] si no hay menciones.')
    nivel_de_criticidad: Criticidad
    resumen_tecnico: NonEmptyString = Field(description='Resumen breve y fiel al texto.')
