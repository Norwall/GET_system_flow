from __future__ import annotations

from collections import defaultdict


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
    mass_quality = max(0.0, min(1.0, float(mass_quality)))
    gas_volume_fraction = max(0.0, min(1.0, float(gas_volume_fraction)))
    gas_superficial_velocity_m_s = max(0.0, float(gas_superficial_velocity_m_s))
    liquid_superficial_velocity_m_s = max(0.0, float(liquid_superficial_velocity_m_s))
    slip_ratio = max(0.0, float(slip_ratio))

    if mass_quality <= 1e-4 or gas_volume_fraction < 0.01:
        return "bubble_onset"
    if gas_volume_fraction < 0.12:
        return "bubbly" if gas_superficial_velocity_m_s < 0.6 else "plug"
    if gas_volume_fraction < 0.35:
        if gas_superficial_velocity_m_s < 1.0 and liquid_superficial_velocity_m_s > 0.10:
            return "stratified_wavy"
        return "plug"
    if gas_volume_fraction < 0.75:
        if gas_superficial_velocity_m_s < 2.5 and liquid_superficial_velocity_m_s > 0.05:
            return "intermittent"
        return "annular_transition"
    if gas_volume_fraction < 0.93:
        return "annular" if slip_ratio < 12.0 else "annular_transition"
    return "annular_mist"


def classify_vertical_riser_regime(
    gas_volume_fraction: float,
    gas_superficial_velocity_m_s: float,
) -> str:
    gas_volume_fraction = max(0.0, min(1.0, float(gas_volume_fraction)))
    gas_superficial_velocity_m_s = max(0.0, float(gas_superficial_velocity_m_s))

    if gas_volume_fraction < 0.15:
        return "bubbly"
    if gas_volume_fraction < 0.45:
        return "slug"
    if gas_volume_fraction < 0.80:
        return "churn"
    if gas_volume_fraction < 0.95 and gas_superficial_velocity_m_s < 8.0:
        return "annular"
    return "annular_mist"


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
