"""Políticas explícitas que el alumnado puede reutilizar en la UI."""

from dataclasses import dataclass
from math import isfinite

from model_ui.contracts import ConfidenceLevel, LatencyStatus


@dataclass(frozen=True)
class ConfidencePolicy:
    """Umbrales de comunicación, no de aprobación del modelo."""

    low_below: float = 0.60
    high_from: float = 0.85


@dataclass(frozen=True)
class LatencyPolicy:
    """Objetivo técnico de la demo."""

    target_ms: float = 300.0


DEFAULT_CONFIDENCE_POLICY = ConfidencePolicy()
DEFAULT_LATENCY_POLICY = LatencyPolicy()


def classify_confidence(
    confidence: float, policy: ConfidencePolicy = DEFAULT_CONFIDENCE_POLICY
) -> ConfidenceLevel:
    """Valida [0, 1] y clasifica: low < low_below <= medium < high_from <= high."""

    if not isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("La confianza debe estar entre 0 y 1.")
    if confidence < policy.low_below:
        return "low"
    if confidence < policy.high_from:
        return "medium"
    return "high"


def classify_latency(
    latency_ms: float, policy: LatencyPolicy = DEFAULT_LATENCY_POLICY
) -> LatencyStatus:
    """Dentro del objetivo si latency_ms <= target_ms; la latencia no puede ser < 0."""

    if not isfinite(latency_ms) or latency_ms < 0:
        raise ValueError("La latencia debe ser un número no negativo.")
    return "within_target" if latency_ms <= policy.target_ms else "above_target"
