from __future__ import annotations

from typing import Any

import numpy as np


def mass_quality_from_mass_flows(
    vapor_mass_flow_kg_s: float | np.ndarray,
    liquid_mass_flow_kg_s: float | np.ndarray,
) -> Any:
    vapor_mass_flow_kg_s = np.asarray(vapor_mass_flow_kg_s, dtype=float)
    liquid_mass_flow_kg_s = np.asarray(liquid_mass_flow_kg_s, dtype=float)
    return vapor_mass_flow_kg_s / np.maximum(vapor_mass_flow_kg_s + liquid_mass_flow_kg_s, 1e-12)


def homogeneous_equilibrium_slip_ratio(mass_quality: float | np.ndarray | None = None) -> Any:
    if mass_quality is None:
        return 1.0
    mass_quality = np.asarray(mass_quality, dtype=float)
    return np.ones_like(mass_quality, dtype=float)


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
    mass_quality, rho_l_kg_m3, rho_g_kg_m3, slip_ratio = np.broadcast_arrays(
        mass_quality,
        rho_l_kg_m3,
        rho_g_kg_m3,
        slip_ratio,
    )

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


def zivi_1964_slip_ratio(
    rho_l_kg_m3: float | np.ndarray,
    rho_g_kg_m3: float | np.ndarray,
) -> Any:
    rho_l_kg_m3 = np.maximum(np.asarray(rho_l_kg_m3, dtype=float), 1e-12)
    rho_g_kg_m3 = np.maximum(np.asarray(rho_g_kg_m3, dtype=float), 1e-12)
    return np.power(rho_l_kg_m3 / rho_g_kg_m3, 1.0 / 3.0)


def mixture_density_from_void_fraction(
    gas_volume_fraction: float | np.ndarray,
    liquid_volume_fraction: float | np.ndarray,
    rho_l_kg_m3: float | np.ndarray,
    rho_g_kg_m3: float | np.ndarray,
) -> Any:
    return (
        np.asarray(liquid_volume_fraction, dtype=float) * np.asarray(rho_l_kg_m3, dtype=float)
        + np.asarray(gas_volume_fraction, dtype=float) * np.asarray(rho_g_kg_m3, dtype=float)
    )
