from __future__ import annotations

from collections import defaultdict

from experimental_regimes import (
    FlowRegimeClassification,
    classify_horizontal_evaporator_regime as _classify_horizontal_evaporator_regime,
    classify_horizontal_evaporator_regime_result,
    classify_vertical_riser_regime as _classify_vertical_riser_regime,
    classify_vertical_riser_regime_result,
    single_liquid_heating_classification,
    unknown_or_out_of_range_classification,
)


FLOW_REGIME_COLORS = {
    "single_liquid_heating": "#d7dee7",
    "single_liquid": "#d7dee7",
    "bubble_onset": "#f4d35e",
    "bubbly": "#f6bd60",
    "plug": "#ee964b",
    "stratified_wavy": "#7fb3d5",
    "intermittent": "#84a98c",
    "annular_transition": "#5c946e",
    "annular": "#2a9d8f",
    "annular_mist": "#264653",
    "slug": "#c97c5d",
    "churn": "#6d597a",
    "condensing_two_phase": "#8d99ae",
}


def classify_horizontal_evaporator_regime(
    mass_quality: float,
    gas_volume_fraction: float,
    gas_superficial_velocity_m_s: float,
    liquid_superficial_velocity_m_s: float,
    slip_ratio: float,
) -> str:
    return _classify_horizontal_evaporator_regime(
        mass_quality=mass_quality,
        gas_volume_fraction=gas_volume_fraction,
        gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
        liquid_superficial_velocity_m_s=liquid_superficial_velocity_m_s,
        slip_ratio=slip_ratio,
    )


def classify_vertical_riser_regime(
    gas_volume_fraction: float,
    gas_superficial_velocity_m_s: float,
) -> str:
    return _classify_vertical_riser_regime(
        gas_volume_fraction=gas_volume_fraction,
        gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
    )


def summarize_regime_fractions(
    regimes: list[str] | tuple[str, ...],
    segment_lengths_m: list[float] | tuple[float, ...],
) -> dict[str, float]:
    accumulated_length_m: dict[str, float] = defaultdict(float)
    total_length_m = 0.0
    for regime, length_m in zip(regimes, segment_lengths_m):
        safe_length_m = max(0.0, float(length_m))
        if safe_length_m <= 0.0:
            continue
        accumulated_length_m[str(regime)] += safe_length_m
        total_length_m += safe_length_m

    if total_length_m <= 0.0:
        return {}

    return dict(
        sorted(
            (
                (regime, regime_length_m / total_length_m)
                for regime, regime_length_m in accumulated_length_m.items()
            ),
            key=lambda item: (-item[1], item[0]),
        )
    )


def dominant_regime(regime_fractions: dict[str, float]) -> str:
    return next(iter(regime_fractions), "")


def format_regime_summary(regime_fractions: dict[str, float]) -> str:
    if not regime_fractions:
        return ""
    return "; ".join(f"{regime}:{fraction:.1%}" for regime, fraction in regime_fractions.items())
