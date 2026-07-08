from __future__ import annotations

import pytest

from boiling_heat_transfer import (
    CHEN_1962_SOURCE_CANDIDATE,
    Chen1962AuditRecord,
    Chen1962CandidateFlowBoilingResult,
    WallSoilBoundary,
    WojtanTh2978CandidateDryoutLimitResult,
    WojtanTh3337CandidateDryoutBoundaryResult,
    chen_1962_audit_record,
    chen_1962_candidate_f_factor,
    chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si,
    chen_1962_candidate_heat_transfer_coefficient_si,
    chen_1962_candidate_inverse_martinelli_parameter,
    chen_1962_candidate_suppression_factor,
    chen_1962_candidate_two_phase_reynolds,
    chen_1962_source_candidate,
    diagnostics_for_solver_status,
    normalize_heat_transfer_model,
    wojtan_th2978_candidate_dryout_completion_quality,
    wojtan_th2978_candidate_dryout_inception_quality,
    wojtan_th2978_candidate_dryout_limits,
    wojtan_th3337_candidate_dryout_boundaries,
    wojtan_th3337_candidate_dryout_completion_quality,
    wojtan_th3337_candidate_dryout_inception_quality,
)
from get_co2_model import CO2MathcadModel


def test_prescribed_heat_input_reports_diagnostic_heat_flux_without_wall_temperature(
    co2_model: CO2MathcadModel,
) -> None:
    result = co2_model.run(2.5, 76.68, 200.0, 0.0)
    perimeter_m = 4.0 * co2_model.geometry.flow_area_m2 / co2_model.geometry.hydraulic_diameter_m

    assert result["converged"] is True
    assert result["heat_transfer_model"] == "prescribed_heat_input"
    assert result["boiling_heat_transfer_status"] == "diagnostic_only_source_required"
    assert result["boiling_heat_flux_w_m2"] == pytest.approx(76.68 / perimeter_m)
    assert result["boiling_heat_transfer_limit"] == "not_evaluated_source_required"
    assert result["dryout_limit"] == "not_evaluated_source_required"
    assert result["failure_class"] == "none"
    assert any("not implemented" in warning for warning in result["warnings"])


def test_wall_coupled_heat_transfer_requires_boundary_conditions(
    co2_model: CO2MathcadModel,
) -> None:
    result = co2_model.run(
        2.5,
        76.68,
        200.0,
        0.0,
        heat_transfer_model="wall_coupled",
    )

    assert result["converged"] is False
    assert result["solver_status"] == "validation_error"
    assert "wall/soil boundary" in result["failure_reason"]
    assert result["heat_transfer_model"] == "wall_coupled"
    assert result["boiling_heat_transfer_limit"] == "requires_wall_boundary"
    assert result["failure_class"] == "validation_error"


def test_wall_coupled_heat_transfer_derives_qtr_from_boundary(
    co2_model: CO2MathcadModel,
) -> None:
    boundary = WallSoilBoundary(
        far_field_temperature_c=5.0,
        effective_conductance_w_m_k=10.0,
    )

    result = co2_model.run(
        2.5,
        1.0,
        200.0,
        0.0,
        heat_transfer_model="wall_coupled",
        wall_soil_boundary=boundary,
    )

    assert result["converged"] is True
    assert result["qtr"] == pytest.approx(50.0)
    assert result["thermal_boundary_model"] == "wall_soil_effective_conductance"
    assert result["wall_soil_temperature_c"] == pytest.approx(5.0)
    assert result["wall_soil_effective_conductance_w_m_k"] == pytest.approx(10.0)
    assert result["wall_soil_delta_t_k"] == pytest.approx(5.0)
    assert result["wall_soil_qtr_w_m"] == pytest.approx(50.0)
    assert result["boiling_heat_transfer_status"] == "diagnostic_only_source_required"
    assert result["boiling_heat_transfer_limit"] == "not_evaluated_source_required"
    assert result["dryout_limit"] == "not_evaluated_source_required"


def test_wall_coupled_heat_transfer_rejects_non_positive_boundary_heat(
    co2_model: CO2MathcadModel,
) -> None:
    result = co2_model.run(
        2.5,
        1.0,
        200.0,
        0.0,
        heat_transfer_model="wall_coupled",
        wall_soil_boundary=WallSoilBoundary(
            far_field_temperature_c=-1.0,
            effective_conductance_w_m_k=10.0,
        ),
    )

    assert result["converged"] is False
    assert result["solver_status"] == "validation_error"
    assert "positive" in result["failure_reason"]
    assert result["boiling_heat_transfer_limit"] == "invalid_wall_boundary"


def test_unknown_heat_transfer_model_is_validation_error(co2_model: CO2MathcadModel) -> None:
    result = co2_model.run(
        2.5,
        76.68,
        200.0,
        0.0,
        heat_transfer_model="kandlikar",
    )

    assert result["converged"] is False
    assert result["solver_status"] == "validation_error"
    assert "Unknown heat_transfer_model" in result["failure_reason"]
    assert result["failure_class"] == "validation_error"


def test_chen_1962_candidate_is_source_gated_not_runtime_released(
    co2_model: CO2MathcadModel,
) -> None:
    audit_record = chen_1962_audit_record()
    candidate = chen_1962_source_candidate()
    result = co2_model.run(
        2.5,
        76.68,
        200.0,
        0.0,
        heat_transfer_model="chen_1962",
    )

    assert normalize_heat_transfer_model("chen_1962") == CHEN_1962_SOURCE_CANDIDATE
    assert result["converged"] is True
    assert result["heat_transfer_model"] == CHEN_1962_SOURCE_CANDIDATE
    assert result["boiling_heat_transfer_status"] == "source_candidate_source_required_not_released"
    assert result["boiling_heat_transfer_limit"] == "not_evaluated_source_required"
    assert result["boiling_heat_transfer_candidate"] == CHEN_1962_SOURCE_CANDIDATE
    assert "10.2172/4636495" in result["boiling_heat_transfer_source"]
    assert result["boiling_heat_transfer_source_status"] == "source_candidate_not_released"
    assert candidate.local_full_text_ref.endswith("/4636495")
    assert isinstance(audit_record, Chen1962AuditRecord)
    assert audit_record.local_full_text_ref == "sources/primary/chen_1962_osti_4636495.pdf"
    assert audit_record.formula_audit_document == "docs/chen_1962_formula_audit_2026-07-06.md"
    assert audit_record.graph_digitization_document == "docs/chen_1962_graph_digitization_2026-07-07.md"
    assert audit_record.graph_review_document == "docs/chen_1962_graph_review_2026-07-08.md"
    assert audit_record.si_mapping_document == "docs/chen_1962_si_mapping_2026-07-07.md"
    assert audit_record.validation_tables_document == "docs/chen_1962_validation_tables_2026-07-07.md"
    assert (
        audit_record.reference_value_audit_document
        == "docs/chen_1962_reference_value_audit_2026-07-08.md"
    )
    assert audit_record.scope_audit_document == "docs/chen_1962_scope_audit_2026-07-08.md"
    assert audit_record.hand_calculation_document == "docs/chen_1962_hand_calculation_2026-07-08.md"
    assert result["boiling_heat_transfer_required_audit_checks"] == list(candidate.required_audit_checks)
    assert result["boiling_heat_transfer_audit_id"] == "HTC-CHEN-1962-SOURCE-CANDIDATE"
    assert result["boiling_heat_transfer_audit_source_status"] == "candidate_only"
    assert result["boiling_heat_transfer_audit_sha256"] == audit_record.local_sha256
    assert result["boiling_heat_transfer_formula_audit_document"] == audit_record.formula_audit_document
    assert result["boiling_heat_transfer_graph_digitization_document"] == audit_record.graph_digitization_document
    assert result["boiling_heat_transfer_graph_review_document"] == audit_record.graph_review_document
    assert result["boiling_heat_transfer_si_mapping_document"] == audit_record.si_mapping_document
    assert (
        result["boiling_heat_transfer_validation_tables_document"]
        == audit_record.validation_tables_document
    )
    assert (
        result["boiling_heat_transfer_reference_value_audit_document"]
        == audit_record.reference_value_audit_document
    )
    assert result["boiling_heat_transfer_scope_audit_document"] == audit_record.scope_audit_document
    assert (
        result["boiling_heat_transfer_hand_calculation_document"]
        == audit_record.hand_calculation_document
    )
    assert "6" in result["boiling_heat_transfer_audited_pages"]
    assert "10-19" in result["boiling_heat_transfer_audited_pages"]
    assert "20-25" in result["boiling_heat_transfer_audited_pages"]
    assert "32-35" in result["boiling_heat_transfer_audited_pages"]
    assert any("Eq. (9)" in item for item in result["boiling_heat_transfer_equation_page_map"])
    assert any("visual scan verifies Eq. (17)" in item for item in result["boiling_heat_transfer_equation_page_map"])
    assert any("Eq. (18)" in item for item in result["boiling_heat_transfer_equation_page_map"])
    assert any("Figs. 7 and 8" in item for item in result["boiling_heat_transfer_equation_page_map"])
    assert any("Vertical axial flow" in item for item in result["boiling_heat_transfer_applicability"])
    assert any("horizontal evaporator is unsupported" in item for item in result["boiling_heat_transfer_applicability"])
    assert any("h_mac = 0.023" in item for item in result["boiling_heat_transfer_equation_structure"])
    assert any("h = h_mic + h_mac" in item for item in result["boiling_heat_transfer_equation_structure"])
    assert any("Forster-Zuber" in item for item in result["boiling_heat_transfer_equation_structure"])
    assert any("Candidate SI mapping" in item for item in result["boiling_heat_transfer_equation_structure"])
    assert any("Candidate graph-axis helpers" in item for item in result["boiling_heat_transfer_equation_structure"])
    assert any("Candidate arithmetic fixtures" in item for item in result["boiling_heat_transfer_equation_structure"])
    assert not any("transcribe Eq. (17)" in item for item in result["boiling_heat_transfer_release_blockers"])
    assert any("candidate SI mapping" in item for item in result["boiling_heat_transfer_release_blockers"])
    assert any("reviewed F and S graph digitization" in item for item in result["boiling_heat_transfer_release_blockers"])
    assert any("no raw HTC measurements" in item for item in result["boiling_heat_transfer_validation_notes"])
    assert any("Reference-value audit" in item for item in result["boiling_heat_transfer_validation_notes"])
    assert any("Scope audit" in item for item in result["boiling_heat_transfer_validation_notes"])
    assert any("Candidate hand-calculation arithmetic" in item for item in result["boiling_heat_transfer_validation_notes"])
    assert result["model_source_status"] == "mixed"


def test_chen_1962_solver_failure_keeps_audit_metadata() -> None:
    diagnostics = diagnostics_for_solver_status(
        heat_transfer_model=CHEN_1962_SOURCE_CANDIDATE,
        solver_status="no_root_bracket",
    )

    result = diagnostics.to_result_fields()

    assert result["boiling_heat_transfer_status"].startswith("source_candidate_source_required")
    assert result["boiling_heat_transfer_audit_id"] == "HTC-CHEN-1962-SOURCE-CANDIDATE"
    assert result["boiling_heat_transfer_audit_local_full_text"].endswith("chen_1962_osti_4636495.pdf")
    assert any("dryout or CHF" in item for item in result["boiling_heat_transfer_release_blockers"])


def test_chen_1962_candidate_graph_helpers_are_not_runtime_release() -> None:
    f_at_unity = chen_1962_candidate_f_factor(1.0)
    f_at_ten = chen_1962_candidate_f_factor(10.0)
    suppression_at_1e5 = chen_1962_candidate_suppression_factor(1.0e5)
    inverse_martinelli = chen_1962_candidate_inverse_martinelli_parameter(
        mass_quality=0.2,
        liquid_density_kg_m3=958.0,
        vapor_density_kg_m3=0.6,
        liquid_viscosity_pa_s=2.8e-4,
        vapor_viscosity_pa_s=1.2e-5,
    )
    two_phase_reynolds = chen_1962_candidate_two_phase_reynolds(
        reynolds_liquid=10000.0,
        f_factor=3.0,
    )

    assert f_at_unity == pytest.approx(2.7088777854)
    assert f_at_ten == pytest.approx(12.9958507345)
    assert suppression_at_1e5 == pytest.approx(0.3820680350)
    assert inverse_martinelli == pytest.approx(8.3744338927)
    assert two_phase_reynolds == pytest.approx(39482.2203885748)

    with pytest.raises(ValueError, match="positive finite"):
        chen_1962_candidate_f_factor(0.0)
    with pytest.raises(ValueError, match="Fig. 7 candidate digitization range"):
        chen_1962_candidate_f_factor(0.09)
    with pytest.raises(ValueError, match="positive finite"):
        chen_1962_candidate_suppression_factor(float("nan"))
    with pytest.raises(ValueError, match="Fig. 8 candidate digitization range"):
        chen_1962_candidate_suppression_factor(1.0e6)
    with pytest.raises(ValueError, match="open interval"):
        chen_1962_candidate_inverse_martinelli_parameter(
            mass_quality=1.0,
            liquid_density_kg_m3=958.0,
            vapor_density_kg_m3=0.6,
            liquid_viscosity_pa_s=2.8e-4,
            vapor_viscosity_pa_s=1.2e-5,
        )
    with pytest.raises(ValueError, match="f_factor"):
        chen_1962_candidate_two_phase_reynolds(reynolds_liquid=10000.0, f_factor=0.0)


def test_chen_1962_candidate_si_helper_matches_documented_hand_calculation() -> None:
    result = chen_1962_candidate_heat_transfer_coefficient_si(
        reynolds_liquid=10000.0,
        prandtl_liquid=2.0,
        diameter_m=0.01,
        liquid_thermal_conductivity_w_m_k=0.6,
        liquid_heat_capacity_j_kg_k=4200.0,
        liquid_density_kg_m3=958.0,
        vapor_density_kg_m3=0.6,
        liquid_viscosity_pa_s=2.8e-4,
        surface_tension_n_m=0.0589,
        latent_heat_j_kg=2.257e6,
        wall_superheat_k=5.0,
        vapor_pressure_difference_pa=18000.0,
        f_factor=3.0,
        suppression_factor=0.4,
    )

    assert result.source_status == "candidate_only_not_runtime_released"
    assert result.h_macro_source == pytest.approx(1524.7435663341)
    assert result.h_micro_source == pytest.approx(241.6266815044)
    assert result.h_total_source == pytest.approx(1766.3702478385)
    assert result.h_macro_w_m2_k == pytest.approx(8657.8954971406)
    assert result.h_micro_w_m2_k == pytest.approx(1372.0199277941)
    assert result.h_total_w_m2_k == pytest.approx(10029.9154249347)

    with pytest.raises(ValueError, match="suppression_factor"):
        chen_1962_candidate_heat_transfer_coefficient_si(
            reynolds_liquid=10000.0,
            prandtl_liquid=2.0,
            diameter_m=0.01,
            liquid_thermal_conductivity_w_m_k=0.6,
            liquid_heat_capacity_j_kg_k=4200.0,
            liquid_density_kg_m3=958.0,
            vapor_density_kg_m3=0.6,
            liquid_viscosity_pa_s=2.8e-4,
            surface_tension_n_m=0.0589,
            latent_heat_j_kg=2.257e6,
            wall_superheat_k=5.0,
            vapor_pressure_difference_pa=18000.0,
            f_factor=3.0,
            suppression_factor=1.1,
        )


def test_chen_1962_candidate_flow_boiling_path_is_not_runtime_release() -> None:
    result = chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si(
        mass_quality=0.2,
        reynolds_liquid=10000.0,
        prandtl_liquid=2.0,
        diameter_m=0.01,
        liquid_thermal_conductivity_w_m_k=0.6,
        liquid_heat_capacity_j_kg_k=4200.0,
        liquid_density_kg_m3=958.0,
        vapor_density_kg_m3=0.6,
        liquid_viscosity_pa_s=2.8e-4,
        vapor_viscosity_pa_s=1.2e-5,
        surface_tension_n_m=0.0589,
        latent_heat_j_kg=2.257e6,
        wall_superheat_k=5.0,
        vapor_pressure_difference_pa=18000.0,
    )

    assert isinstance(result, Chen1962CandidateFlowBoilingResult)
    assert result.source_status == "candidate_only_not_runtime_released"
    assert result.heat_transfer.source_status == "candidate_only_not_runtime_released"
    assert result.inverse_martinelli_parameter == pytest.approx(8.3744338927)
    assert result.f_factor == pytest.approx(11.4390861217)
    assert result.two_phase_reynolds == pytest.approx(210372.5940296686)
    assert result.suppression_factor == pytest.approx(0.2220058995)
    assert result.heat_transfer.h_macro_source == pytest.approx(5813.8909896245)
    assert result.heat_transfer.h_micro_source == pytest.approx(134.1063719014)
    assert result.heat_transfer.h_total_source == pytest.approx(5947.9973615260)
    assert result.heat_transfer.h_total_w_m2_k == pytest.approx(33774.2953703176)

    with pytest.raises(ValueError, match="open interval"):
        chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si(
            mass_quality=0.0,
            reynolds_liquid=10000.0,
            prandtl_liquid=2.0,
            diameter_m=0.01,
            liquid_thermal_conductivity_w_m_k=0.6,
            liquid_heat_capacity_j_kg_k=4200.0,
            liquid_density_kg_m3=958.0,
            vapor_density_kg_m3=0.6,
            liquid_viscosity_pa_s=2.8e-4,
            vapor_viscosity_pa_s=1.2e-5,
            surface_tension_n_m=0.0589,
            latent_heat_j_kg=2.257e6,
            wall_superheat_k=5.0,
            vapor_pressure_difference_pa=18000.0,
        )
    with pytest.raises(ValueError, match="0.01 <= x <= 0.70"):
        chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si(
            mass_quality=0.005,
            reynolds_liquid=10000.0,
            prandtl_liquid=2.0,
            diameter_m=0.01,
            liquid_thermal_conductivity_w_m_k=0.6,
            liquid_heat_capacity_j_kg_k=4200.0,
            liquid_density_kg_m3=958.0,
            vapor_density_kg_m3=0.6,
            liquid_viscosity_pa_s=2.8e-4,
            vapor_viscosity_pa_s=1.2e-5,
            surface_tension_n_m=0.0589,
            latent_heat_j_kg=2.257e6,
            wall_superheat_k=5.0,
            vapor_pressure_difference_pa=18000.0,
        )
    with pytest.raises(ValueError, match="0.01 <= x <= 0.70"):
        chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si(
            mass_quality=0.8,
            reynolds_liquid=10000.0,
            prandtl_liquid=2.0,
            diameter_m=0.01,
            liquid_thermal_conductivity_w_m_k=0.6,
            liquid_heat_capacity_j_kg_k=4200.0,
            liquid_density_kg_m3=958.0,
            vapor_density_kg_m3=0.6,
            liquid_viscosity_pa_s=2.8e-4,
            vapor_viscosity_pa_s=1.2e-5,
            surface_tension_n_m=0.0589,
            latent_heat_j_kg=2.257e6,
            wall_superheat_k=5.0,
            vapor_pressure_difference_pa=18000.0,
        )


def test_wojtan_th3337_candidate_dryout_boundaries_are_not_runtime_release() -> None:
    result = wojtan_th3337_candidate_dryout_boundaries(
        gas_weber_number=200.0,
        gas_froude_number=20.0,
        vapor_density_kg_m3=20.0,
        liquid_density_kg_m3=1000.0,
        heat_flux_ratio_q_qcrit=1.0,
    )

    assert isinstance(result, WojtanTh3337CandidateDryoutBoundaryResult)
    assert result.source_status == "candidate_only_not_runtime_released"
    assert result.dryout_inception_quality == pytest.approx(0.5047352096)
    assert result.dryout_completion_quality == pytest.approx(0.9791233757)
    assert result.dryout_inception_quality == pytest.approx(
        wojtan_th3337_candidate_dryout_inception_quality(
            gas_weber_number=200.0,
            gas_froude_number=20.0,
            vapor_density_kg_m3=20.0,
            liquid_density_kg_m3=1000.0,
            heat_flux_ratio_q_qcrit=1.0,
        )
    )
    assert result.dryout_completion_quality == pytest.approx(
        wojtan_th3337_candidate_dryout_completion_quality(
            gas_weber_number=200.0,
            gas_froude_number=20.0,
            vapor_density_kg_m3=20.0,
            liquid_density_kg_m3=1000.0,
            heat_flux_ratio_q_qcrit=1.0,
        )
    )

    with pytest.raises(ValueError, match="gas_weber_number"):
        wojtan_th3337_candidate_dryout_boundaries(
            gas_weber_number=0.0,
            gas_froude_number=20.0,
            vapor_density_kg_m3=20.0,
            liquid_density_kg_m3=1000.0,
            heat_flux_ratio_q_qcrit=1.0,
        )
    with pytest.raises(ValueError, match="heat_flux_ratio_q_qcrit"):
        wojtan_th3337_candidate_dryout_boundaries(
            gas_weber_number=200.0,
            gas_froude_number=20.0,
            vapor_density_kg_m3=20.0,
            liquid_density_kg_m3=1000.0,
            heat_flux_ratio_q_qcrit=float("nan"),
        )


def test_wojtan_th2978_rendered_dryout_limits_are_not_runtime_release() -> None:
    result = wojtan_th2978_candidate_dryout_limits(
        gas_weber_number=200.0,
        gas_froude_number=20.0,
        vapor_density_kg_m3=20.0,
        liquid_density_kg_m3=1000.0,
        heat_flux_ratio_q_qcrit=1.0,
    )

    assert isinstance(result, WojtanTh2978CandidateDryoutLimitResult)
    assert result.source_status == "candidate_only_not_runtime_released"
    assert result.dryout_inception_quality == pytest.approx(0.5047352096)
    assert result.dryout_completion_quality == pytest.approx(0.9791233757)
    assert result.dryout_inception_quality == pytest.approx(
        wojtan_th2978_candidate_dryout_inception_quality(
            gas_weber_number=200.0,
            gas_froude_number=20.0,
            vapor_density_kg_m3=20.0,
            liquid_density_kg_m3=1000.0,
            heat_flux_ratio_q_qcrit=1.0,
        )
    )
    assert result.dryout_completion_quality == pytest.approx(
        wojtan_th2978_candidate_dryout_completion_quality(
            gas_weber_number=200.0,
            gas_froude_number=20.0,
            vapor_density_kg_m3=20.0,
            liquid_density_kg_m3=1000.0,
            heat_flux_ratio_q_qcrit=1.0,
        )
    )


def test_dryout_diagnostic_does_not_replace_solver_convergence_failure(
    co2_model: CO2MathcadModel,
) -> None:
    result = co2_model.run(2.5, 130.0, 200.0, 0.0)

    assert result["converged"] is False
    assert result["solver_status"] == "no_root_bracket"
    assert result["failure_class"] == "numerical_failure"
    assert result["numerical_failure"] == "no_root_bracket"
    assert result["dryout_limit"] == "not_evaluated_source_required"
    assert result["boiling_heat_transfer_status"] == "not_evaluated_solver_not_converged"


def test_near_critical_warning_is_classified_as_property_limit() -> None:
    diagnostics = diagnostics_for_solver_status(
        heat_transfer_model="prescribed_heat_input",
        solver_status="converged",
        near_critical_warning="Temperature is 1 K below the CO2 critical temperature.",
    )

    result_fields = diagnostics.to_result_fields()
    assert result_fields["failure_class"] == "property_limit"
    assert result_fields["property_limit"] == "near_critical_warning"
    assert any("critical temperature" in warning for warning in result_fields["warnings"])
