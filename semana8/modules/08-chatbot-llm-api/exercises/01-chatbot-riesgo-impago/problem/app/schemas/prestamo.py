from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)


class PrestamoEntrada(BaseModel):
    """Las 6 variables del modelo, en el orden del enunciado."""

    # extra="forbid": rechaza campos que no existan (el LLM a veces se los inventa)
    model_config = ConfigDict(extra="forbid")

    edad: int = Field(ge=18, le=75)
    ingresos_mensuales: float = Field(gt=0)
    importe_prestamo: float = Field(gt=0)
    plazo_meses: int = Field(ge=6, le=84)
    antiguedad_laboral_anios: int = Field(ge=0, le=50)
    impagos_previos: int = Field(ge=0, le=20)

    @field_validator("antiguedad_laboral_anios")
    @classmethod
    def antiguedad_coherente_con_edad(cls, valor: int, info: ValidationInfo) -> int:
        # "edad" se declara antes, asi que ya esta validada en info.data
        edad = info.data.get("edad")
        if edad is not None and valor > edad - 16:
            raise ValueError("la antiguedad no puede ser mayor que edad - 16")
        return valor


class PrediccionSalida(BaseModel):
    probabilidad_impago: float = Field(ge=0, le=1)
    decision: Literal["aprobar", "revisar", "rechazar"]
