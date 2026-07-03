from __future__ import annotations

from experimental_regimes import FlowRegimeClassification


PUBLISHED_REGIME_MAP = "published_regime_map"
EXPERIMENTAL_REGIME_AWARE = "experimental_regime_aware"

_REGIME_MODEL_ALIASES = {
    "published": PUBLISHED_REGIME_MAP,
    "published_regimes": PUBLISHED_REGIME_MAP,
    "source_gated_published": PUBLISHED_REGIME_MAP,
    "source_required_published": PUBLISHED_REGIME_MAP,
    "regime_aware": EXPERIMENTAL_REGIME_AWARE,
}

_PUBLISHED_HORIZONTAL_SOURCE = (
    "Wojtan, Ursenbacher, Thome 2005 horizontal diabatic flow-boiling map; "
    "DOI 10.1016/j.ijheatmasstransfer.2004.12.012; full primary-source "
    "transition equations are not wired."
)
_PUBLISHED_VERTICAL_SOURCE = (
    "Taitel, Barnea, Dukler 1980 vertical upflow map; DOI 10.1002/aic.690260304; "
    "full primary-source transition equations are not wired."
)


def normalize_regime_model(model: str) -> str:
    key = str(model).strip().lower()
    return _REGIME_MODEL_ALIASES.get(key, key)


def regime_model_scientific_status(model: str) -> str:
    normalized_model = normalize_regime_model(model)
    if normalized_model == PUBLISHED_REGIME_MAP:
        return "published"
    if normalized_model == EXPERIMENTAL_REGIME_AWARE:
        return "experimental"
    return "unknown"


def regime_model_source_status(model: str) -> str:
    normalized_model = normalize_regime_model(model)
    if normalized_model == PUBLISHED_REGIME_MAP:
        return "source_required"
    if normalized_model == EXPERIMENTAL_REGIME_AWARE:
        return "experimental_no_primary_source"
    return "unknown"


def _source_required_classification(source: str, context: str) -> FlowRegimeClassification:
    return FlowRegimeClassification(
        name="unknown_or_out_of_range",
        source=source,
        status="source_required",
        transition_criteria=context,
        confidence="not_evaluated",
    )


def classify_horizontal_evaporator_regime_result(*args, **kwargs) -> FlowRegimeClassification:
    return _source_required_classification(
        _PUBLISHED_HORIZONTAL_SOURCE,
        "Wojtan-Ursenbacher-Thome map source gate: full transition criteria, "
        "dimensionless groups, dryout boundaries, and applicability limits must be "
        "verified from the primary article before implementation.",
    )


def classify_vertical_riser_regime_result(*args, **kwargs) -> FlowRegimeClassification:
    return _source_required_classification(
        _PUBLISHED_VERTICAL_SOURCE,
        "Taitel-Barnea-Dukler map source gate: transition equations and all "
        "coefficients must be verified from the primary article before implementation.",
    )


__all__ = [
    "EXPERIMENTAL_REGIME_AWARE",
    "PUBLISHED_REGIME_MAP",
    "classify_horizontal_evaporator_regime_result",
    "classify_vertical_riser_regime_result",
    "normalize_regime_model",
    "regime_model_scientific_status",
    "regime_model_source_status",
]
