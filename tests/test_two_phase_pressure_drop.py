from __future__ import annotations

import numpy as np
import pytest

from published_friction import (
    SourceRequiredCorrelationError,
    chisholm_constant,
    friedel_th3337_candidate_pressure_gradient_pa_per_m,
    friedel_th3337_candidate_two_phase_multiplier,
    friedel_1979_pressure_gradient_pa_per_m,
    lockhart_martinelli_chisholm_pressure_gradient_pa_per_m,
    martinelli_parameter,
    moreno_quiben_th3337_candidate_annular_interfacial_friction_factor,
    moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m,
    moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m,
    moreno_quiben_th3337_candidate_gas_friction_factor,
    moreno_quiben_th3337_candidate_mist_friction_factor,
    moreno_quiben_th3337_candidate_mist_homogeneous_void_fraction,
    moreno_quiben_th3337_candidate_mist_mixture_density_kg_m3,
    moreno_quiben_th3337_candidate_mist_mixture_viscosity_pa_s,
    moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m,
    moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m,
    moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m,
    moreno_quiben_th3337_candidate_stratified_wavy_two_phase_friction_factor,
    muller_steinhagen_heck_th3337_candidate_pressure_gradient_pa_per_m,
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


def test_msh_th3337_candidate_helper_matches_documented_formula() -> None:
    gradient = muller_steinhagen_heck_th3337_candidate_pressure_gradient_pa_per_m(
        mass_quality=0.3,
        mass_flux_kg_m2_s=200.0,
        hydraulic_diameter_m=0.01,
        liquid_density_kg_m3=900.0,
        vapor_density_kg_m3=10.0,
        liquid_friction_factor=0.005,
        vapor_friction_factor=0.004,
    )

    assert gradient == pytest.approx(1806.9606433768)

    with pytest.raises(ValueError, match="0 <= x < 1"):
        muller_steinhagen_heck_th3337_candidate_pressure_gradient_pa_per_m(
            mass_quality=1.0,
            mass_flux_kg_m2_s=200.0,
            hydraulic_diameter_m=0.01,
            liquid_density_kg_m3=900.0,
            vapor_density_kg_m3=10.0,
            liquid_friction_factor=0.005,
            vapor_friction_factor=0.004,
        )


def test_moreno_quiben_th3337_annular_candidate_helper_matches_documented_formula() -> None:
    interfacial_friction = moreno_quiben_th3337_candidate_annular_interfacial_friction_factor(
        film_thickness_m=0.0005,
        hydraulic_diameter_m=0.01,
        liquid_density_kg_m3=900.0,
        vapor_density_kg_m3=30.0,
        liquid_viscosity_pa_s=2.0e-4,
        vapor_viscosity_pa_s=1.2e-5,
        surface_tension_n_m=0.02,
        liquid_weber_number=50.0,
    )
    gradient = moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m(
        film_thickness_m=0.0005,
        hydraulic_diameter_m=0.01,
        liquid_density_kg_m3=900.0,
        vapor_density_kg_m3=30.0,
        liquid_viscosity_pa_s=2.0e-4,
        vapor_viscosity_pa_s=1.2e-5,
        surface_tension_n_m=0.02,
        liquid_weber_number=50.0,
        vapor_velocity_m_s=8.0,
    )

    assert interfacial_friction == pytest.approx(0.0314880634)
    assert gradient == pytest.approx(12091.4163488975)

    with pytest.raises(ValueError, match="hydraulic_diameter_m/2"):
        moreno_quiben_th3337_candidate_annular_interfacial_friction_factor(
            film_thickness_m=0.005,
            hydraulic_diameter_m=0.01,
            liquid_density_kg_m3=900.0,
            vapor_density_kg_m3=30.0,
            liquid_viscosity_pa_s=2.0e-4,
            vapor_viscosity_pa_s=1.2e-5,
            surface_tension_n_m=0.02,
            liquid_weber_number=50.0,
        )


def test_moreno_quiben_th3337_mist_candidate_helper_matches_documented_formula() -> None:
    alpha_h = moreno_quiben_th3337_candidate_mist_homogeneous_void_fraction(
        mass_quality=0.8,
        liquid_density_kg_m3=900.0,
        vapor_density_kg_m3=10.0,
    )
    rho_m = moreno_quiben_th3337_candidate_mist_mixture_density_kg_m3(
        mass_quality=0.8,
        liquid_density_kg_m3=900.0,
        vapor_density_kg_m3=10.0,
    )
    mu_m = moreno_quiben_th3337_candidate_mist_mixture_viscosity_pa_s(
        mass_quality=0.8,
        liquid_viscosity_pa_s=1.0e-3,
        vapor_viscosity_pa_s=1.0e-5,
    )
    friction_factor = moreno_quiben_th3337_candidate_mist_friction_factor(
        mass_quality=0.8,
        mass_flux_kg_m2_s=200.0,
        hydraulic_diameter_m=0.01,
        liquid_viscosity_pa_s=1.0e-3,
        vapor_viscosity_pa_s=1.0e-5,
    )
    gradient = moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m(
        mass_quality=0.8,
        mass_flux_kg_m2_s=200.0,
        hydraulic_diameter_m=0.01,
        liquid_density_kg_m3=900.0,
        vapor_density_kg_m3=10.0,
        liquid_viscosity_pa_s=1.0e-3,
        vapor_viscosity_pa_s=1.0e-5,
    )

    assert alpha_h == pytest.approx(0.9972299169)
    assert rho_m == pytest.approx(12.4653739612)
    assert mu_m == pytest.approx(0.000208)
    assert friction_factor == pytest.approx(0.0079778419)
    assert gradient == pytest.approx(5120.0016535769)

    gas_limit_gradient = moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m(
        mass_quality=1.0,
        mass_flux_kg_m2_s=200.0,
        hydraulic_diameter_m=0.01,
        liquid_density_kg_m3=900.0,
        vapor_density_kg_m3=10.0,
        liquid_viscosity_pa_s=1.0e-3,
        vapor_viscosity_pa_s=1.0e-5,
    )
    assert gas_limit_gradient == pytest.approx(2988.5434844500)

    with pytest.raises(ValueError, match="0 < x <= 1"):
        moreno_quiben_th3337_candidate_mist_homogeneous_void_fraction(
            mass_quality=0.0,
            liquid_density_kg_m3=900.0,
            vapor_density_kg_m3=10.0,
        )


def test_moreno_quiben_th3337_dryout_pressure_drop_interpolation_matches_documented_formula() -> None:
    midpoint_gradient = moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m(
        mass_quality=0.7,
        dryout_inception_quality=0.5,
        dryout_completion_quality=0.9,
        inception_pressure_gradient_pa_per_m=10000.0,
        mist_completion_pressure_gradient_pa_per_m=3000.0,
    )
    inception_gradient = moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m(
        mass_quality=0.5,
        dryout_inception_quality=0.5,
        dryout_completion_quality=0.9,
        inception_pressure_gradient_pa_per_m=10000.0,
        mist_completion_pressure_gradient_pa_per_m=3000.0,
    )
    completion_gradient = moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m(
        mass_quality=0.9,
        dryout_inception_quality=0.5,
        dryout_completion_quality=0.9,
        inception_pressure_gradient_pa_per_m=10000.0,
        mist_completion_pressure_gradient_pa_per_m=3000.0,
    )

    assert midpoint_gradient == pytest.approx(6500.0)
    assert inception_gradient == pytest.approx(10000.0)
    assert completion_gradient == pytest.approx(3000.0)

    with pytest.raises(ValueError, match="must stay between"):
        moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m(
            mass_quality=0.95,
            dryout_inception_quality=0.5,
            dryout_completion_quality=0.9,
            inception_pressure_gradient_pa_per_m=10000.0,
            mist_completion_pressure_gradient_pa_per_m=3000.0,
        )

    with pytest.raises(ValueError, match="must be < dryout_completion_quality"):
        moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m(
            mass_quality=0.7,
            dryout_inception_quality=0.9,
            dryout_completion_quality=0.9,
            inception_pressure_gradient_pa_per_m=10000.0,
            mist_completion_pressure_gradient_pa_per_m=3000.0,
        )


def test_moreno_quiben_th3337_stratified_wavy_candidate_helper_matches_documented_formula() -> None:
    gas_friction = moreno_quiben_th3337_candidate_gas_friction_factor(
        mass_quality=0.5,
        mass_flux_kg_m2_s=200.0,
        hydraulic_diameter_m=0.01,
        vapor_viscosity_pa_s=1.0e-5,
    )
    two_phase_friction = moreno_quiben_th3337_candidate_stratified_wavy_two_phase_friction_factor(
        dry_perimeter_fraction=0.25,
        gas_friction_factor=gas_friction,
        annular_interfacial_friction_factor=0.03,
    )
    gradient = moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m(
        dry_perimeter_fraction=0.25,
        gas_friction_factor=gas_friction,
        annular_interfacial_friction_factor=0.03,
        hydraulic_diameter_m=0.01,
        vapor_density_kg_m3=20.0,
        vapor_velocity_m_s=10.0,
    )

    assert gas_friction == pytest.approx(0.0044424965)
    assert two_phase_friction == pytest.approx(0.0236106241)
    assert gradient == pytest.approx(9444.2496469004)

    with pytest.raises(ValueError, match="0 <= value <= 1"):
        moreno_quiben_th3337_candidate_stratified_wavy_two_phase_friction_factor(
            dry_perimeter_fraction=-0.1,
            gas_friction_factor=gas_friction,
            annular_interfacial_friction_factor=0.03,
        )


def test_moreno_quiben_th3337_slug_interpolation_matches_documented_formula() -> None:
    gradient = moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m(
        liquid_only_pressure_gradient_pa_per_m=1000.0,
        limiting_branch_pressure_gradient_pa_per_m=5000.0,
        intermittent_annular_boundary_void_fraction=0.5,
    )
    liquid_limit = moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m(
        liquid_only_pressure_gradient_pa_per_m=1000.0,
        limiting_branch_pressure_gradient_pa_per_m=5000.0,
        intermittent_annular_boundary_void_fraction=0.0,
    )
    branch_limit = moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m(
        liquid_only_pressure_gradient_pa_per_m=1000.0,
        limiting_branch_pressure_gradient_pa_per_m=5000.0,
        intermittent_annular_boundary_void_fraction=1.0,
    )

    assert gradient == pytest.approx(5045.3784915223)
    assert liquid_limit == pytest.approx(1000.0)
    assert branch_limit == pytest.approx(5000.0)

    with pytest.raises(ValueError, match="0 <= value <= 1"):
        moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m(
            liquid_only_pressure_gradient_pa_per_m=1000.0,
            limiting_branch_pressure_gradient_pa_per_m=5000.0,
            intermittent_annular_boundary_void_fraction=1.2,
        )


def test_friedel_th3337_candidate_helper_matches_documented_formula() -> None:
    multiplier = friedel_th3337_candidate_two_phase_multiplier(
        mass_quality=0.3,
        mass_flux_kg_m2_s=200.0,
        hydraulic_diameter_m=0.01,
        liquid_density_kg_m3=900.0,
        vapor_density_kg_m3=10.0,
        liquid_viscosity_pa_s=1.0e-3,
        vapor_viscosity_pa_s=1.0e-5,
        surface_tension_n_m=0.02,
        liquid_friction_factor=0.005,
        vapor_friction_factor=0.004,
    )
    gradient = friedel_th3337_candidate_pressure_gradient_pa_per_m(
        liquid_reference_pressure_gradient_pa_per_m=44.4444444444,
        mass_quality=0.3,
        mass_flux_kg_m2_s=200.0,
        hydraulic_diameter_m=0.01,
        liquid_density_kg_m3=900.0,
        vapor_density_kg_m3=10.0,
        liquid_viscosity_pa_s=1.0e-3,
        vapor_viscosity_pa_s=1.0e-5,
        surface_tension_n_m=0.02,
        liquid_friction_factor=0.005,
        vapor_friction_factor=0.004,
    )

    assert multiplier == pytest.approx(24.7228013381)
    assert gradient == pytest.approx(1098.7911705830)

    with pytest.raises(ValueError, match="must be < 1"):
        friedel_th3337_candidate_two_phase_multiplier(
            mass_quality=0.3,
            mass_flux_kg_m2_s=200.0,
            hydraulic_diameter_m=0.01,
            liquid_density_kg_m3=900.0,
            vapor_density_kg_m3=10.0,
            liquid_viscosity_pa_s=1.0e-5,
            vapor_viscosity_pa_s=1.0e-5,
            surface_tension_n_m=0.02,
            liquid_friction_factor=0.005,
            vapor_friction_factor=0.004,
        )
