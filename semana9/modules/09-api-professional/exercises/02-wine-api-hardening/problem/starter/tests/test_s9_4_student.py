"""S9.4 — Tests que escribe el alumnado.

Cada test empieza en rojo con `pytest.fail`. Sustituye esa línea por el test
real; la entrega se considera completa cuando toda la suite está en verde.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wine_api.dependencies import get_predictor
from wine_api.export_openapi import render_openapi
from wine_api.predictor import UnavailablePredictor

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "contracts" / "openapi.json"


def test_prediction_returns_503_when_model_is_unavailable(
    client: TestClient, valid_payload: dict
) -> None:
    client.app.dependency_overrides[get_predictor] = lambda: UnavailablePredictor()
    try:
        response = client.post("/v1/predictions", json=valid_payload)
    finally:
        client.app.dependency_overrides.pop(get_predictor, None)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"
    assert get_predictor not in client.app.dependency_overrides


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("alcohol", 4.99),  # justo por debajo del mínimo
        ("alcohol", 20.01),  # justo por encima del máximo
        ("ph", None),
        ("density", "denso"),
        ("chlorides", -0.001),
        ("citric_acid", True),  # un booleano no es un número
    ],
)
def test_out_of_contract_values_are_rejected(
    client: TestClient, valid_payload: dict, field: str, value: object
) -> None:
    valid_payload["features"][field] = value

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 422
    fields = [item["field"] for item in response.json()["error"]["fields"]]
    assert fields == [f"features.{field}"]


@pytest.mark.parametrize("alcohol", [5, 20])
def test_range_limits_are_inclusive(
    client: TestClient, valid_payload: dict, alcohol: int
) -> None:
    valid_payload["features"]["alcohol"] = alcohol

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 200


def test_openapi_matches_versioned_contract() -> None:
    assert CONTRACT_PATH.exists(), (
        "Falta contracts/openapi.json: genera el snapshot con "
        "`uv run python -m wine_api.export_openapi`."
    )
    versioned = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert json.loads(render_openapi()) == versioned, (
        "El contrato OpenAPI ha cambiado: revisa si es compatible, sube la "
        "versión y vuelve a exportar el snapshot."
    )
