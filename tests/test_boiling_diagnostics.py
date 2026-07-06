from __future__ import annotations

import pytest

from boiling_heat_transfer import (
    CHEN_1962_SOURCE_CANDIDATE,
    WallSoilBoundary,
    chen_1962_source_candidate,
    diagnostics_for_solver_status,
    normalize_heat_transfer_model,
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
    assert result["model_source_status"] == "mixed"


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
