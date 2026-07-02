from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FlowRegimeClassification:
    name: str
    source: str
    status: str
    transition_criteria: str
    confidence: str


EXPERIMENTAL_REGIME_SOURCE = "experimental_regime_aware heuristic thresholds; no primary source"


def single_liquid_heating_classification() -> FlowRegimeClassification:
    return FlowRegimeClassification(
        name="single_liquid_heating",
        source="solver phase partition",
        status="diagnostic",
        transition_criteria="local cell is upstream of boiling onset",
        confidence="high",
    )


def unknown_or_out_of_range_classification(context: str) -> FlowRegimeClassification:
    return FlowRegimeClassification(
        name="unknown_or_out_of_range",
        source="published regime map not implemented",
        status="not_implemented",
        transition_criteria=context,
        confidence="none",
    )


def classify_horizontal_evaporator_regime_result(
    mass_quality: float,
    gas_volume_fraction: float,
    gas_superficial_velocity_m_s: float,
    liquid_superficial_velocity_m_s: float,
    slip_ratio: float,
) -> FlowRegimeClassification:
    mass_quality = max(0.0, min(1.0, float(mass_quality)))
    gas_volume_fraction = max(0.0, min(1.0, float(gas_volume_fraction)))
    gas_superficial_velocity_m_s = max(0.0, float(gas_superficial_velocity_m_s))
    liquid_superficial_velocity_m_s = max(0.0, float(liquid_superficial_velocity_m_s))
    slip_ratio = max(0.0, float(slip_ratio))

    if mass_quality <= 1e-4 or gas_volume_fraction < 0.01:
        name = "bubble_onset"
        criteria = "x <= 1e-4 or alpha < 0.01"
    elif gas_volume_fraction < 0.12:
        if gas_superficial_velocity_m_s < 0.6:
            name = "bubbly"
            criteria = "alpha < 0.12 and j_g < 0.6 m/s"
        else:
            name = "plug"
            criteria = "alpha < 0.12 and j_g >= 0.6 m/s"
    elif gas_volume_fraction < 0.35:
        if gas_superficial_velocity_m_s < 1.0 and liquid_superficial_velocity_m_s > 0.10:
            name = "stratified_wavy"
            criteria = "0.12 <= alpha < 0.35, j_g < 1.0 m/s, j_l > 0.10 m/s"
        else:
            name = "plug"
            criteria = "0.12 <= alpha < 0.35 outside stratified-wavy heuristic"
    elif gas_volume_fraction < 0.75:
        if gas_superficial_velocity_m_s < 2.5 and liquid_superficial_velocity_m_s > 0.05:
            name = "intermittent"
            criteria = "0.35 <= alpha < 0.75, j_g < 2.5 m/s, j_l > 0.05 m/s"
        else:
            name = "annular_transition"
            criteria = "0.35 <= alpha < 0.75 outside intermittent heuristic"
    elif gas_volume_fraction < 0.93:
        if slip_ratio < 12.0:
            name = "annular"
            criteria = "0.75 <= alpha < 0.93 and S < 12"
        else:
            name = "annular_transition"
            criteria = "0.75 <= alpha < 0.93 and S >= 12"
    else:
        name = "annular_mist"
        criteria = "alpha >= 0.93"

    return FlowRegimeClassification(
        name=name,
        source=EXPERIMENTAL_REGIME_SOURCE,
        status="experimental",
        transition_criteria=criteria,
        confidence="heuristic",
    )


def classify_horizontal_evaporator_regime(
    mass_quality: float,
    gas_volume_fraction: float,
    gas_superficial_velocity_m_s: float,
    liquid_superficial_velocity_m_s: float,
    slip_ratio: float,
) -> str:
    return classify_horizontal_evaporator_regime_result(
        mass_quality=mass_quality,
        gas_volume_fraction=gas_volume_fraction,
        gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
        liquid_superficial_velocity_m_s=liquid_superficial_velocity_m_s,
        slip_ratio=slip_ratio,
    ).name


def classify_vertical_riser_regime_result(
    gas_volume_fraction: float,
    gas_superficial_velocity_m_s: float,
) -> FlowRegimeClassification:
    gas_volume_fraction = max(0.0, min(1.0, float(gas_volume_fraction)))
    gas_superficial_velocity_m_s = max(0.0, float(gas_superficial_velocity_m_s))

    if gas_volume_fraction < 0.15:
        name = "bubbly"
        criteria = "alpha < 0.15"
    elif gas_volume_fraction < 0.45:
        name = "slug"
        criteria = "0.15 <= alpha < 0.45"
    elif gas_volume_fraction < 0.80:
        name = "churn"
        criteria = "0.45 <= alpha < 0.80"
    elif gas_volume_fraction < 0.95 and gas_superficial_velocity_m_s < 8.0:
        name = "annular"
        criteria = "0.80 <= alpha < 0.95 and j_g < 8.0 m/s"
    else:
        name = "annular_mist"
        criteria = "alpha >= 0.95 or j_g >= 8.0 m/s"

    return FlowRegimeClassification(
        name=name,
        source=EXPERIMENTAL_REGIME_SOURCE,
        status="experimental",
        transition_criteria=criteria,
        confidence="heuristic",
    )


def classify_vertical_riser_regime(
    gas_volume_fraction: float,
    gas_superficial_velocity_m_s: float,
) -> str:
    return classify_vertical_riser_regime_result(
        gas_volume_fraction=gas_volume_fraction,
        gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
    ).name
