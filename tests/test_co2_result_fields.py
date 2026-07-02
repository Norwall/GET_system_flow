from __future__ import annotations

import pytest

from co2_results import SteadyLoopResult
from get_co2_model import CO2MathcadModel
from two_phase_closures import closure_state_from_model


def test_run_exposes_structured_diagnostics_and_alias_fields(co2_model: CO2MathcadModel) -> None:
    result = co2_model.run(2.5, 76.68, 200.0, 0.0)
    structured_result = co2_model.run_result(2.5, 76.68, 200.0, 0.0)
    pass_result = structured_result.pass_result

    assert isinstance(structured_result, SteadyLoopResult)
    assert structured_result.converged is True
    assert pass_result is not None

    assert result["solver_status"] == "converged"
    assert result["failure_reason"] is None
    assert result["root_bracket"] is not None
    assert result["n_sign_changes"] >= 1
    assert result["closure_name"] == "worksheet_compatible+darcy_friction_factor+martinelli+chisholm"
    assert result["property_model_name"] == "CO2SaturationProperties"
    assert result["fluid"] == "CO2"
    assert result["property_backend"] == "mathcad_table"
    assert "CO2.xmcd" in result["property_source"]
    assert "Mathcad CO2 table backend" in result["property_warning"]
    assert result["near_critical_warning"] == ""
    assert result["heat_transfer_model"] == "prescribed_heat_input"
    assert result["boiling_heat_transfer_status"] == "diagnostic_only_source_required"
    assert result["boiling_heat_flux_w_m2"] > 0.0
    assert result["dryout_limit"] == "not_evaluated_source_required"
    assert result["failure_class"] == "none"

    assert result["GG0_liq_equiv_lph"] == pytest.approx(result["GG0_lph"], rel=0.0, abs=0.0)
    assert result["GG0_gas_lph"] > result["GG0_liq_equiv_lph"]
    assert result["outlet_gas_volume_fraction_true"] == pytest.approx(result["phiG1_true"], rel=0.0, abs=0.0)
    assert result["outlet_gas_volume_fraction_closure"] == pytest.approx(result["phiG_formula"], rel=0.0, abs=0.0)
    assert result["model_mode"] == "worksheet_compatible"
    assert result["n_section_states"] == 5
    assert result["n_control_volumes"] == 1200
    assert result["boiling_onset_position_m"] == pytest.approx(result["preboiling_evaporator_length_m"])
    assert result["preboiling_evaporator_length_m"] + result["boiling_length_m"] == pytest.approx(200.0)
    assert result["section_state_names"] == "downcomer,riser,evaporator_preboiling,evaporator_boiling,condenser"

    assert len(pass_result.section_states) == 5
    assert pass_result.evaporator_profile is not None
    assert pass_result.evaporator_profile.n_points == 1200
    assert pass_result.section_states[3].phase_regime == "boiling_two_phase"
    assert pass_result.section_states[3].pressure_drop_pa == pytest.approx(result["sumPsiL_Pa"])


def test_failed_run_returns_failure_diagnostics(co2_model: CO2MathcadModel) -> None:
    result = co2_model.run(2.5, 130.0, 200.0, 0.0)

    assert result["converged"] is False
    assert result["solver_status"] == "no_root_bracket"
    assert result["failure_reason"] is not None
    assert result["root_bracket"] is None
    assert result["n_sign_changes"] == 0


@pytest.mark.slow
@pytest.mark.distributed
def test_distributed_mode_builds_nontrivial_evaporator_temperature_profile(co2_model: CO2MathcadModel) -> None:
    worksheet_result = co2_model.run_result(2.5, 76.68, 200.0, 0.0, mode="worksheet_compatible")
    distributed_result = co2_model.run_result(2.5, 76.68, 200.0, 0.0, mode="distributed_steady")
    profile = distributed_result.pass_result.evaporator_profile if distributed_result.pass_result is not None else None

    assert distributed_result.converged is True
    assert distributed_result.pass_result is not None
    assert profile is not None
    assert distributed_result.to_dict()["model_mode"] == "distributed_steady"
    assert distributed_result.pass_result.required_head_m == pytest.approx(2.5, abs=5e-3)
    assert distributed_result.circulation_factor is not None
    assert worksheet_result.circulation_factor is not None
    assert distributed_result.circulation_factor > 0.0
    assert distributed_result.circulation_factor != pytest.approx(worksheet_result.circulation_factor, rel=1e-3)

    phase_regime = profile.phase_regime
    temperatures = profile.local_temperature_c
    pressures = profile.local_pressure_pa
    boiling_onset_index = phase_regime.index("boiling_two_phase")

    assert phase_regime[0] == "single_liquid_heating"
    assert temperatures[0] < temperatures[boiling_onset_index]
    assert temperatures[boiling_onset_index] >= temperatures[-1]
    assert pressures[0] > pressures[boiling_onset_index]
    assert pressures[boiling_onset_index] >= pressures[-1]
    assert distributed_result.pass_result.riser_profile is not None
    assert distributed_result.to_dict()["n_riser_points"] > 0
    assert distributed_result.to_dict()["driving_pressure_pa"] > 0.0
    assert distributed_result.to_dict()["effective_density_difference_kg_m3"] > 0.0
    assert distributed_result.to_dict()["outlet_slip_ratio"] > 1.0
    assert distributed_result.to_dict()["evaporator_dominant_flow_regime"] != ""
    assert distributed_result.to_dict()["riser_dominant_flow_regime"] != ""
    assert distributed_result.to_dict()["evaporator_flow_regime_summary"] != ""
    assert distributed_result.to_dict()["riser_flow_regime_summary"] != ""
    riser_profile = distributed_result.pass_result.riser_profile
    assert riser_profile.local_pressure_pa[0] > riser_profile.local_pressure_pa[-1]
    assert riser_profile.local_temperature_c[0] > riser_profile.local_temperature_c[-1]
    assert len(profile.flow_regime) == profile.n_points
    assert len(riser_profile.flow_regime) == riser_profile.n_points
    assert distributed_result.pass_result.section_states[1].outlet_vapor_mass_flow_kg_s > 0.0
    assert distributed_result.pass_result.section_states[1].phase_regime == distributed_result.to_dict()["riser_dominant_flow_regime"]


@pytest.mark.slow
@pytest.mark.distributed
def test_alternative_closure_models_change_branch_characteristics(co2_model: CO2MathcadModel) -> None:
    worksheet = co2_model.run_result(2.5, 76.68, 200.0, 0.0, mode="distributed_steady", closure_model="worksheet_compatible")
    homogeneous = co2_model.run_result(2.5, 76.68, 200.0, 0.0, mode="distributed_steady", closure_model="homogeneous_equilibrium")
    zivi = co2_model.run_result(2.5, 76.68, 200.0, 0.0, mode="distributed_steady", closure_model="zivi")
    regime_aware = co2_model.run_result(2.5, 76.68, 200.0, 0.0, mode="distributed_steady", closure_model="regime_aware")

    assert worksheet.converged is True
    assert homogeneous.converged is True
    assert zivi.converged is True
    assert regime_aware.converged is True

    assert worksheet.circulation_factor is not None
    assert homogeneous.circulation_factor is not None
    assert zivi.circulation_factor is not None
    assert regime_aware.circulation_factor is not None

    assert homogeneous.to_dict()["outlet_slip_ratio"] == pytest.approx(1.0, rel=1e-12)
    assert zivi.to_dict()["outlet_slip_ratio"] > 1.0
    assert worksheet.to_dict()["outlet_slip_ratio"] > zivi.to_dict()["outlet_slip_ratio"]
    assert zivi.to_dict()["outlet_slip_ratio"] > regime_aware.to_dict()["outlet_slip_ratio"] > 1.0

    assert regime_aware.circulation_factor > homogeneous.circulation_factor > zivi.circulation_factor > worksheet.circulation_factor
    assert homogeneous.to_dict()["phiG_formula"] > zivi.to_dict()["phiG_formula"] > worksheet.to_dict()["phiG_formula"] > regime_aware.to_dict()["phiG_formula"]
    assert "worksheet_compatible" in worksheet.to_dict()["closure_name"]
    assert "homogeneous_equilibrium" in homogeneous.to_dict()["closure_name"]
    assert "zivi" in zivi.to_dict()["closure_name"]
    assert "regime_aware" in regime_aware.to_dict()["closure_name"]
    assert worksheet.to_dict()["outlet_selected_void_fraction_model"] == "worksheet_compatible"
    assert worksheet.to_dict()["outlet_selected_friction_model"] == "lockhart_martinelli_chisholm"
    assert homogeneous.to_dict()["outlet_selected_void_fraction_model"] == "homogeneous_equilibrium"
    assert zivi.to_dict()["outlet_selected_void_fraction_model"] == "zivi"
    assert regime_aware.to_dict()["outlet_selected_void_fraction_model"] == "zivi"
    assert regime_aware.to_dict()["outlet_selected_friction_model"] == "separated_shear"
    assert regime_aware.to_dict()["evaporator_dominant_flow_regime"] != ""
    assert regime_aware.to_dict()["riser_dominant_flow_regime"] != ""


def test_regime_aware_closure_switches_to_direct_regime_specific_models() -> None:
    bubbly_vertical = closure_state_from_model(
        model="regime_aware",
        vapor_mass_flow_kg_s=0.001,
        liquid_mass_flow_kg_s=0.2,
        gas_mass_flux_kg_m2_s=3.0,
        liquid_mass_flux_kg_m2_s=400.0,
        vapor_specific_volume_m3_per_kg=0.02,
        liquid_specific_volume_m3_per_kg=0.0013,
        phi2l=1.5,
        orientation="vertical_up",
        hydraulic_diameter_m=0.0265,
        relative_roughness=0.0038,
        vapor_dynamic_viscosity_pa_s=1.5e-5,
        liquid_dynamic_viscosity_pa_s=8e-5,
    )
    annular_horizontal = closure_state_from_model(
        model="regime_aware",
        vapor_mass_flow_kg_s=0.05,
        liquid_mass_flow_kg_s=0.02,
        gas_mass_flux_kg_m2_s=180.0,
        liquid_mass_flux_kg_m2_s=60.0,
        vapor_specific_volume_m3_per_kg=0.08,
        liquid_specific_volume_m3_per_kg=0.0013,
        phi2l=6.0,
        orientation="horizontal",
        hydraulic_diameter_m=0.0265,
        relative_roughness=0.0038,
        vapor_dynamic_viscosity_pa_s=1.5e-5,
        liquid_dynamic_viscosity_pa_s=8e-5,
    )

    assert bubbly_vertical.diagnostic_regime == "bubbly"
    assert bubbly_vertical.selected_void_fraction_model == "drift_flux"
    assert bubbly_vertical.selected_friction_model == "homogeneous_mixture"
    assert bubbly_vertical.friction_pressure_gradient_pa_per_m is not None

    assert annular_horizontal.diagnostic_regime == "annular_mist"
    assert annular_horizontal.selected_void_fraction_model == "annular_core"
    assert annular_horizontal.selected_friction_model == "annular_film"
    assert annular_horizontal.friction_pressure_gradient_pa_per_m is not None


@pytest.mark.slow
@pytest.mark.distributed
def test_regime_aware_high_load_reaches_annular_film_branch(co2_model: CO2MathcadModel) -> None:
    result = co2_model.run_result(
        2.5,
        160.0,
        200.0,
        0.0,
        mode="distributed_steady",
        closure_model="regime_aware",
    )
    result_dict = result.to_dict()

    assert result.converged is True
    assert result_dict["outlet_selected_void_fraction_model"] == "annular_core"
    assert result_dict["outlet_selected_friction_model"] == "annular_film"
    assert result_dict["phiG_formula"] > 0.8
