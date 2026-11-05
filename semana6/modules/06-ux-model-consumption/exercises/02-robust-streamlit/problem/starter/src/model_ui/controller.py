"""TODOs del controlador de estados independiente de Streamlit."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from time import perf_counter
from uuid import uuid4

from pydantic import BaseModel

from model_ui.contracts import PredictionPayload, UiState
from model_ui.gateway import InferenceGateway
from model_ui.presentation import build_prediction_view, to_user_facing_error
from model_ui.telemetry import Telemetry

StateEmitter = Callable[[UiState], None]
Clock = Callable[[], float]
RequestIdFactory = Callable[[], str]


class PredictionController:
    """Orquesta loading, gateway, errores y telemetría."""

    def __init__(
        self,
        gateway: InferenceGateway,
        *,
        telemetry: Telemetry | None = None,
        clock: Clock = perf_counter,
        request_id_factory: RequestIdFactory | None = None,
    ) -> None:
        self.gateway = gateway
        self.telemetry = telemetry or Telemetry()
        self._clock = clock
        self._request_id_factory = request_id_factory or (lambda: uuid4().hex[:10])

    def submit(
        self,
        values: Mapping[str, object],
        *,
        emit: StateEmitter | None = None,
    ) -> UiState:
        """Emite loading, mide la latencia, valida la salida y termina en success/error.

        La telemetría solo recibe agregados (latencia, código de error y
        versiones): ``values`` nunca se guarda ni se registra.
        """

        request_id = self._request_id_factory()
        if emit is not None:
            emit(UiState(phase="loading", request_id=request_id))

        started = self._clock()
        try:
            raw = self.gateway.predict(values)
        except Exception as error:  # noqa: BLE001 - se traduce a un error visible
            return self._fail(error, request_id, self._elapsed_ms(started), emit)
        latency_ms = self._elapsed_ms(started)

        try:
            prediction = self._validate_output(raw)
            view = build_prediction_view(prediction, latency_ms)
        except Exception as error:  # noqa: BLE001 - salida inválida del backend
            return self._fail(error, request_id, latency_ms, emit)

        self.telemetry.record_success(
            latency_ms,
            model_version=prediction.model_version,
            preprocessing_version=prediction.preprocessing_version,
        )
        state = UiState(phase="success", request_id=request_id, view=view)
        if emit is not None:
            emit(state)
        return state

    def _elapsed_ms(self, started: float) -> float:
        """Latencia en milisegundos, redondeada como en la telemetría."""

        return round((self._clock() - started) * 1000, 3)

    @staticmethod
    def _validate_output(raw: object) -> PredictionPayload:
        """Revalida la salida del gateway contra el contrato de la UI."""

        data = raw.model_dump() if isinstance(raw, BaseModel) else raw
        return PredictionPayload.model_validate(data)

    def _fail(
        self,
        error: Exception,
        request_id: str,
        latency_ms: float,
        emit: StateEmitter | None,
    ) -> UiState:
        """Traduce la excepción, registra el código y emite el estado de error."""

        user_error = to_user_facing_error(error, request_id)
        self.telemetry.record_error(user_error.code, latency_ms)
        state = UiState(phase="error", request_id=request_id, error=user_error)
        if emit is not None:
            emit(state)
        return state
