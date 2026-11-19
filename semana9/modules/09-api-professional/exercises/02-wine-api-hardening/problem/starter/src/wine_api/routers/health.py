from fastapi import APIRouter

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.errors import ModelUnavailableError
from wine_api.schemas import ErrorResponse, HealthResponse

SERVICE_NAME = "wine-quality-prediction"

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Comprobar el estado del servicio",
    response_description="El servicio responde y el modelo está cargado.",
    responses={
        503: {
            "model": ErrorResponse,
            "description": "El modelo no está cargado: no hay predicciones posibles.",
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
        }
    },
)
def read_health(predictor: PredictorDep, request_id: RequestIdDep) -> HealthResponse:
    """Indica si el servicio está vivo y el modelo listo para predecir.

    Úsalo como sondeo de disponibilidad antes de enviar predicciones. Un `503`
    significa que el modelo no se ha podido cargar: reintenta más tarde.
    """

    if not predictor.is_ready():
        raise ModelUnavailableError()
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        model_status="ready",
        model_version=predictor.model_version,
        request_id=request_id,
    )
