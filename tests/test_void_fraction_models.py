from __future__ import annotations

import numpy as np
import pytest

from published_void_fraction import (
    homogeneous_equilibrium_slip_ratio,
    mass_quality_from_mass_flows,
    mixture_density_from_void_fraction,
    void_fraction_from_quality,
    zivi_1964_slip_ratio,
)
from two_phase_closures import closure_state_from_model, zivi_slip_ratio


def test_mass_quality_and_void_fraction_limits_are_bounded() -> None:
    mass_quality = mass_quality_from_mass_flows(
        vapor_mass_flow_kg_s=np.asarray([0.0, 0.1, 1.0]),
        liquid_mass_flow_kg_s=np.asarray([1.0, 0.9, 0.0]),
    )

    liquid_fraction, gas_fraction = void_fraction_from_quality(
        mass_quality=mass_quality,
        rho_l_kg_m3=900.0,
        rho_g_kg_m3=15.0,
        slip_ratio=1.0,
    )

    np.testing.assert_allclose(mass_quality, np.asarray([0.0, 0.1, 1.0]))
    assert np.all(gas_fraction >= 0.0)
    assert np.all(gas_fraction <= 1.0)
    np.testing.assert_allclose(liquid_fraction + gas_fraction, np.ones_like(gas_fraction))
    assert gas_fraction[0] == pytest.approx(0.0)
    assert gas_fraction[-1] == pytest.approx(1.0)


def test_homogeneous_equilibrium_uses_unit_slip() -> None:
    assert homogeneous_equilibrium_slip_ratio() == pytest.approx(1.0)
    np.testing.assert_allclose(
        homogeneous_equilibrium_slip_ratio(np.asarray([0.0, 0.5, 1.0])),
        np.ones(3),
    )


def test_zivi_slip_is_greater_than_one_for_dense_liquid() -> None:
    zivi_slip = zivi_1964_slip_ratio(rho_l_kg_m3=900.0, rho_g_kg_m3=15.0)

    assert zivi_slip > 1.0
    assert zivi_slip == pytest.approx(zivi_slip_ratio(900.0, 15.0))


def test_mixture_density_stays_between_phase_densities() -> None:
    liquid_fraction, gas_fraction = void_fraction_from_quality(
        mass_quality=np.asarray([0.05, 0.5, 0.95]),
        rho_l_kg_m3=900.0,
        rho_g_kg_m3=15.0,
        slip_ratio=zivi_1964_slip_ratio(900.0, 15.0),
    )
    mixture_density = mixture_density_from_void_fraction(
        gas_volume_fraction=gas_fraction,
        liquid_volume_fraction=liquid_fraction,
        rho_l_kg_m3=900.0,
        rho_g_kg_m3=15.0,
    )

    assert np.all(mixture_density > 15.0)
    assert np.all(mixture_density < 900.0)
    assert np.all(np.diff(mixture_density) < 0.0)


def test_published_closure_states_select_only_published_void_models() -> None:
    common_args = {
        "vapor_mass_flow_kg_s": 0.02,
        "liquid_mass_flow_kg_s": 0.08,
        "gas_mass_flux_kg_m2_s": 4.0,
        "liquid_mass_flux_kg_m2_s": 16.0,
        "vapor_specific_volume_m3_per_kg": 1.0 / 15.0,
        "liquid_specific_volume_m3_per_kg": 1.0 / 900.0,
        "phi2l": 5.0,
    }

    homogeneous = closure_state_from_model(model="homogeneous_equilibrium", **common_args)
    zivi = closure_state_from_model(model="zivi", **common_args)

    assert homogeneous.selected_void_fraction_model == "homogeneous_equilibrium"
    assert homogeneous.selected_friction_model == "lockhart_martinelli_chisholm"
    assert homogeneous.slip_ratio == pytest.approx(1.0)
    assert zivi.selected_void_fraction_model == "zivi"
    assert zivi.selected_friction_model == "lockhart_martinelli_chisholm"
    assert zivi.slip_ratio > 1.0
