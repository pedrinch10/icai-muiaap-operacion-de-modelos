"""Contratos públicos de la Wine Quality API.

Punto de partida: la API de S8 valida la entrada, pero la salida todavía es un
`dict` sin contrato. En S9 la respuesta también pasa a ser un contrato.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

VALID_FEATURES_EXAMPLE = {
    "fixed_acidity": 7.4,
    "volatile_acidity": 0.7,
    "citric_acid": 0.0,
    "residual_sugar": 1.9,
    "chlorides": 0.076,
    "free_sulfur_dioxide": 11.0,
    "total_sulfur_dioxide": 34.0,
    "density": 0.9978,
    "ph": 3.51,
    "sulphates": 0.56,
    "alcohol": 9.4,
}


class WineFeatures(BaseModel):
    """Once variables fisicoquímicas de un vino tinto, con rangos inclusivos."""

    model_config = ConfigDict(extra="forbid", strict=True)

    fixed_acidity: float = Field(
        ge=0, le=20, description="Acidez fija (g/dm³ de ácido tartárico)."
    )
    volatile_acidity: float = Field(
        ge=0, le=2, description="Acidez volátil (g/dm³ de ácido acético)."
    )
    citric_acid: float = Field(ge=0, le=2, description="Ácido cítrico (g/dm³).")
    residual_sugar: float = Field(ge=0, le=20, description="Azúcar residual (g/dm³).")
    chlorides: float = Field(ge=0, le=1, description="Cloruros (g/dm³ de NaCl).")
    free_sulfur_dioxide: float = Field(
        ge=0, le=100, description="Dióxido de azufre libre (mg/dm³)."
    )
    total_sulfur_dioxide: float = Field(
        ge=0, le=300, description="Dióxido de azufre total (mg/dm³)."
    )
    density: float = Field(ge=0.98, le=1.01, description="Densidad (g/cm³).")
    ph: float = Field(ge=2.5, le=4.5, description="pH (escala de acidez).")
    sulphates: float = Field(
        ge=0, le=3, description="Sulfatos (g/dm³ de sulfato de potasio)."
    )
    alcohol: float = Field(ge=5, le=20, description="Alcohol (% vol.).")


class PredictionRequest(BaseModel):
    """Cuerpo de `POST /v1/predictions`."""

    model_config = ConfigDict(extra="forbid")

    features: WineFeatures


class QualityBand(StrEnum):
    """Bandas de calidad que entiende el consumidor."""

    NEEDS_REVIEW = "needs_review"
    ACCEPTABLE = "acceptable"
    EXCELLENT = "excellent"


class Prediction(BaseModel):
    """Predicción pública: no incluye puntuaciones internas del modelo."""

    model_config = ConfigDict(from_attributes=True)

    quality_band: QualityBand = Field(description="Banda de calidad estimada.")
    confidence: float = Field(ge=0, le=1, description="Confianza (0 a 1).")
    model_version: str = Field(description="Versión del modelo que predijo.")
    preprocessing_version: str = Field(description="Versión del preprocesado.")

    @field_serializer("confidence")
    def _round_confidence(self, value: float) -> float:
        """El contrato público expone dos decimales; el modelo da más."""

        return round(value, 2)


class PredictionResponse(BaseModel):
    """Respuesta de `POST /v1/predictions`."""

    prediction: Prediction
    request_id: str = Field(description="Identificador de la petición (X-Request-Id).")
    served_at: datetime = Field(
        description="Momento de la respuesta en UTC, ISO 8601 con sufijo Z."
    )

    @field_serializer("served_at")
    def _serialize_served_at(self, value: datetime) -> str:
        """UTC, ISO 8601, milisegundos y sufijo Z: 2026-10-20T09:15:00.123Z."""

        return (
            value.astimezone(UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )


class HealthResponse(BaseModel):
    """Estado del servicio y del modelo cargado."""

    status: Literal["ok"]
    service: str
    model_status: Literal["ready"]
    model_version: str
    request_id: str


class ErrorCode(StrEnum):
    """Códigos estables: el cliente programa contra ellos, no contra el texto."""

    INVALID_JSON = "invalid_json"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    HTTP_ERROR = "http_error"
    MODEL_UNAVAILABLE = "model_unavailable"
    INTERNAL_ERROR = "internal_error"


class FieldError(BaseModel):
    """Un campo del cuerpo que incumple el contrato."""

    field: str = Field(examples=["features.alcohol"])
    message: str = Field(examples=["Input should be a valid number"])


class ErrorDetail(BaseModel):
    """Descripción estable del error."""

    code: ErrorCode
    message: str
    fields: list[FieldError] | None = Field(
        default=None, description="Solo presente en errores de validación."
    )


class ErrorResponse(BaseModel):
    """Sobre común de todas las respuestas de error (contrato de S7)."""

    error: ErrorDetail
    request_id: str
