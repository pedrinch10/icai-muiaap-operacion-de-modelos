"""Starter S6: snapshot de la app de S5 con cableado avanzado pendiente."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from model_ui.contracts import UiState
from model_ui.controller import PredictionController
from model_ui.gateway import (
    FEATURE_NAMES,
    DemoGateway,
    InferenceGateway,
    PackagedBundleGateway,
    UnavailableGateway,
)
from model_ui.session import (
    LAST_STATE_KEY,
    LAST_VALUES_KEY,
    TELEMETRY_KEY,
    clear_last_state,
    initialize_session_state,
)

FEATURE_FIELDS = (
    ("fixed_acidity", "Fixed acidity", 0.0, 20.0, 7.4),
    ("volatile_acidity", "Volatile acidity", 0.0, 2.0, 0.7),
    ("citric_acid", "Citric acid", 0.0, 2.0, 0.0),
    ("residual_sugar", "Residual sugar", 0.0, 20.0, 1.9),
    ("chlorides", "Chlorides", 0.0, 1.0, 0.076),
    ("free_sulfur_dioxide", "Free sulfur dioxide", 0.0, 100.0, 11.0),
    ("total_sulfur_dioxide", "Total sulfur dioxide", 0.0, 300.0, 34.0),
    ("density", "Density", 0.98, 1.01, 0.9978),
    ("ph", "pH", 2.5, 4.5, 3.51),
    ("sulphates", "Sulphates", 0.0, 3.0, 0.56),
    ("alcohol", "Alcohol", 5.0, 20.0, 9.4),
)

assert tuple(field[0] for field in FEATURE_FIELDS) == FEATURE_NAMES


def build_gateway(bundle_value: str | None) -> InferenceGateway:
    """Selecciona el bundle configurado o conserva el gateway demo de S5."""

    if not bundle_value:
        return DemoGateway()
    try:
        return PackagedBundleGateway.from_bundle_path(Path(bundle_value))
    except Exception as error:  # noqa: BLE001 - se convierte en estado visible
        return UnavailableGateway(str(error))


def collect_values(st: Any) -> tuple[bool, dict[str, float]]:
    """Formulario heredado de S5; no es un TODO de esta semana."""

    values: dict[str, float] = {}
    with st.form("wine_quality_form"):
        st.caption("Formulario de S5: la inferencia se envía al pulsar el botón.")
        columns = st.columns(2)
        for index, (name, label, minimum, maximum, default) in enumerate(
            FEATURE_FIELDS
        ):
            with columns[index % 2]:
                values[name] = st.number_input(
                    label,
                    min_value=minimum,
                    max_value=maximum,
                    value=default,
                    key=f"input_{name}",
                )
        submitted = st.form_submit_button("Ejecutar inferencia")
    return submitted, values


def get_cached_gateway(st: Any, bundle_value: str | None) -> InferenceGateway:
    """Devuelve el gateway como recurso de Streamlit, no una respuesta.

    ``st.cache_resource`` conserva un único gateway (el bundle ya cargado) entre
    reruns y sesiones. Es seguro compartirlo porque solo se lee. El argumento de
    la caché es la ruta configurada; los valores del formulario y las
    predicciones de una persona nunca entran en la caché.
    """

    cached_builder = st.cache_resource(show_spinner=False)(build_gateway)
    return cached_builder(bundle_value)


def render_state(st: Any, state: UiState, target: Any | None = None) -> None:
    """Presenta idle/loading/success/error en un target de Streamlit.

    Con ``target`` (por ejemplo un ``st.empty()``) sustituye el contenido de ese
    hueco; sin él, dibuja en la página. Nunca muestra excepciones: solo el copy
    ya traducido por ``presentation.py``.
    """

    destination = target if target is not None else st
    with destination.container():
        if state.phase == "idle":
            st.info("Completa el formulario y pulsa «Ejecutar inferencia».")
        elif state.phase == "loading":
            with st.status(
                "Validando la muestra y ejecutando el modelo…",
                state="running",
                expanded=False,
            ):
                st.write("El formulario se mantiene; el resultado aparecerá aquí.")
        elif state.phase == "success" and state.view is not None:
            _render_success(st, state)
        elif state.phase == "error" and state.error is not None:
            error = state.error
            st.error(error.title)
            st.write(error.message)
            st.info(error.recovery)
            st.caption(f"Request ID: {error.request_id}")
        else:
            st.info("Completa el formulario y pulsa «Ejecutar inferencia».")


def _render_success(st: Any, state: UiState) -> None:
    """Resultado: categoría, confianza y latencia; trazabilidad aplazada."""

    view = state.view
    assert view is not None
    category, confidence, latency = st.columns(3)
    category.metric("Resultado", view.quality_label)
    confidence.metric("Confianza", f"{view.confidence:.0%}")
    latency.metric("Latencia", f"{view.latency_ms:.0f} ms")

    confidence_text = f"{view.confidence_label}: {view.confidence_message}"
    if view.confidence_level == "low":
        st.warning(confidence_text)
    else:
        st.info(confidence_text)

    if view.latency_status == "above_target":
        st.warning(f"{view.latency_label}: {view.latency_message}")
    else:
        st.caption(f"{view.latency_label}: {view.latency_message}")

    with st.expander("Trazabilidad"):
        st.json(
            {
                "model_version": view.model_version,
                "preprocessing_version": view.preprocessing_version,
                "request_id": state.request_id,
            }
        )


def main() -> None:
    """Ejecuta la app de S5 con estado avanzado de S6."""

    try:
        import streamlit as st
    except ModuleNotFoundError as error:
        raise SystemExit(
            "Instala Streamlit con `uv run --with streamlit streamlit run app.py`."
        ) from error

    st.set_page_config(page_title="Wine Quality · S6", page_icon="🍷")
    st.title("Inferencia de calidad de vino")
    st.caption("S6: la app de S5 ahora conserva estado y comunica la operación.")

    initialize_session_state(st.session_state)
    bundle_value = os.getenv("MODEL_UI_BUNDLE")
    gateway = get_cached_gateway(st, bundle_value)
    telemetry = st.session_state[TELEMETRY_KEY]
    controller = PredictionController(gateway, telemetry=telemetry)

    submitted, values = collect_values(st)
    state_slot = st.empty()

    def show(event: UiState) -> None:
        render_state(st, event, state_slot)

    # Los botones se leen antes de dibujar el resultado para que su efecto se
    # vea en esta misma ejecución. «Reintentar» vive en un hueco propio: se
    # muestra si el estado final es un error y se retira si deja de serlo.
    previous = st.session_state[LAST_STATE_KEY]
    last_values = st.session_state[LAST_VALUES_KEY]
    clear_column, retry_column = st.columns(2)
    retry_slot = retry_column.empty()
    clear_clicked = clear_column.button("Limpiar último resultado")
    retry_clicked = False
    retry_shown = False
    if previous.phase == "error" and last_values:
        retry_clicked = retry_slot.button("Reintentar", key="retry")
        retry_shown = True

    if submitted:
        st.session_state[LAST_VALUES_KEY] = values
        st.session_state[LAST_STATE_KEY] = controller.submit(values, emit=show)
    elif retry_clicked:
        st.session_state[LAST_STATE_KEY] = controller.submit(last_values, emit=show)
    elif clear_clicked:
        clear_last_state(st.session_state)

    state = st.session_state[LAST_STATE_KEY]
    render_state(st, state, state_slot)

    can_retry = state.phase == "error" and bool(st.session_state[LAST_VALUES_KEY])
    if can_retry and not retry_shown:
        retry_slot.button("Reintentar", key="retry")
    elif not can_retry and retry_shown:
        retry_slot.empty()

    st.divider()
    st.subheader("Telemetría de la sesión")
    st.json(telemetry.snapshot().__dict__)
    st.caption("Solo se muestran agregados; no se guardan las features en Telemetry.")


if __name__ == "__main__":
    main()
