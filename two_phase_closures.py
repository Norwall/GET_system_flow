from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.special import erf

from two_phase_regimes import classify_horizontal_evaporator_regime, classify_vertical_riser_regime


@dataclass(frozen=True)
class TwoPhaseClosureState:
    liquid_volume_fraction: float
    gas_volume_fraction: float
    mixture_density_kg_m3: float
    gas_velocity_m_s: float
    liquid_velocity_m_s: float
    slip_ratio: float
    diagnostic_regime: str = ""
    friction_pressure_gradient_pa_per_m: float | None = None
    effective_two_phase_multiplier: float | None = None
    base_two_phase_multiplier: float | None = None
    selected_void_fraction_model: str = ""
    selected_friction_model: str = ""


_CLOSURE_MODEL_ALIASES = {
    "regime_aware": "experimental_regime_aware",
}

_PUBLISHED_CLOSURE_MODELS = {
    "homogeneous_equilibrium",
    "zivi",
}

_MATHCAD_COMPATIBLE_CLOSURE_MODELS = {
    "worksheet_compatible",
}

_EXPERIMENTAL_CLOSURE_MODELS = {
    "experimental_regime_aware",
}

_CLOSURE_MODEL_FORMULA_REGISTRY_IDS = {
    "worksheet_compatible": (
        "FRIC-DARCY-MASS-FLUX",
        "FRIC-LEGACY-BLENDED-DARCY",
        "TP-LOCKHART-MARTINELLI",
        "TP-CHISHOLM-CONSTANT",
        "TP-CHISHOLM-MULTIPLIER",
        "VOID-WORKSHEET-PHI2L",
        "FLOW-PHASE-VELOCITIES",
        "FLOW-SLIP-RATIO",
        "FLOW-MIXTURE-DENSITY",
    ),
    "homogeneous_equilibrium": (
        "FRIC-DARCY-MASS-FLUX",
        "FRIC-LEGACY-BLENDED-DARCY",
        "TP-LOCKHART-MARTINELLI",
        "TP-CHISHOLM-CONSTANT",
        "TP-CHISHOLM-MULTIPLIER",
        "VOID-GENERIC-SLIP",
        "VOID-HOMOGENEOUS-EQUILIBRIUM",
        "FLOW-PHASE-VELOCITIES",
        "FLOW-SLIP-RATIO",
        "FLOW-MIXTURE-DENSITY",
    ),
    "zivi": (
        "FRIC-DARCY-MASS-FLUX",
        "FRIC-LEGACY-BLENDED-DARCY",
        "TP-LOCKHART-MARTINELLI",
        "TP-CHISHOLM-CONSTANT",
        "TP-CHISHOLM-MULTIPLIER",
        "VOID-GENERIC-SLIP",
        "VOID-ZIVI-1964",
        "FLOW-PHASE-VELOCITIES",
        "FLOW-SLIP-RATIO",
        "FLOW-MIXTURE-DENSITY",
    ),
    "experimental_regime_aware": (
        "FRIC-DARCY-MASS-FLUX",
        "FRIC-LEGACY-BLENDED-DARCY",
        "TP-LOCKHART-MARTINELLI",
        "TP-CHISHOLM-CONSTANT",
        "TP-CHISHOLM-MULTIPLIER",
        "VOID-GENERIC-SLIP",
        "VOID-ZIVI-1964",
        "EXP-REGIME-AWARE-CLASSIFIERS",
        "EXP-DRIFT-FLUX-LIKE-VOID",
        "EXP-ANNULAR-CORE-VOID",
        "EXP-REGIME-FRICTION-GRADIENTS",
        "FLOW-PHASE-VELOCITIES",
        "FLOW-SLIP-RATIO",
        "FLOW-MIXTURE-DENSITY",
    ),
}


def normalize_closure_model(model: str) -> str:
    """Return the effective closure model name used by the numerical implementation."""
    return _CLOSURE_MODEL_ALIASES.get(model, model)


def closure_model_scientific_status(model: str) -> str:
    """Classify whether a closure is Mathcad-compatible, published, or experimental."""
    normalized_model = normalize_closure_model(model)
    if normalized_model in _MATHCAD_COMPATIBLE_CLOSURE_MODELS:
        return "mathcad_compatible"
    if normalized_model in _PUBLISHED_CLOSURE_MODELS:
        return "published"
    if normalized_model in _EXPERIMENTAL_CLOSURE_MODELS:
        return "experimental"
    return "unknown"


def closure_model_formula_registry_ids(model: str) -> tuple[str, ...]:
    """Return formula-registry IDs required by a closure model."""
    return _CLOSURE_MODEL_FORMULA_REGISTRY_IDS.get(normalize_closure_model(model), ())


def mass_quality_from_mass_flows(
    vapor_mass_flow_kg_s: float | np.ndarray,
    liquid_mass_flow_kg_s: float | np.ndarray,
) -> Any:
    vapor_mass_flow_kg_s = np.asarray(vapor_mass_flow_kg_s, dtype=float)
    liquid_mass_flow_kg_s = np.asarray(liquid_mass_flow_kg_s, dtype=float)
    return vapor_mass_flow_kg_s / np.maximum(vapor_mass_flow_kg_s + liquid_mass_flow_kg_s, 1e-12)


def void_fraction_from_quality(
    mass_quality: float | np.ndarray,
    rho_l_kg_m3: float | np.ndarray,
    rho_g_kg_m3: float | np.ndarray,
    slip_ratio: float | np.ndarray,
) -> tuple[Any, Any]:
    mass_quality = np.clip(np.asarray(mass_quality, dtype=float), 0.0, 1.0)
    rho_l_kg_m3 = np.maximum(np.asarray(rho_l_kg_m3, dtype=float), 1e-12)
    rho_g_kg_m3 = np.maximum(np.asarray(rho_g_kg_m3, dtype=float), 1e-12)
    slip_ratio = np.maximum(np.asarray(slip_ratio, dtype=float), 1e-12)

    gas_volume_fraction = np.zeros_like(mass_quality, dtype=float)
    all_liquid_mask = mass_quality <= 0.0
    all_gas_mask = mass_quality >= 1.0
    mixed_mask = ~(all_liquid_mask | all_gas_mask)

    gas_volume_fraction[all_gas_mask] = 1.0
    gas_volume_fraction[all_liquid_mask] = 0.0
    gas_volume_fraction[mixed_mask] = 1.0 / (
        1.0
        + ((1.0 - mass_quality[mixed_mask]) / mass_quality[mixed_mask])
        * (rho_g_kg_m3[mixed_mask] / rho_l_kg_m3[mixed_mask])
        * slip_ratio[mixed_mask]
    )
    liquid_volume_fraction = 1.0 - gas_volume_fraction
    return liquid_volume_fraction, gas_volume_fraction


def rough_turbulent_friction_factor_ln(relative_roughness: float) -> float:
    """Current Python rough-turbulent term, using the natural logarithm."""
    return float((1.8 * np.log(8.3 / relative_roughness)) ** (-2))


def rough_turbulent_friction_factor_log10(relative_roughness: float) -> float:
    """Mathcad-compatible rough-turbulent term, using the decimal logarithm."""
    return float((1.8 * np.log10(8.3 / relative_roughness)) ** (-2))


def darcy_friction_factor(
    reynolds_number: float | np.ndarray,
    relative_roughness: float,
    rough_log_base: str = "natural",
) -> Any:
    reynolds_number = np.maximum(np.asarray(reynolds_number, dtype=float), 1e-12)
    if rough_log_base not in {"natural", "log10"}:
        raise ValueError(f"Unsupported rough_log_base: {rough_log_base!r}.")
    friction_laminar = 64.0 / reynolds_number
    friction_blasius = 0.3164 / np.power(reynolds_number, 0.25)
    if rough_log_base == "log10":
        friction_rough = rough_turbulent_friction_factor_log10(relative_roughness)
    else:
        friction_rough = rough_turbulent_friction_factor_ln(relative_roughness)
    turbulent_blend = 0.5 + 0.5 * erf((reynolds_number - 2850.0) / (600.0 * np.sqrt(2.0)))
    roughness_blend = erf((reynolds_number * relative_roughness) / (275.0 * np.sqrt(2.0)))
    return (
        friction_laminar * (1.0 - turbulent_blend)
        + friction_blasius * turbulent_blend * (1.0 - roughness_blend)
        + friction_rough * turbulent_blend * roughness_blend
    )


def laminar_darcy_friction_factor(reynolds_number: float | np.ndarray) -> Any:
    reynolds_number = np.maximum(np.asarray(reynolds_number, dtype=float), 1e-12)
    return 64.0 / reynolds_number


def colebrook_white_friction_factor(
    reynolds_number: float | np.ndarray,
    relative_roughness: float,
) -> Any:
    reynolds = np.maximum(np.asarray(reynolds_number, dtype=float), 1e-12)
    relative_roughness = max(float(relative_roughness), 0.0)
    turbulent = np.maximum(reynolds, 2300.0)
    friction = np.full_like(turbulent, 0.02, dtype=float)
    for _ in range(24):
        argument = (relative_roughness / 3.7) + (2.51 / (turbulent * np.sqrt(np.maximum(friction, 1e-12))))
        friction = np.power(-2.0 * np.log10(np.maximum(argument, 1e-30)), -2.0)
    result = np.where(reynolds < 2300.0, laminar_darcy_friction_factor(reynolds), friction)
    return float(result) if np.ndim(result) == 0 else result


def churchill_1977_friction_factor(
    reynolds_number: float | np.ndarray,
    relative_roughness: float,
) -> Any:
    reynolds = np.maximum(np.asarray(reynolds_number, dtype=float), 1e-12)
    relative_roughness = max(float(relative_roughness), 0.0)
    a_term = np.power(
        2.457
        * np.log(
            1.0
            / np.maximum(
                np.power(7.0 / reynolds, 0.9) + (0.27 * relative_roughness),
                1e-30,
            )
        ),
        16.0,
    )
    b_term = np.power(37530.0 / reynolds, 16.0)
    result = 8.0 * np.power(np.power(8.0 / reynolds, 12.0) + np.power(a_term + b_term, -1.5), 1.0 / 12.0)
    return float(result) if np.ndim(result) == 0 else result


def normalize_friction_model(model: str) -> str:
    aliases = {
        "worksheet_compatible": "mathcad_compat",
        "legacy": "mathcad_compat",
        "legacy_blended": "mathcad_compat",
        "colebrook": "colebrook_white",
        "churchill": "churchill_explicit",
    }
    return aliases.get(model, model)


def friction_factor_from_model(
    reynolds_number: float | np.ndarray,
    relative_roughness: float,
    model: str = "mathcad_compat",
) -> Any:
    normalized_model = normalize_friction_model(model)
    if normalized_model == "mathcad_compat":
        return darcy_friction_factor(reynolds_number, relative_roughness, rough_log_base="natural")
    if normalized_model == "colebrook_white":
        return colebrook_white_friction_factor(reynolds_number, relative_roughness)
    if normalized_model == "churchill_explicit":
        return churchill_1977_friction_factor(reynolds_number, relative_roughness)
    if normalized_model == "laminar_only":
        return laminar_darcy_friction_factor(reynolds_number)
    if normalized_model == "zero_friction":
        reynolds = np.asarray(reynolds_number, dtype=float)
        result = np.zeros_like(reynolds, dtype=float)
        return float(result) if np.ndim(result) == 0 else result
    raise ValueError(f"Unsupported friction_model: {model!r}.")


def martinelli_parameter(
    liquid_mass_flow_kg_s: float | np.ndarray,
    vapor_mass_flow_kg_s: float | np.ndarray,
    liquid_friction_factor: float | np.ndarray,
    gas_friction_factor: float | np.ndarray,
    liquid_specific_volume_m3_per_kg: float | np.ndarray,
    vapor_specific_volume_m3_per_kg: float | np.ndarray,
) -> Any:
    liquid_mass_flow_kg_s = np.asarray(liquid_mass_flow_kg_s, dtype=float)
    vapor_mass_flow_kg_s = np.maximum(np.asarray(vapor_mass_flow_kg_s, dtype=float), 1e-12)
    liquid_friction_factor = np.maximum(np.asarray(liquid_friction_factor, dtype=float), 1e-12)
    gas_friction_factor = np.maximum(np.asarray(gas_friction_factor, dtype=float), 1e-12)
    liquid_specific_volume_m3_per_kg = np.maximum(np.asarray(liquid_specific_volume_m3_per_kg, dtype=float), 1e-12)
    vapor_specific_volume_m3_per_kg = np.maximum(np.asarray(vapor_specific_volume_m3_per_kg, dtype=float), 1e-12)
    martinelli_argument = (liquid_friction_factor * liquid_specific_volume_m3_per_kg) / (
        gas_friction_factor * vapor_specific_volume_m3_per_kg
    )
    return (liquid_mass_flow_kg_s / vapor_mass_flow_kg_s) * np.sqrt(np.maximum(martinelli_argument, 1e-30))


def chisholm_constant(gas_reynolds: float | np.ndarray, liquid_reynolds: float | np.ndarray) -> Any:
    gas_reynolds = np.asarray(gas_reynolds, dtype=float)
    liquid_reynolds = np.asarray(liquid_reynolds, dtype=float)
    return np.where(
        (gas_reynolds > 2320.0) & (liquid_reynolds > 2320.0),
        20.0,
        np.where(
            (gas_reynolds > 2320.0) & (liquid_reynolds <= 2320.0),
            12.0,
            np.where((gas_reynolds <= 2320.0) & (liquid_reynolds > 2320.0), 10.0, 5.0),
        ),
    )


def two_phase_multiplier_liquid_reference(
    martinelli_x: float | np.ndarray,
    chisholm_c: float | np.ndarray,
) -> Any:
    return 1.0 + chisholm_c / martinelli_x + 1.0 / martinelli_x**2


def worksheet_void_fraction_from_phi2l(phi2l: float | np.ndarray) -> tuple[Any, Any]:
    liquid_volume_fraction = 1.0 / np.power(phi2l, 1.0 / 3.0)
    gas_volume_fraction = 1.0 - liquid_volume_fraction
    return liquid_volume_fraction, gas_volume_fraction


def compute_void_fraction(
    phi2l: float | np.ndarray,
    model: str = "worksheet_compatible",
) -> tuple[Any, Any]:
    if model != "worksheet_compatible":
        raise ValueError(f"Unsupported void-fraction model: {model}")
    return worksheet_void_fraction_from_phi2l(phi2l)


def compute_phase_velocities(
    gas_mass_flux_kg_m2_s: float | np.ndarray,
    liquid_mass_flux_kg_m2_s: float | np.ndarray,
    gas_volume_fraction: float | np.ndarray,
    liquid_volume_fraction: float | np.ndarray,
    vapor_specific_volume_m3_per_kg: float | np.ndarray,
    liquid_specific_volume_m3_per_kg: float | np.ndarray,
) -> tuple[Any, Any]:
    gas_volume_fraction = np.maximum(np.asarray(gas_volume_fraction, dtype=float), 1e-12)
    liquid_volume_fraction = np.maximum(np.asarray(liquid_volume_fraction, dtype=float), 1e-12)
    gas_velocity_m_s = (np.asarray(gas_mass_flux_kg_m2_s, dtype=float) / gas_volume_fraction) * np.asarray(
        vapor_specific_volume_m3_per_kg,
        dtype=float,
    )
    liquid_velocity_m_s = (np.asarray(liquid_mass_flux_kg_m2_s, dtype=float) / liquid_volume_fraction) * np.asarray(
        liquid_specific_volume_m3_per_kg,
        dtype=float,
    )
    return gas_velocity_m_s, liquid_velocity_m_s


def compute_slip_ratio(
    gas_velocity_m_s: float | np.ndarray,
    liquid_velocity_m_s: float | np.ndarray,
) -> Any:
    return np.asarray(gas_velocity_m_s, dtype=float) / np.maximum(np.asarray(liquid_velocity_m_s, dtype=float), 1e-12)


def compute_mixture_density(
    gas_volume_fraction: float | np.ndarray,
    liquid_volume_fraction: float | np.ndarray,
    vapor_specific_volume_m3_per_kg: float | np.ndarray,
    liquid_specific_volume_m3_per_kg: float | np.ndarray,
) -> Any:
    return (
        np.asarray(liquid_volume_fraction, dtype=float) / np.asarray(liquid_specific_volume_m3_per_kg, dtype=float)
        + np.asarray(gas_volume_fraction, dtype=float) / np.asarray(vapor_specific_volume_m3_per_kg, dtype=float)
    )


def zivi_slip_ratio(
    rho_l_kg_m3: float | np.ndarray,
    rho_g_kg_m3: float | np.ndarray,
) -> Any:
    rho_l_kg_m3 = np.maximum(np.asarray(rho_l_kg_m3, dtype=float), 1e-12)
    rho_g_kg_m3 = np.maximum(np.asarray(rho_g_kg_m3, dtype=float), 1e-12)
    return np.power(rho_l_kg_m3 / rho_g_kg_m3, 1.0 / 3.0)


def single_phase_pressure_gradient_pa_per_m(
    mass_flux_kg_m2_s: float | np.ndarray,
    specific_volume_m3_per_kg: float | np.ndarray,
    friction_factor: float | np.ndarray,
    hydraulic_diameter_m: float,
) -> Any:
    hydraulic_diameter_m = max(float(hydraulic_diameter_m), 1e-12)
    return (
        np.asarray(friction_factor, dtype=float)
        * np.asarray(specific_volume_m3_per_kg, dtype=float)
        * np.asarray(mass_flux_kg_m2_s, dtype=float) ** 2
    ) / (2.0 * hydraulic_diameter_m)


def homogeneous_mixture_dynamic_viscosity_pa_s(
    mass_quality: float | np.ndarray,
    liquid_dynamic_viscosity_pa_s: float | np.ndarray,
    vapor_dynamic_viscosity_pa_s: float | np.ndarray,
) -> Any:
    mass_quality = np.clip(np.asarray(mass_quality, dtype=float), 0.0, 1.0)
    liquid_dynamic_viscosity_pa_s = np.maximum(np.asarray(liquid_dynamic_viscosity_pa_s, dtype=float), 1e-12)
    vapor_dynamic_viscosity_pa_s = np.maximum(np.asarray(vapor_dynamic_viscosity_pa_s, dtype=float), 1e-12)
    inverse_viscosity = (mass_quality / vapor_dynamic_viscosity_pa_s) + (
        (1.0 - mass_quality) / liquid_dynamic_viscosity_pa_s
    )
    return 1.0 / np.maximum(inverse_viscosity, 1e-12)


def drift_flux_void_fraction(
    gas_superficial_velocity_m_s: float,
    liquid_superficial_velocity_m_s: float,
    rho_l_kg_m3: float,
    rho_g_kg_m3: float,
    hydraulic_diameter_m: float,
    orientation: str,
) -> tuple[float, float]:
    total_superficial_velocity_m_s = max(
        0.0,
        float(gas_superficial_velocity_m_s) + float(liquid_superficial_velocity_m_s),
    )
    gas_superficial_velocity_m_s = max(0.0, float(gas_superficial_velocity_m_s))
    rho_l_kg_m3 = max(float(rho_l_kg_m3), 1e-12)
    rho_g_kg_m3 = max(float(rho_g_kg_m3), 1e-12)
    hydraulic_diameter_m = max(float(hydraulic_diameter_m), 1e-12)
    if total_superficial_velocity_m_s <= 0.0 or gas_superficial_velocity_m_s <= 0.0:
        return 1.0, 0.0

    distribution_parameter = 1.08 if orientation == "horizontal" else 1.18
    drift_prefactor = 0.30 if orientation == "horizontal" else 0.50
    buoyancy_factor = max((rho_l_kg_m3 - rho_g_kg_m3) / rho_l_kg_m3, 0.0)
    drift_velocity_m_s = drift_prefactor * np.sqrt(9.81 * hydraulic_diameter_m * buoyancy_factor)
    gas_volume_fraction = gas_superficial_velocity_m_s / max(
        (distribution_parameter * total_superficial_velocity_m_s) + drift_velocity_m_s,
        1e-12,
    )
    gas_volume_fraction = float(np.clip(gas_volume_fraction, 0.0, 0.995))
    return 1.0 - gas_volume_fraction, gas_volume_fraction


def annular_core_void_fraction(
    mass_quality: float,
    rho_l_kg_m3: float,
    rho_g_kg_m3: float,
    zivi_slip: float,
    orientation: str,
) -> tuple[float, float]:
    annular_slip_ratio = max(
        1.05,
        (0.60 if orientation == "horizontal" else 0.72) * float(zivi_slip),
    )
    liquid_volume_fraction, gas_volume_fraction = void_fraction_from_quality(
        mass_quality=mass_quality,
        rho_l_kg_m3=rho_l_kg_m3,
        rho_g_kg_m3=rho_g_kg_m3,
        slip_ratio=annular_slip_ratio,
    )
    return (
        float(np.asarray(liquid_volume_fraction, dtype=float)),
        float(np.asarray(gas_volume_fraction, dtype=float)),
    )


def homogeneous_mixture_two_phase_multiplier(
    mass_quality: float,
    rho_l_kg_m3: float,
    rho_g_kg_m3: float,
) -> float:
    mass_quality = max(0.0, min(1.0, float(mass_quality)))
    rho_l_kg_m3 = max(float(rho_l_kg_m3), 1e-12)
    rho_g_kg_m3 = max(float(rho_g_kg_m3), 1e-12)
    mixture_density_kg_m3 = 1.0 / max((mass_quality / rho_g_kg_m3) + ((1.0 - mass_quality) / rho_l_kg_m3), 1e-12)
    density_factor = rho_l_kg_m3 / mixture_density_kg_m3
    inertia_factor = 1.0 + 0.25 * mass_quality / max(1.0 - mass_quality, 1e-12)
    return max(density_factor * inertia_factor, 1.0)


def _select_void_fraction_model_for_regime(
    regime: str,
    orientation: str,
) -> str:
    if regime in {"bubble_onset", "bubbly"}:
        return "drift_flux"
    if regime in {"plug", "slug", "intermittent", "churn"}:
        return "zivi"
    if regime == "stratified_wavy":
        return "worksheet_compatible"
    if regime == "annular_transition":
        return "annular_core"
    if regime in {"annular", "annular_mist"}:
        return "annular_core"
    return "zivi"


def _select_friction_model_for_regime(
    regime: str,
    orientation: str,
) -> str:
    if regime in {"bubble_onset", "bubbly"}:
        return "homogeneous_mixture"
    if regime == "stratified_wavy":
        return "stratified_separated"
    if regime in {"plug", "slug", "intermittent", "churn", "annular_transition"}:
        return "separated_shear_vertical" if orientation == "vertical_up" else "separated_shear"
    if regime in {"annular", "annular_mist"}:
        return "annular_film_vertical" if orientation == "vertical_up" else "annular_film"
    return "lockhart_martinelli_chisholm"


def _resolve_void_fraction_from_selected_model(
    selected_void_fraction_model: str,
    mass_quality: float,
    rho_l_kg_m3: float,
    rho_g_kg_m3: float,
    zivi_slip: float,
    phi2l: float,
    gas_superficial_velocity_m_s: float,
    liquid_superficial_velocity_m_s: float,
    hydraulic_diameter_m: float,
    orientation: str,
) -> tuple[float, float]:
    if selected_void_fraction_model == "worksheet_compatible":
        liquid_volume_fraction, gas_volume_fraction = worksheet_void_fraction_from_phi2l(phi2l)
    elif selected_void_fraction_model == "homogeneous_equilibrium":
        liquid_volume_fraction, gas_volume_fraction = void_fraction_from_quality(
            mass_quality=mass_quality,
            rho_l_kg_m3=rho_l_kg_m3,
            rho_g_kg_m3=rho_g_kg_m3,
            slip_ratio=1.0,
        )
    elif selected_void_fraction_model == "zivi":
        liquid_volume_fraction, gas_volume_fraction = void_fraction_from_quality(
            mass_quality=mass_quality,
            rho_l_kg_m3=rho_l_kg_m3,
            rho_g_kg_m3=rho_g_kg_m3,
            slip_ratio=zivi_slip,
        )
    elif selected_void_fraction_model == "drift_flux":
        liquid_volume_fraction, gas_volume_fraction = drift_flux_void_fraction(
            gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
            liquid_superficial_velocity_m_s=liquid_superficial_velocity_m_s,
            rho_l_kg_m3=rho_l_kg_m3,
            rho_g_kg_m3=rho_g_kg_m3,
            hydraulic_diameter_m=hydraulic_diameter_m,
            orientation=orientation,
        )
    elif selected_void_fraction_model == "annular_core":
        liquid_volume_fraction, gas_volume_fraction = annular_core_void_fraction(
            mass_quality=mass_quality,
            rho_l_kg_m3=rho_l_kg_m3,
            rho_g_kg_m3=rho_g_kg_m3,
            zivi_slip=zivi_slip,
            orientation=orientation,
        )
    else:
        raise ValueError(f"Unsupported selected void-fraction model: {selected_void_fraction_model}")
    return (
        float(np.asarray(liquid_volume_fraction, dtype=float)),
        float(np.asarray(gas_volume_fraction, dtype=float)),
    )


def _resolve_two_phase_friction_response(
    selected_friction_model: str,
    base_two_phase_multiplier: float,
    mass_quality: float,
    rho_l_kg_m3: float,
    rho_g_kg_m3: float,
    liquid_volume_fraction: float,
    gas_volume_fraction: float,
    gas_mass_flux_kg_m2_s: float,
    liquid_mass_flux_kg_m2_s: float,
    vapor_specific_volume_m3_per_kg: float,
    liquid_specific_volume_m3_per_kg: float,
    vapor_dynamic_viscosity_pa_s: float | None,
    liquid_dynamic_viscosity_pa_s: float | None,
    hydraulic_diameter_m: float | None,
    relative_roughness: float | None,
    friction_model: str = "mathcad_compat",
) -> tuple[float, float | None]:
    if (
        vapor_dynamic_viscosity_pa_s is None
        or liquid_dynamic_viscosity_pa_s is None
        or hydraulic_diameter_m is None
        or relative_roughness is None
    ):
        if selected_friction_model == "lockhart_martinelli_chisholm":
            return base_two_phase_multiplier, None
        if selected_friction_model == "homogeneous_mixture":
            return homogeneous_mixture_two_phase_multiplier(
                mass_quality=mass_quality,
                rho_l_kg_m3=rho_l_kg_m3,
                rho_g_kg_m3=rho_g_kg_m3,
            ), None
        if selected_friction_model == "stratified_separated":
            return 0.88 * base_two_phase_multiplier, None
        if selected_friction_model == "separated_shear":
            return 0.98 * base_two_phase_multiplier, None
        if selected_friction_model == "separated_shear_vertical":
            return 1.05 * base_two_phase_multiplier, None
        if selected_friction_model == "annular_film":
            return 1.15 * base_two_phase_multiplier, None
        if selected_friction_model == "annular_film_vertical":
            return 1.20 * base_two_phase_multiplier, None
        raise ValueError(f"Unsupported selected friction model: {selected_friction_model}")

    hydraulic_diameter_m = max(float(hydraulic_diameter_m), 1e-12)
    relative_roughness = float(relative_roughness)
    vapor_dynamic_viscosity_pa_s = max(float(vapor_dynamic_viscosity_pa_s), 1e-12)
    liquid_dynamic_viscosity_pa_s = max(float(liquid_dynamic_viscosity_pa_s), 1e-12)
    gas_mass_flux_kg_m2_s = max(float(gas_mass_flux_kg_m2_s), 0.0)
    liquid_mass_flux_kg_m2_s = max(float(liquid_mass_flux_kg_m2_s), 0.0)
    liquid_volume_fraction = max(float(liquid_volume_fraction), 1e-12)
    gas_volume_fraction = max(float(gas_volume_fraction), 1e-12)

    liquid_reynolds = (liquid_mass_flux_kg_m2_s * hydraulic_diameter_m) / liquid_dynamic_viscosity_pa_s
    gas_reynolds = (gas_mass_flux_kg_m2_s * hydraulic_diameter_m) / vapor_dynamic_viscosity_pa_s
    liquid_friction_factor = float(friction_factor_from_model(liquid_reynolds, relative_roughness, friction_model))
    gas_friction_factor = float(friction_factor_from_model(gas_reynolds, relative_roughness, friction_model))
    liquid_only_pressure_gradient_pa_per_m = float(
        single_phase_pressure_gradient_pa_per_m(
            mass_flux_kg_m2_s=liquid_mass_flux_kg_m2_s,
            specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
            friction_factor=liquid_friction_factor,
            hydraulic_diameter_m=hydraulic_diameter_m,
        )
    )
    gas_only_pressure_gradient_pa_per_m = float(
        single_phase_pressure_gradient_pa_per_m(
            mass_flux_kg_m2_s=gas_mass_flux_kg_m2_s,
            specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
            friction_factor=gas_friction_factor,
            hydraulic_diameter_m=hydraulic_diameter_m,
        )
    )

    if selected_friction_model == "lockhart_martinelli_chisholm":
        friction_pressure_gradient_pa_per_m = base_two_phase_multiplier * liquid_only_pressure_gradient_pa_per_m
    elif selected_friction_model == "homogeneous_mixture":
        mixture_density_kg_m3 = 1.0 / max(
            (mass_quality / max(rho_g_kg_m3, 1e-12)) + ((1.0 - mass_quality) / max(rho_l_kg_m3, 1e-12)),
            1e-12,
        )
        mixture_specific_volume_m3_per_kg = 1.0 / max(mixture_density_kg_m3, 1e-12)
        mixture_viscosity_pa_s = float(
            homogeneous_mixture_dynamic_viscosity_pa_s(
                mass_quality=mass_quality,
                liquid_dynamic_viscosity_pa_s=liquid_dynamic_viscosity_pa_s,
                vapor_dynamic_viscosity_pa_s=vapor_dynamic_viscosity_pa_s,
            )
        )
        total_mass_flux_kg_m2_s = gas_mass_flux_kg_m2_s + liquid_mass_flux_kg_m2_s
        mixture_reynolds = (total_mass_flux_kg_m2_s * hydraulic_diameter_m) / max(mixture_viscosity_pa_s, 1e-12)
        mixture_friction_factor = float(friction_factor_from_model(mixture_reynolds, relative_roughness, friction_model))
        friction_pressure_gradient_pa_per_m = float(
            single_phase_pressure_gradient_pa_per_m(
                mass_flux_kg_m2_s=total_mass_flux_kg_m2_s,
                specific_volume_m3_per_kg=mixture_specific_volume_m3_per_kg,
                friction_factor=mixture_friction_factor,
                hydraulic_diameter_m=hydraulic_diameter_m,
            )
        )
    elif selected_friction_model == "stratified_separated":
        liquid_film_gradient_pa_per_m = liquid_only_pressure_gradient_pa_per_m * min(1.0 / liquid_volume_fraction, 3.0)
        gas_core_gradient_pa_per_m = gas_only_pressure_gradient_pa_per_m * min(1.0 / gas_volume_fraction, 2.0)
        friction_pressure_gradient_pa_per_m = max(
            (0.88 * liquid_film_gradient_pa_per_m) + (0.22 * gas_core_gradient_pa_per_m),
            liquid_only_pressure_gradient_pa_per_m,
        )
    elif selected_friction_model == "separated_shear":
        liquid_film_gradient_pa_per_m = liquid_only_pressure_gradient_pa_per_m * min(1.0 / liquid_volume_fraction, 3.5)
        gas_core_gradient_pa_per_m = gas_only_pressure_gradient_pa_per_m * min(1.0 / gas_volume_fraction, 3.0)
        friction_pressure_gradient_pa_per_m = max(
            (0.95 * liquid_film_gradient_pa_per_m) + (0.40 * gas_core_gradient_pa_per_m),
            liquid_only_pressure_gradient_pa_per_m,
            gas_only_pressure_gradient_pa_per_m,
        )
    elif selected_friction_model == "separated_shear_vertical":
        liquid_film_gradient_pa_per_m = liquid_only_pressure_gradient_pa_per_m * min(1.0 / liquid_volume_fraction, 3.5)
        gas_core_gradient_pa_per_m = gas_only_pressure_gradient_pa_per_m * min(1.0 / gas_volume_fraction, 3.2)
        friction_pressure_gradient_pa_per_m = max(
            (1.02 * liquid_film_gradient_pa_per_m) + (0.48 * gas_core_gradient_pa_per_m),
            liquid_only_pressure_gradient_pa_per_m,
            gas_only_pressure_gradient_pa_per_m,
        )
    elif selected_friction_model == "annular_film":
        liquid_film_gradient_pa_per_m = liquid_only_pressure_gradient_pa_per_m * min(1.0 / liquid_volume_fraction, 4.0)
        gas_core_gradient_pa_per_m = gas_only_pressure_gradient_pa_per_m * min(1.0 / gas_volume_fraction, 4.0)
        friction_pressure_gradient_pa_per_m = max(
            (0.28 * liquid_film_gradient_pa_per_m) + (1.05 * gas_core_gradient_pa_per_m),
            gas_only_pressure_gradient_pa_per_m,
        )
    elif selected_friction_model == "annular_film_vertical":
        liquid_film_gradient_pa_per_m = liquid_only_pressure_gradient_pa_per_m * min(1.0 / liquid_volume_fraction, 4.2)
        gas_core_gradient_pa_per_m = gas_only_pressure_gradient_pa_per_m * min(1.0 / gas_volume_fraction, 4.2)
        friction_pressure_gradient_pa_per_m = max(
            (0.32 * liquid_film_gradient_pa_per_m) + (1.12 * gas_core_gradient_pa_per_m),
            gas_only_pressure_gradient_pa_per_m,
        )
    else:
        raise ValueError(f"Unsupported selected friction model: {selected_friction_model}")

    effective_two_phase_multiplier = friction_pressure_gradient_pa_per_m / max(
        liquid_only_pressure_gradient_pa_per_m,
        1e-12,
    )
    return float(effective_two_phase_multiplier), float(friction_pressure_gradient_pa_per_m)


def worksheet_closure_state(
    phi2l: float | np.ndarray,
    gas_mass_flux_kg_m2_s: float | np.ndarray,
    liquid_mass_flux_kg_m2_s: float | np.ndarray,
    vapor_specific_volume_m3_per_kg: float | np.ndarray,
    liquid_specific_volume_m3_per_kg: float | np.ndarray,
) -> TwoPhaseClosureState:
    liquid_volume_fraction, gas_volume_fraction = compute_void_fraction(phi2l, model="worksheet_compatible")
    gas_velocity_m_s, liquid_velocity_m_s = compute_phase_velocities(
        gas_mass_flux_kg_m2_s=gas_mass_flux_kg_m2_s,
        liquid_mass_flux_kg_m2_s=liquid_mass_flux_kg_m2_s,
        gas_volume_fraction=gas_volume_fraction,
        liquid_volume_fraction=liquid_volume_fraction,
        vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
        liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
    )
    mixture_density_kg_m3 = compute_mixture_density(
        gas_volume_fraction=gas_volume_fraction,
        liquid_volume_fraction=liquid_volume_fraction,
        vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
        liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
    )
    slip_ratio = compute_slip_ratio(
        gas_velocity_m_s=gas_velocity_m_s,
        liquid_velocity_m_s=liquid_velocity_m_s,
    )
    return TwoPhaseClosureState(
        liquid_volume_fraction=float(np.asarray(liquid_volume_fraction, dtype=float)),
        gas_volume_fraction=float(np.asarray(gas_volume_fraction, dtype=float)),
        mixture_density_kg_m3=float(np.asarray(mixture_density_kg_m3, dtype=float)),
        gas_velocity_m_s=float(np.asarray(gas_velocity_m_s, dtype=float)),
        liquid_velocity_m_s=float(np.asarray(liquid_velocity_m_s, dtype=float)),
        slip_ratio=float(np.asarray(slip_ratio, dtype=float)),
        effective_two_phase_multiplier=float(np.asarray(phi2l, dtype=float)),
        base_two_phase_multiplier=float(np.asarray(phi2l, dtype=float)),
        selected_void_fraction_model="worksheet_compatible",
        selected_friction_model="lockhart_martinelli_chisholm",
    )


def closure_state_from_model(
    model: str,
    vapor_mass_flow_kg_s: float,
    liquid_mass_flow_kg_s: float,
    gas_mass_flux_kg_m2_s: float,
    liquid_mass_flux_kg_m2_s: float,
    vapor_specific_volume_m3_per_kg: float,
    liquid_specific_volume_m3_per_kg: float,
    phi2l: float | None = None,
    orientation: str = "horizontal",
    hydraulic_diameter_m: float | None = None,
    relative_roughness: float | None = None,
    vapor_dynamic_viscosity_pa_s: float | None = None,
    liquid_dynamic_viscosity_pa_s: float | None = None,
    friction_model: str = "mathcad_compat",
) -> TwoPhaseClosureState:
    model = normalize_closure_model(model)
    rho_l_kg_m3 = 1.0 / max(liquid_specific_volume_m3_per_kg, 1e-12)
    rho_g_kg_m3 = 1.0 / max(vapor_specific_volume_m3_per_kg, 1e-12)
    mass_quality = float(
        np.asarray(
            mass_quality_from_mass_flows(
                vapor_mass_flow_kg_s=vapor_mass_flow_kg_s,
                liquid_mass_flow_kg_s=liquid_mass_flow_kg_s,
            ),
            dtype=float,
        )
    )

    if model == "worksheet_compatible":
        if phi2l is None:
            raise ValueError("worksheet_compatible closure requires phi2l.")
        return worksheet_closure_state(
            phi2l=phi2l,
            gas_mass_flux_kg_m2_s=gas_mass_flux_kg_m2_s,
            liquid_mass_flux_kg_m2_s=liquid_mass_flux_kg_m2_s,
            vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
            liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
        )

    if model == "homogeneous_equilibrium":
        slip_ratio = 1.0
    elif model == "zivi":
        slip_ratio = float(np.asarray(zivi_slip_ratio(rho_l_kg_m3=rho_l_kg_m3, rho_g_kg_m3=rho_g_kg_m3), dtype=float))
    elif model == "experimental_regime_aware":
        base_two_phase_multiplier = float(phi2l) if phi2l is not None else 1.0
        zivi_slip = float(np.asarray(zivi_slip_ratio(rho_l_kg_m3=rho_l_kg_m3, rho_g_kg_m3=rho_g_kg_m3), dtype=float))
        gas_superficial_velocity_m_s = float(np.asarray(gas_mass_flux_kg_m2_s, dtype=float)) * vapor_specific_volume_m3_per_kg
        liquid_superficial_velocity_m_s = float(np.asarray(liquid_mass_flux_kg_m2_s, dtype=float)) * liquid_specific_volume_m3_per_kg
        diagnostic_regime = ""
        selected_void_fraction_model = "zivi"
        selected_friction_model = "lockhart_martinelli_chisholm"
        for _ in range(2):
            liquid_volume_fraction, gas_volume_fraction = _resolve_void_fraction_from_selected_model(
                selected_void_fraction_model=selected_void_fraction_model,
                mass_quality=mass_quality,
                rho_l_kg_m3=rho_l_kg_m3,
                rho_g_kg_m3=rho_g_kg_m3,
                zivi_slip=zivi_slip,
                phi2l=base_two_phase_multiplier,
                gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
                liquid_superficial_velocity_m_s=liquid_superficial_velocity_m_s,
                hydraulic_diameter_m=hydraulic_diameter_m if hydraulic_diameter_m is not None else 1.0,
                orientation=orientation,
            )
            loop_gas_velocity_m_s, loop_liquid_velocity_m_s = compute_phase_velocities(
                gas_mass_flux_kg_m2_s=gas_mass_flux_kg_m2_s,
                liquid_mass_flux_kg_m2_s=liquid_mass_flux_kg_m2_s,
                gas_volume_fraction=gas_volume_fraction,
                liquid_volume_fraction=liquid_volume_fraction,
                vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
                liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
            )
            loop_slip_ratio = float(
                np.asarray(
                    compute_slip_ratio(
                        gas_velocity_m_s=loop_gas_velocity_m_s,
                        liquid_velocity_m_s=loop_liquid_velocity_m_s,
                    ),
                    dtype=float,
                )
            )
            if orientation == "vertical_up":
                diagnostic_regime = classify_vertical_riser_regime(
                    gas_volume_fraction=gas_volume_fraction,
                    gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
                )
            else:
                diagnostic_regime = classify_horizontal_evaporator_regime(
                    mass_quality=mass_quality,
                    gas_volume_fraction=gas_volume_fraction,
                    gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
                    liquid_superficial_velocity_m_s=liquid_superficial_velocity_m_s,
                    slip_ratio=loop_slip_ratio,
                )
            selected_void_fraction_model = _select_void_fraction_model_for_regime(
                regime=diagnostic_regime,
                orientation=orientation,
            )
            selected_friction_model = _select_friction_model_for_regime(
                regime=diagnostic_regime,
                orientation=orientation,
            )

        liquid_volume_fraction, gas_volume_fraction = _resolve_void_fraction_from_selected_model(
            selected_void_fraction_model=selected_void_fraction_model,
            mass_quality=mass_quality,
            rho_l_kg_m3=rho_l_kg_m3,
            rho_g_kg_m3=rho_g_kg_m3,
            zivi_slip=zivi_slip,
            phi2l=base_two_phase_multiplier,
            gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
            liquid_superficial_velocity_m_s=liquid_superficial_velocity_m_s,
            hydraulic_diameter_m=hydraulic_diameter_m if hydraulic_diameter_m is not None else 1.0,
            orientation=orientation,
        )
        gas_velocity_m_s, liquid_velocity_m_s = compute_phase_velocities(
            gas_mass_flux_kg_m2_s=gas_mass_flux_kg_m2_s,
            liquid_mass_flux_kg_m2_s=liquid_mass_flux_kg_m2_s,
            gas_volume_fraction=gas_volume_fraction,
            liquid_volume_fraction=liquid_volume_fraction,
            vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
            liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
        )
        slip_ratio = float(np.asarray(compute_slip_ratio(gas_velocity_m_s=gas_velocity_m_s, liquid_velocity_m_s=liquid_velocity_m_s), dtype=float))
        mixture_density_kg_m3 = compute_mixture_density(
            gas_volume_fraction=gas_volume_fraction,
            liquid_volume_fraction=liquid_volume_fraction,
            vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
            liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
        )
        if orientation == "vertical_up":
            diagnostic_regime = classify_vertical_riser_regime(
                gas_volume_fraction=gas_volume_fraction,
                gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
            )
        else:
            diagnostic_regime = classify_horizontal_evaporator_regime(
                mass_quality=mass_quality,
                gas_volume_fraction=gas_volume_fraction,
                gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
                liquid_superficial_velocity_m_s=liquid_superficial_velocity_m_s,
                slip_ratio=slip_ratio,
            )
        final_selected_void_fraction_model = _select_void_fraction_model_for_regime(
            regime=diagnostic_regime,
            orientation=orientation,
        )
        final_selected_friction_model = _select_friction_model_for_regime(
            regime=diagnostic_regime,
            orientation=orientation,
        )
        if final_selected_void_fraction_model != selected_void_fraction_model:
            liquid_volume_fraction, gas_volume_fraction = _resolve_void_fraction_from_selected_model(
                selected_void_fraction_model=final_selected_void_fraction_model,
                mass_quality=mass_quality,
                rho_l_kg_m3=rho_l_kg_m3,
                rho_g_kg_m3=rho_g_kg_m3,
                zivi_slip=zivi_slip,
                phi2l=base_two_phase_multiplier,
                gas_superficial_velocity_m_s=gas_superficial_velocity_m_s,
                liquid_superficial_velocity_m_s=liquid_superficial_velocity_m_s,
                hydraulic_diameter_m=hydraulic_diameter_m if hydraulic_diameter_m is not None else 1.0,
                orientation=orientation,
            )
            gas_velocity_m_s, liquid_velocity_m_s = compute_phase_velocities(
                gas_mass_flux_kg_m2_s=gas_mass_flux_kg_m2_s,
                liquid_mass_flux_kg_m2_s=liquid_mass_flux_kg_m2_s,
                gas_volume_fraction=gas_volume_fraction,
                liquid_volume_fraction=liquid_volume_fraction,
                vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
                liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
            )
            slip_ratio = float(np.asarray(compute_slip_ratio(gas_velocity_m_s=gas_velocity_m_s, liquid_velocity_m_s=liquid_velocity_m_s), dtype=float))
            mixture_density_kg_m3 = compute_mixture_density(
                gas_volume_fraction=gas_volume_fraction,
                liquid_volume_fraction=liquid_volume_fraction,
                vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
                liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
            )
        selected_void_fraction_model = final_selected_void_fraction_model
        selected_friction_model = final_selected_friction_model
        effective_two_phase_multiplier, friction_pressure_gradient_pa_per_m = _resolve_two_phase_friction_response(
            selected_friction_model=selected_friction_model,
            base_two_phase_multiplier=base_two_phase_multiplier,
            mass_quality=mass_quality,
            rho_l_kg_m3=rho_l_kg_m3,
            rho_g_kg_m3=rho_g_kg_m3,
            liquid_volume_fraction=liquid_volume_fraction,
            gas_volume_fraction=gas_volume_fraction,
            gas_mass_flux_kg_m2_s=gas_mass_flux_kg_m2_s,
            liquid_mass_flux_kg_m2_s=liquid_mass_flux_kg_m2_s,
            vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
            liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
            vapor_dynamic_viscosity_pa_s=vapor_dynamic_viscosity_pa_s,
            liquid_dynamic_viscosity_pa_s=liquid_dynamic_viscosity_pa_s,
            hydraulic_diameter_m=hydraulic_diameter_m,
            relative_roughness=relative_roughness,
            friction_model=friction_model,
        )
        return TwoPhaseClosureState(
            liquid_volume_fraction=float(np.asarray(liquid_volume_fraction, dtype=float)),
            gas_volume_fraction=float(np.asarray(gas_volume_fraction, dtype=float)),
            mixture_density_kg_m3=float(np.asarray(mixture_density_kg_m3, dtype=float)),
            gas_velocity_m_s=float(np.asarray(gas_velocity_m_s, dtype=float)),
            liquid_velocity_m_s=float(np.asarray(liquid_velocity_m_s, dtype=float)),
            slip_ratio=float(np.asarray(slip_ratio, dtype=float)),
            diagnostic_regime=diagnostic_regime,
            friction_pressure_gradient_pa_per_m=friction_pressure_gradient_pa_per_m,
            effective_two_phase_multiplier=float(effective_two_phase_multiplier),
            base_two_phase_multiplier=float(base_two_phase_multiplier),
            selected_void_fraction_model=selected_void_fraction_model,
            selected_friction_model=selected_friction_model,
        )
    else:
        raise ValueError(f"Unsupported closure model: {model}")

    liquid_volume_fraction, gas_volume_fraction = void_fraction_from_quality(
        mass_quality=mass_quality,
        rho_l_kg_m3=rho_l_kg_m3,
        rho_g_kg_m3=rho_g_kg_m3,
        slip_ratio=slip_ratio,
    )
    gas_velocity_m_s, liquid_velocity_m_s = compute_phase_velocities(
        gas_mass_flux_kg_m2_s=gas_mass_flux_kg_m2_s,
        liquid_mass_flux_kg_m2_s=liquid_mass_flux_kg_m2_s,
        gas_volume_fraction=gas_volume_fraction,
        liquid_volume_fraction=liquid_volume_fraction,
        vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
        liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
    )
    mixture_density_kg_m3 = compute_mixture_density(
        gas_volume_fraction=gas_volume_fraction,
        liquid_volume_fraction=liquid_volume_fraction,
        vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
        liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
    )
    effective_two_phase_multiplier = float(phi2l) if phi2l is not None else None
    friction_pressure_gradient_pa_per_m = None
    if phi2l is not None:
        effective_two_phase_multiplier, friction_pressure_gradient_pa_per_m = _resolve_two_phase_friction_response(
            selected_friction_model="lockhart_martinelli_chisholm",
            base_two_phase_multiplier=float(phi2l),
            mass_quality=mass_quality,
            rho_l_kg_m3=rho_l_kg_m3,
            rho_g_kg_m3=rho_g_kg_m3,
            liquid_volume_fraction=float(np.asarray(liquid_volume_fraction, dtype=float)),
            gas_volume_fraction=float(np.asarray(gas_volume_fraction, dtype=float)),
            gas_mass_flux_kg_m2_s=gas_mass_flux_kg_m2_s,
            liquid_mass_flux_kg_m2_s=liquid_mass_flux_kg_m2_s,
            vapor_specific_volume_m3_per_kg=vapor_specific_volume_m3_per_kg,
            liquid_specific_volume_m3_per_kg=liquid_specific_volume_m3_per_kg,
            vapor_dynamic_viscosity_pa_s=vapor_dynamic_viscosity_pa_s,
            liquid_dynamic_viscosity_pa_s=liquid_dynamic_viscosity_pa_s,
            hydraulic_diameter_m=hydraulic_diameter_m,
            relative_roughness=relative_roughness,
            friction_model=friction_model,
        )
    return TwoPhaseClosureState(
        liquid_volume_fraction=float(np.asarray(liquid_volume_fraction, dtype=float)),
        gas_volume_fraction=float(np.asarray(gas_volume_fraction, dtype=float)),
        mixture_density_kg_m3=float(np.asarray(mixture_density_kg_m3, dtype=float)),
        gas_velocity_m_s=float(np.asarray(gas_velocity_m_s, dtype=float)),
        liquid_velocity_m_s=float(np.asarray(liquid_velocity_m_s, dtype=float)),
        slip_ratio=float(np.asarray(slip_ratio, dtype=float)),
        friction_pressure_gradient_pa_per_m=friction_pressure_gradient_pa_per_m,
        effective_two_phase_multiplier=effective_two_phase_multiplier,
        base_two_phase_multiplier=float(phi2l) if phi2l is not None else None,
        selected_void_fraction_model=model,
        selected_friction_model="lockhart_martinelli_chisholm",
    )
