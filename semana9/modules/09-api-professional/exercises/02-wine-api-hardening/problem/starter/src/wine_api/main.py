"""Punto de entrada de la API: `fastapi dev` usa `wine_api.main:app`."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from wine_api.errors import install_error_handlers
from wine_api.predictor import Predictor, build_predictor
from wine_api.request_id import request_id_middleware
from wine_api.routers import health, predictions

API_VERSION = "1.1.0"  # S9.1c añade `served_at`: cambio compatible, sube el menor.

API_SUMMARY = "Predicción de la calidad de un vino tinto."
API_DESCRIPTION = """
API de ejemplo del curso: devuelve una banda de calidad y una confianza a partir
de once variables fisicoquímicas. El modelo es determinista y docente.

**Identificador de petición.** Cada respuesta, correcta o de error, lleva un
`request_id` en el cuerpo y en la cabecera `X-Request-Id`. Cítalo al comunicar
una incidencia.

**Errores.** Todos los errores comparten un único sobre:
`{"error": {"code", "message", "fields"}, "request_id"}`. Programa contra
`error.code`, no contra `message`; `fields` solo aparece en errores de
validación (422).
"""
OPENAPI_TAGS = [
    {"name": "health", "description": "Estado del servicio y del modelo."},
    {"name": "predictions", "description": "Inferencia de calidad del vino."},
]


def create_app(predictor: Predictor | None = None) -> FastAPI:
    """Crea la aplicación; los tests inyectan su propio predictor."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.predictor = predictor or build_predictor(
            os.environ.get("WINE_API_MODE", "ready")
        )
        yield

    app = FastAPI(
        title="Wine Quality API",
        version=API_VERSION,
        summary=API_SUMMARY,
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )
    app.middleware("http")(request_id_middleware)
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(predictions.router)
    return app


app = create_app()
