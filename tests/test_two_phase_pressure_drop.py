from __future__ import annotations

import numpy as np
import pytest

from published_friction import (
    SourceRequiredCorrelationError,
    chisholm_constant,
    friedel_1979_pressure_gradient_pa_per_m,
    lockhart_martinelli_chisholm_pressure_gradient_pa_per_m,
    martinelli_parameter,
    muller_steinhagen_heck_1986_pressure_gradient_pa_per_m,
    single_phase_pressure_gradient_pa_per_m,
    two_phase_multiplier_liquid_reference,
)
from two_phase_closures import closure_state_from_model, friction_factor_from_model


def test_chisholm_constant_matches_laminar_turbulent_table() -> None:
    gas_reynolds = np.asarray([3000.0, 3000.0, 1000.0, 1000.0])
    liquid_reynolds = np.asarray([3000.0, 1000.0, 3000.0, 1000.0])

    np.testing.assert_allclose(chisholm_constant(gas_reynolds, liquid_reynolds), np.asarray([20.0, 12.0, 10.0, 5.0]))


def test_lockhart_martinelli_chisholm_multiplier_is_positive() -> None:
    martinelli_x = martinelli_parameter(
        liquid_mass_flow_kg_s=np.asarray([0.08, 0.04]),
        vapor_mass_flow_kg_s=np.asarray([0.02, 0.06]),
        liquid_friction_factor=0.025,
        gas_friction_factor=0.018,
        liquid_specific_volume_m3_per_kg=1.0 / 900.0,
        vapor_specific_volume_m3_per_kg=1.0 / 15.0,
    )
    multiplier = two_phase_multiplier_liquid_reference(martinelli_x=martinelli_x, chisholm_c=20.0)

    assert np.all(martinelli_x > 0.0)
    assert np.all(multiplier > 1.0)


def test_pressure_gradient_is_positive_for_positive_mass_flux() -> None:
    gradient = single_phase_pressure_gradient_pa_per_m(
        mass_flux_kg_m2_s=50.0,
        specific_volume_m3_per_kg=1.0 / 900.0,
        friction_factor=0.025,
        hydraulic_diameter_m=0.0265,
    )
    two_phase_gradient = lockhart_martinelli_chisholm_pressure_gradient_pa_per_m(
        liquid_reference_pressure_gradient_pa_per_m=gradient,
        martinelli_x=2.0,
        chisholm_c=20.0,
    )

    assert gradient > 0.0
    assert two_phase_gradient > gradient


def test_zero_vapor_flow_is_regularized_without_nan_or_inf() -> None:
    martinelli_x = martinelli_parameter(
        liquid_mass_flow_kg_s=0.1,
        vapor_mass_flow_kg_s=0.0,
        liquid_friction_factor=0.025,
        gas_friction_factor=0.018,
        liquid_specific_volume_m3_per_kg=1.0 / 900.0,
        vapor_specific_volume_m3_per_kg=1.0 / 15.0,
    )
    multiplier = two_phase_multiplier_liquid_reference(martinelli_x=martinelli_x, chisholm_c=20.0)

    assert np.isfinite(martinelli_x)
    assert np.isfinite(multiplier)
    assert multiplier >= 1.0


def test_published_closure_pressure_gradient_uses_lockhart_martinelli_chisholm() -> None:
    state = closure_state_from_model(
        model="zivi",
        vapor_mass_flow_kg_s=0.02,
        liquid_mass_flow_kg_s=0.08,
        gas_mass_flux_kg_m2_s=4.0,
        liquid_mass_flux_kg_m2_s=16.0,
        vapor_specific_volume_m3_per_kg=1.0 / 15.0,
        liquid_specific_volume_m3_per_kg=1.0 / 900.0,
        phi2l=5.0,
        hydraulic_diameter_m=0.0265,
        relative_roughness=1e-4 / 0.0265,
        vapor_dynamic_viscosity_pa_s=1.4e-5,
        liquid_dynamic_viscosity_pa_s=1.2e-4,
        friction_model="colebrook_white",
    )

    assert state.selected_friction_model == "lockhart_martinelli_chisholm"
    assert state.effective_two_phase_multiplier is not None
    assert state.effective_two_phase_multiplier > 0.0
    assert state.friction_pressure_gradient_pa_per_m is not None
    assert state.friction_pressure_gradient_pa_per_m > 0.0
    assert friction_factor_from_model(1.0e5, 1e-4 / 0.0265, "colebrook_white") > 0.0


def test_muller_steinhagen_heck_guard_requires_primary_source_audit() -> None:
    with pytest.raises(SourceRequiredCorrelationError, match="Muller-Steinhagen-Heck 1986") as exc_info:
        muller_steinhagen_heck_1986_pressure_gradient_pa_per_m()
    message = str(exc_info.value)
    assert "not implemented" in message
    assert "primary-source" in message
    assert "source audit" in message


def test_friedel_guard_requires_primary_source_audit() -> None:
    with pytest.raises(SourceRequiredCorrelationError, match="Friedel 1979") as exc_info:
        friedel_1979_pressure_gradient_pa_per_m()
    message = str(exc_info.value)
    assert "not implemented" in message
    assert "primary-source" in message
    assert "source audit" in message
