from __future__ import annotations

from typing import Any

import numpy as np


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
