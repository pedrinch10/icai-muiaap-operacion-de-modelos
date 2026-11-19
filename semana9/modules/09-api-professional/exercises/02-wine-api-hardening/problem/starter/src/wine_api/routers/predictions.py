from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.schemas import (
    VALID_FEATURES_EXAMPLE,
    ErrorResponse,
    Prediction,
    PredictionRequest,
    PredictionResponse,
)

# Mensaje de ejemplo de pydantic para un valor por encima del máximo de `alcohol`.
ALCOHOL_RANGE_MESSAGE = "Input should be less than or equal to 20"

router = APIRouter(
    prefix="/v1/predictions",
    tags=["predictions"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "El cuerpo no es JSON válido.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "invalid_json",
                            "message": "The request body is not valid JSON",
                        },
                        "request_id": "req_3f9a1c2b7d4e",
                    }
                }
            },
        },
        422: {
            "model": ErrorResponse,
            "description": "El JSON no cumple el contrato: faltan campos, sobran "
            "campos o hay valores de tipo o rango incorrectos.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "validation_error",
                            "message": "The request body does not satisfy the contract",
                            "fields": [
                                {
                                    "field": "features.alcohol",
                                    "message": ALCOHOL_RANGE_MESSAGE,
                                }
                            ],
                        },
                        "request_id": "req_8b21e0c4a9f7",
                    }
                }
            },
        },
        503: {
            "model": ErrorResponse,
            "description": "El modelo no está disponible.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "model_unavailable",
                            "message": "The prediction model is not ready",
                        },
                        "request_id": "req_c47d5e1b0a36",
                    }
                }
            },
        },
    },
)

PREDICTION_EXAMPLES = {
    "valid": {
        "summary": "Vino válido",
        "value": {"features": VALID_FEATURES_EXAMPLE},
    },
    "alcohol_out_of_range": {
        "summary": "Alcohol fuera de rango: 422",
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "alcohol": 25.0}},
    },
    "missing_ph": {
        "summary": "Falta el campo ph: 422",
        "value": {
            "features": {
                name: value
                for name, value in VALID_FEATURES_EXAMPLE.items()
                if name != "ph"
            }
        },
    },
}


@router.post(
    "",
    summary="Predecir la calidad de un vino tinto",
    response_description="Banda de calidad, confianza y versiones del modelo.",
)
def create_prediction(
    payload: Annotated[PredictionRequest, Body(openapi_examples=PREDICTION_EXAMPLES)],
    predictor: PredictorDep,
    request_id: RequestIdDep,
) -> PredictionResponse:
    """Estima la banda de calidad de un vino a partir de once variables.

    - Los once campos de `features` son obligatorios y no admiten otros.
    - Cada campo tiene un rango inclusivo (ver el esquema `WineFeatures`).
    - `confidence` va de 0 a 1 con dos decimales.
    - `served_at` está en UTC, ISO 8601 y con sufijo `Z`.

    La puntuación interna del modelo no forma parte del contrato.
    """

    output = predictor.predict(payload.features)
    return PredictionResponse(
        prediction=Prediction.model_validate(output),
        request_id=request_id,
        served_at=datetime.now(UTC),
    )
