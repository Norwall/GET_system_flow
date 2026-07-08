from __future__ import annotations

from typing import Any

import numpy as np


class SourceRequiredCorrelationError(NotImplementedError):
    """Raised when a published correlation is cited but not source-audited."""


def muller_steinhagen_heck_1986_pressure_gradient_pa_per_m(*args: Any, **kwargs: Any) -> Any:
    """Guard for the MSH 1986 pressure-drop correlation until source audit is complete."""

    raise SourceRequiredCorrelationError(
        "Muller-Steinhagen-Heck 1986 is not implemented: the current source audit "
        "has not verified the full primary-source formula, total-mass-flux convention, "
        "and Darcy/Fanning friction-factor convention from DOI 10.1016/0255-2701(86)80008-3."
    )


def friedel_1979_pressure_gradient_pa_per_m(*args: Any, **kwargs: Any) -> Any:
    """Guard for the Friedel 1979 pressure-drop correlation until source audit is complete."""

    raise SourceRequiredCorrelationError(
        "Friedel 1979 is not implemented: the full primary-source conference paper and "
        "formula conventions are not available in the current source audit."
    )


def muller_steinhagen_heck_th3337_candidate_pressure_gradient_pa_per_m(
    *,
    mass_quality: float | np.ndarray,
    mass_flux_kg_m2_s: float | np.ndarray,
    hydraulic_diameter_m: float,
    liquid_density_kg_m3: float | np.ndarray,
    vapor_density_kg_m3: float | np.ndarray,
    liquid_friction_factor: float | np.ndarray,
    vapor_friction_factor: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of MSH Eqs. (4.53)-(4.56).

    This helper is dissertation audit guidance only. It intentionally does not
    replace the guarded Muller-Steinhagen-Heck 1986 primary-source function.
    The friction-factor convention must still be resolved before release.
    """

    x = _quality_0_to_1_open_upper(mass_quality)
    mass_flux = _positive_array(mass_flux_kg_m2_s, "mass_flux_kg_m2_s")
    diameter = _positive_scalar(hydraulic_diameter_m, "hydraulic_diameter_m")
    rho_l = _positive_array(liquid_density_kg_m3, "liquid_density_kg_m3")
    rho_g = _positive_array(vapor_density_kg_m3, "vapor_density_kg_m3")
    f_l = _positive_array(liquid_friction_factor, "liquid_friction_factor")
    f_g = _positive_array(vapor_friction_factor, "vapor_friction_factor")

    liquid_only_gradient = f_l * 2.0 * mass_flux**2 / (diameter * rho_l)
    vapor_only_gradient = f_g * 2.0 * mass_flux**2 / (diameter * rho_g)
    interpolation_factor = liquid_only_gradient + 2.0 * (vapor_only_gradient - liquid_only_gradient) * x
    return interpolation_factor * (1.0 - x) ** (1.0 / 3.0) + vapor_only_gradient * x**3


def friedel_th3337_candidate_two_phase_multiplier(
    *,
    mass_quality: float | np.ndarray,
    mass_flux_kg_m2_s: float | np.ndarray,
    hydraulic_diameter_m: float,
    liquid_density_kg_m3: float | np.ndarray,
    vapor_density_kg_m3: float | np.ndarray,
    liquid_viscosity_pa_s: float | np.ndarray,
    vapor_viscosity_pa_s: float | np.ndarray,
    surface_tension_n_m: float | np.ndarray,
    liquid_friction_factor: float | np.ndarray,
    vapor_friction_factor: float | np.ndarray,
    gravity_m_s2: float = 9.80665,
) -> Any:
    """Candidate TH3337 transcription of Friedel Eqs. (4.41)-(4.47)."""

    x = _quality_0_to_1_open_upper(mass_quality)
    mass_flux = _positive_array(mass_flux_kg_m2_s, "mass_flux_kg_m2_s")
    diameter = _positive_scalar(hydraulic_diameter_m, "hydraulic_diameter_m")
    rho_l = _positive_array(liquid_density_kg_m3, "liquid_density_kg_m3")
    rho_g = _positive_array(vapor_density_kg_m3, "vapor_density_kg_m3")
    mu_l = _positive_array(liquid_viscosity_pa_s, "liquid_viscosity_pa_s")
    mu_g = _positive_array(vapor_viscosity_pa_s, "vapor_viscosity_pa_s")
    sigma = _positive_array(surface_tension_n_m, "surface_tension_n_m")
    f_l = _positive_array(liquid_friction_factor, "liquid_friction_factor")
    f_g = _positive_array(vapor_friction_factor, "vapor_friction_factor")
    gravity = _positive_scalar(gravity_m_s2, "gravity_m_s2")
    viscosity_ratio = mu_g / mu_l
    if np.any(viscosity_ratio >= 1.0):
        raise ValueError("vapor_viscosity_pa_s/liquid_viscosity_pa_s must be < 1 for the TH3337 H term.")

    rho_h = 1.0 / (x / rho_g + (1.0 - x) / rho_l)
    froude_h = mass_flux**2 / (gravity * diameter * rho_h**2)
    e_term = (1.0 - x) ** 2 + x**2 * rho_l * f_g / (rho_g * f_l)
    f_term = x**0.78 * (1.0 - x) ** 0.224
    h_term = (rho_l / rho_g) ** 0.91 * viscosity_ratio**0.19 * (1.0 - viscosity_ratio) ** 0.7
    weber_l = mass_flux**2 * diameter / (sigma * rho_h)
    return e_term + 3.24 * f_term * h_term / (froude_h**0.045 * weber_l**0.035)


def friedel_th3337_candidate_pressure_gradient_pa_per_m(
    *,
    liquid_reference_pressure_gradient_pa_per_m: float | np.ndarray,
    mass_quality: float | np.ndarray,
    mass_flux_kg_m2_s: float | np.ndarray,
    hydraulic_diameter_m: float,
    liquid_density_kg_m3: float | np.ndarray,
    vapor_density_kg_m3: float | np.ndarray,
    liquid_viscosity_pa_s: float | np.ndarray,
    vapor_viscosity_pa_s: float | np.ndarray,
    surface_tension_n_m: float | np.ndarray,
    liquid_friction_factor: float | np.ndarray,
    vapor_friction_factor: float | np.ndarray,
    gravity_m_s2: float = 9.80665,
) -> Any:
    """Candidate TH3337 transcription of Friedel Eq. (4.40)."""

    liquid_gradient = _positive_array(
        liquid_reference_pressure_gradient_pa_per_m,
        "liquid_reference_pressure_gradient_pa_per_m",
    )
    multiplier = friedel_th3337_candidate_two_phase_multiplier(
        mass_quality=mass_quality,
        mass_flux_kg_m2_s=mass_flux_kg_m2_s,
        hydraulic_diameter_m=hydraulic_diameter_m,
        liquid_density_kg_m3=liquid_density_kg_m3,
        vapor_density_kg_m3=vapor_density_kg_m3,
        liquid_viscosity_pa_s=liquid_viscosity_pa_s,
        vapor_viscosity_pa_s=vapor_viscosity_pa_s,
        surface_tension_n_m=surface_tension_n_m,
        liquid_friction_factor=liquid_friction_factor,
        vapor_friction_factor=vapor_friction_factor,
        gravity_m_s2=gravity_m_s2,
    )
    return liquid_gradient * multiplier


def moreno_quiben_th3337_candidate_annular_interfacial_friction_factor(
    *,
    film_thickness_m: float | np.ndarray,
    hydraulic_diameter_m: float,
    liquid_density_kg_m3: float | np.ndarray,
    vapor_density_kg_m3: float | np.ndarray,
    liquid_viscosity_pa_s: float | np.ndarray,
    vapor_viscosity_pa_s: float | np.ndarray,
    surface_tension_n_m: float | np.ndarray,
    liquid_weber_number: float | np.ndarray,
    gravity_m_s2: float = 9.80665,
) -> Any:
    """Candidate TH3337 transcription of Moreno Quiben Eq. (7.4).

    This helper covers only the annular branch of the dissertation pressure-drop
    model. It is not a released WUT, Friedel, or MSH runtime implementation.
    """

    delta = _positive_array(film_thickness_m, "film_thickness_m")
    diameter = _positive_scalar(hydraulic_diameter_m, "hydraulic_diameter_m")
    rho_l = _positive_array(liquid_density_kg_m3, "liquid_density_kg_m3")
    rho_g = _positive_array(vapor_density_kg_m3, "vapor_density_kg_m3")
    mu_l = _positive_array(liquid_viscosity_pa_s, "liquid_viscosity_pa_s")
    mu_g = _positive_array(vapor_viscosity_pa_s, "vapor_viscosity_pa_s")
    sigma = _positive_array(surface_tension_n_m, "surface_tension_n_m")
    we_l = _positive_array(liquid_weber_number, "liquid_weber_number")
    gravity = _positive_scalar(gravity_m_s2, "gravity_m_s2")

    if np.any(delta >= diameter / 2.0):
        raise ValueError("film_thickness_m must be smaller than hydraulic_diameter_m/2 for the annular film.")
    density_difference = rho_l - rho_g
    if np.any(density_difference <= 0.0):
        raise ValueError("liquid_density_kg_m3 must exceed vapor_density_kg_m3 for the TH3337 annular branch.")

    wave_group = density_difference * gravity * delta**2 / sigma
    return (
        0.67
        * (delta / diameter) ** 1.2
        * wave_group ** (-0.4)
        * (mu_g / mu_l) ** 0.08
        * we_l ** (-0.034)
    )


def moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m(
    *,
    film_thickness_m: float | np.ndarray,
    hydraulic_diameter_m: float,
    liquid_density_kg_m3: float | np.ndarray,
    vapor_density_kg_m3: float | np.ndarray,
    liquid_viscosity_pa_s: float | np.ndarray,
    vapor_viscosity_pa_s: float | np.ndarray,
    surface_tension_n_m: float | np.ndarray,
    liquid_weber_number: float | np.ndarray,
    vapor_velocity_m_s: float | np.ndarray,
    gravity_m_s2: float = 9.80665,
) -> Any:
    """Candidate TH3337 transcription of Moreno Quiben Eq. (7.5)."""

    diameter = _positive_scalar(hydraulic_diameter_m, "hydraulic_diameter_m")
    rho_g = _positive_array(vapor_density_kg_m3, "vapor_density_kg_m3")
    u_g = _positive_array(vapor_velocity_m_s, "vapor_velocity_m_s")
    interfacial_friction = moreno_quiben_th3337_candidate_annular_interfacial_friction_factor(
        film_thickness_m=film_thickness_m,
        hydraulic_diameter_m=hydraulic_diameter_m,
        liquid_density_kg_m3=liquid_density_kg_m3,
        vapor_density_kg_m3=vapor_density_kg_m3,
        liquid_viscosity_pa_s=liquid_viscosity_pa_s,
        vapor_viscosity_pa_s=vapor_viscosity_pa_s,
        surface_tension_n_m=surface_tension_n_m,
        liquid_weber_number=liquid_weber_number,
        gravity_m_s2=gravity_m_s2,
    )
    return 4.0 * interfacial_friction / diameter * rho_g * u_g**2 / 2.0


def moreno_quiben_th3337_candidate_mist_homogeneous_void_fraction(
    *,
    mass_quality: float | np.ndarray,
    liquid_density_kg_m3: float | np.ndarray,
    vapor_density_kg_m3: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of the homogeneous void fraction in Eq. (7.15)."""

    x = _quality_open_lower_closed_upper(mass_quality)
    rho_l = _positive_array(liquid_density_kg_m3, "liquid_density_kg_m3")
    rho_g = _positive_array(vapor_density_kg_m3, "vapor_density_kg_m3")
    return 1.0 / (1.0 + ((1.0 - x) / x) * (rho_g / rho_l))


def moreno_quiben_th3337_candidate_mist_mixture_density_kg_m3(
    *,
    mass_quality: float | np.ndarray,
    liquid_density_kg_m3: float | np.ndarray,
    vapor_density_kg_m3: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of Eq. (7.14)."""

    alpha_h = moreno_quiben_th3337_candidate_mist_homogeneous_void_fraction(
        mass_quality=mass_quality,
        liquid_density_kg_m3=liquid_density_kg_m3,
        vapor_density_kg_m3=vapor_density_kg_m3,
    )
    rho_l = _positive_array(liquid_density_kg_m3, "liquid_density_kg_m3")
    rho_g = _positive_array(vapor_density_kg_m3, "vapor_density_kg_m3")
    return rho_l * (1.0 - alpha_h) + rho_g * alpha_h


def moreno_quiben_th3337_candidate_mist_mixture_viscosity_pa_s(
    *,
    mass_quality: float | np.ndarray,
    liquid_viscosity_pa_s: float | np.ndarray,
    vapor_viscosity_pa_s: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of the Cicchitti viscosity in Eq. (7.17)."""

    x = _quality_open_lower_closed_upper(mass_quality)
    mu_l = _positive_array(liquid_viscosity_pa_s, "liquid_viscosity_pa_s")
    mu_g = _positive_array(vapor_viscosity_pa_s, "vapor_viscosity_pa_s")
    return x * mu_g + (1.0 - x) * mu_l


def moreno_quiben_th3337_candidate_mist_friction_factor(
    *,
    mass_quality: float | np.ndarray,
    mass_flux_kg_m2_s: float | np.ndarray,
    hydraulic_diameter_m: float,
    liquid_viscosity_pa_s: float | np.ndarray,
    vapor_viscosity_pa_s: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of Eq. (7.16)."""

    mass_flux = _positive_array(mass_flux_kg_m2_s, "mass_flux_kg_m2_s")
    diameter = _positive_scalar(hydraulic_diameter_m, "hydraulic_diameter_m")
    mu_m = moreno_quiben_th3337_candidate_mist_mixture_viscosity_pa_s(
        mass_quality=mass_quality,
        liquid_viscosity_pa_s=liquid_viscosity_pa_s,
        vapor_viscosity_pa_s=vapor_viscosity_pa_s,
    )
    reynolds_m = mass_flux * diameter / mu_m
    return 0.079 / reynolds_m**0.25


def moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m(
    *,
    mass_quality: float | np.ndarray,
    mass_flux_kg_m2_s: float | np.ndarray,
    hydraulic_diameter_m: float,
    liquid_density_kg_m3: float | np.ndarray,
    vapor_density_kg_m3: float | np.ndarray,
    liquid_viscosity_pa_s: float | np.ndarray,
    vapor_viscosity_pa_s: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of Eq. (7.13), per unit length."""

    mass_flux = _positive_array(mass_flux_kg_m2_s, "mass_flux_kg_m2_s")
    diameter = _positive_scalar(hydraulic_diameter_m, "hydraulic_diameter_m")
    rho_m = moreno_quiben_th3337_candidate_mist_mixture_density_kg_m3(
        mass_quality=mass_quality,
        liquid_density_kg_m3=liquid_density_kg_m3,
        vapor_density_kg_m3=vapor_density_kg_m3,
    )
    friction_factor = moreno_quiben_th3337_candidate_mist_friction_factor(
        mass_quality=mass_quality,
        mass_flux_kg_m2_s=mass_flux_kg_m2_s,
        hydraulic_diameter_m=hydraulic_diameter_m,
        liquid_viscosity_pa_s=liquid_viscosity_pa_s,
        vapor_viscosity_pa_s=vapor_viscosity_pa_s,
    )
    return 2.0 * friction_factor * mass_flux**2 / (diameter * rho_m)


def moreno_quiben_th3337_candidate_gas_friction_factor(
    *,
    mass_quality: float | np.ndarray,
    mass_flux_kg_m2_s: float | np.ndarray,
    hydraulic_diameter_m: float,
    vapor_viscosity_pa_s: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of the gas friction factor in Eq. (7.10)."""

    x = _quality_open_lower_closed_upper(mass_quality)
    mass_flux = _positive_array(mass_flux_kg_m2_s, "mass_flux_kg_m2_s")
    diameter = _positive_scalar(hydraulic_diameter_m, "hydraulic_diameter_m")
    mu_g = _positive_array(vapor_viscosity_pa_s, "vapor_viscosity_pa_s")
    reynolds_g = mass_flux * x * diameter / mu_g
    return 0.079 / reynolds_g**0.25


def moreno_quiben_th3337_candidate_stratified_wavy_two_phase_friction_factor(
    *,
    dry_perimeter_fraction: float | np.ndarray,
    gas_friction_factor: float | np.ndarray,
    annular_interfacial_friction_factor: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of Moreno Quiben Eq. (7.9)."""

    epsilon_dry = _fraction_0_to_1_closed(dry_perimeter_fraction, "dry_perimeter_fraction")
    f_g = _positive_array(gas_friction_factor, "gas_friction_factor")
    f_i = _positive_array(annular_interfacial_friction_factor, "annular_interfacial_friction_factor")
    return epsilon_dry * f_g + (1.0 - epsilon_dry) * f_i


def moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m(
    *,
    dry_perimeter_fraction: float | np.ndarray,
    gas_friction_factor: float | np.ndarray,
    annular_interfacial_friction_factor: float | np.ndarray,
    hydraulic_diameter_m: float,
    vapor_density_kg_m3: float | np.ndarray,
    vapor_velocity_m_s: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of Moreno Quiben Eq. (7.11), per unit length."""

    diameter = _positive_scalar(hydraulic_diameter_m, "hydraulic_diameter_m")
    rho_g = _positive_array(vapor_density_kg_m3, "vapor_density_kg_m3")
    u_g = _positive_array(vapor_velocity_m_s, "vapor_velocity_m_s")
    friction_factor = moreno_quiben_th3337_candidate_stratified_wavy_two_phase_friction_factor(
        dry_perimeter_fraction=dry_perimeter_fraction,
        gas_friction_factor=gas_friction_factor,
        annular_interfacial_friction_factor=annular_interfacial_friction_factor,
    )
    return 4.0 * friction_factor / diameter * rho_g * u_g**2 / 2.0


def moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m(
    *,
    mass_quality: float | np.ndarray,
    dryout_inception_quality: float | np.ndarray,
    dryout_completion_quality: float | np.ndarray,
    inception_pressure_gradient_pa_per_m: float | np.ndarray,
    mist_completion_pressure_gradient_pa_per_m: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of Moreno Quiben Eq. (7.18), per unit length.

    This helper covers only the thesis dryout-zone pressure-drop interpolation.
    It does not release a runtime dryout, WUT heat-transfer, MSH or Friedel model.
    """

    x = _quality_0_to_1_closed(mass_quality, "mass_quality")
    xdi = _quality_0_to_1_closed(dryout_inception_quality, "dryout_inception_quality")
    xde = _quality_0_to_1_closed(dryout_completion_quality, "dryout_completion_quality")
    p_tp = _positive_array(inception_pressure_gradient_pa_per_m, "inception_pressure_gradient_pa_per_m")
    p_mist = _positive_array(
        mist_completion_pressure_gradient_pa_per_m,
        "mist_completion_pressure_gradient_pa_per_m",
    )

    if np.any(xdi >= xde):
        raise ValueError("dryout_inception_quality must be < dryout_completion_quality for Eq. (7.18).")
    if np.any((x < xdi) | (x > xde)):
        raise ValueError(
            "mass_quality must stay between dryout_inception_quality and "
            "dryout_completion_quality for Eq. (7.18)."
        )

    return p_tp - (x - xdi) / (xde - xdi) * (p_tp - p_mist)


def moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m(
    *,
    liquid_only_pressure_gradient_pa_per_m: float | np.ndarray,
    limiting_branch_pressure_gradient_pa_per_m: float | np.ndarray,
    intermittent_annular_boundary_void_fraction: float | np.ndarray,
) -> Any:
    """Candidate TH3337 transcription of Moreno Quiben Eqs. (7.6) and (7.12).

    The same interpolation is used for slug+intermittent to annular and
    slug+stratified-wavy to stratified-wavy pressure-drop branches.
    """

    liquid_gradient = _positive_array(
        liquid_only_pressure_gradient_pa_per_m,
        "liquid_only_pressure_gradient_pa_per_m",
    )
    branch_gradient = _positive_array(
        limiting_branch_pressure_gradient_pa_per_m,
        "limiting_branch_pressure_gradient_pa_per_m",
    )
    alpha_ia = _fraction_0_to_1_closed(
        intermittent_annular_boundary_void_fraction,
        "intermittent_annular_boundary_void_fraction",
    )
    return liquid_gradient * (1.0 - alpha_ia) ** 0.25 + branch_gradient * alpha_ia**0.25


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
    martinelli_x = np.maximum(np.asarray(martinelli_x, dtype=float), 1e-12)
    chisholm_c = np.asarray(chisholm_c, dtype=float)
    return 1.0 + chisholm_c / martinelli_x + 1.0 / martinelli_x**2


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


def lockhart_martinelli_chisholm_pressure_gradient_pa_per_m(
    liquid_reference_pressure_gradient_pa_per_m: float | np.ndarray,
    martinelli_x: float | np.ndarray,
    chisholm_c: float | np.ndarray,
) -> Any:
    return np.asarray(liquid_reference_pressure_gradient_pa_per_m, dtype=float) * two_phase_multiplier_liquid_reference(
        martinelli_x=martinelli_x,
        chisholm_c=chisholm_c,
    )


def _positive_array(value: float | np.ndarray, name: str) -> np.ndarray:
    values = np.asarray(value, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values <= 0.0):
        raise ValueError(f"{name} must contain only positive finite values.")
    return values


def _positive_scalar(value: float, name: str) -> float:
    numeric = float(value)
    if not np.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{name} must be a positive finite value.")
    return numeric


def _quality_0_to_1_open_upper(value: float | np.ndarray) -> np.ndarray:
    values = np.asarray(value, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values < 0.0) or np.any(values >= 1.0):
        raise ValueError("mass_quality must satisfy 0 <= x < 1 for the TH3337 candidate formulas.")
    return values


def _quality_open_lower_closed_upper(value: float | np.ndarray) -> np.ndarray:
    values = np.asarray(value, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values <= 0.0) or np.any(values > 1.0):
        raise ValueError("mass_quality must satisfy 0 < x <= 1 for the TH3337 mist candidate formulas.")
    return values


def _quality_0_to_1_closed(value: float | np.ndarray, name: str) -> np.ndarray:
    values = np.asarray(value, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError(f"{name} must satisfy 0 <= x <= 1 for the TH3337 dryout candidate formula.")
    return values


def _fraction_0_to_1_closed(value: float | np.ndarray, name: str) -> np.ndarray:
    values = np.asarray(value, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError(f"{name} must satisfy 0 <= value <= 1.")
    return values


__all__ = [
    "SourceRequiredCorrelationError",
    "chisholm_constant",
    "friedel_th3337_candidate_pressure_gradient_pa_per_m",
    "friedel_th3337_candidate_two_phase_multiplier",
    "friedel_1979_pressure_gradient_pa_per_m",
    "lockhart_martinelli_chisholm_pressure_gradient_pa_per_m",
    "martinelli_parameter",
    "moreno_quiben_th3337_candidate_annular_interfacial_friction_factor",
    "moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m",
    "moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m",
    "moreno_quiben_th3337_candidate_gas_friction_factor",
    "moreno_quiben_th3337_candidate_mist_friction_factor",
    "moreno_quiben_th3337_candidate_mist_homogeneous_void_fraction",
    "moreno_quiben_th3337_candidate_mist_mixture_density_kg_m3",
    "moreno_quiben_th3337_candidate_mist_mixture_viscosity_pa_s",
    "moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m",
    "moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m",
    "moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m",
    "moreno_quiben_th3337_candidate_stratified_wavy_two_phase_friction_factor",
    "muller_steinhagen_heck_th3337_candidate_pressure_gradient_pa_per_m",
    "muller_steinhagen_heck_1986_pressure_gradient_pa_per_m",
    "single_phase_pressure_gradient_pa_per_m",
    "two_phase_multiplier_liquid_reference",
]
