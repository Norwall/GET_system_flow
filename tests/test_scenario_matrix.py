from __future__ import annotations

import pytest

from refrigerant_properties import BackendUnavailableError
from scenario_matrix import (
    SCENARIO_FAILURE_CLASSES,
    SCENARIO_STATUSES,
    ScenarioCase,
    default_scenario_cases,
    run_scenario_case,
    run_scenario_matrix,
)


def _cases_by_id() -> dict[str, ScenarioCase]:
    return {case.case_id: case for case in default_scenario_cases(include_backend_probe=True)}


def test_default_scenario_cases_cover_checkpoint_categories() -> None:
    cases = default_scenario_cases(include_backend_probe=True)
    tags = {tag for case in cases for tag in case.tags}

    assert {
        "co2_temperature_grid",
        "nh3_temperature_grid",
        "qtr_sweep",
        "height_sweep",
        "length_sweep",
        "diameter_sweep",
        "roughness_sweep",
        "horizontal_without_riser",
        "no_driving_head",
        "high_riser",
        "near_critical",
        "invalid_input",
        "backend_unavailable",
    } <= tags
    assert sum("co2_temperature_grid" in case.tags for case in cases) == 5
    assert sum("nh3_temperature_grid" in case.tags for case in cases) == 5


@pytest.mark.parametrize(
    "case_id",
    [
        "co2_tcon_minus20",
        "co2_tcon_minus10",
        "co2_tcon_0",
        "co2_tcon_10",
        "co2_tcon_20",
        "nh3_tcon_minus20",
        "nh3_tcon_minus10",
        "nh3_tcon_0",
        "nh3_tcon_10",
        "nh3_tcon_20",
    ],
)
def test_temperature_grid_cases_are_working_root_scan_points(case_id: str) -> None:
    outcome = run_scenario_case(_cases_by_id()[case_id], root_nsamp=24)

    assert outcome.status == "working"
    assert outcome.converged is True
    assert outcome.solver_status == "converged"
    assert outcome.failure_class == "none"
    assert outcome.circulation_factor is not None
    assert outcome.qcrit_status == "not_evaluated"


@pytest.mark.parametrize(
    "case_id",
    ["co2_qtr_high_no_root", "co2_li_long_no_root", "co2_diameter_small_no_root"],
)
def test_high_resistance_or_high_load_cases_report_no_root(case_id: str) -> None:
    outcome = run_scenario_case(_cases_by_id()[case_id], root_nsamp=24)

    assert outcome.status == "no_root"
    assert outcome.converged is False
    assert outcome.solver_status == "no_root_bracket"
    assert outcome.failure_class == "numerical_failure"
    assert outcome.circulation_factor is None


def test_no_riser_and_invalid_inputs_return_structured_statuses_without_root_scan() -> None:
    cases = _cases_by_id()

    no_riser = run_scenario_case(cases["co2_horizontal_no_riser"], root_nsamp=24)
    zero_qtr = run_scenario_case(cases["co2_invalid_zero_qtr"], root_nsamp=24)
    negative_h = run_scenario_case(cases["co2_invalid_negative_H"], root_nsamp=24)
    zero_li = run_scenario_case(cases["co2_invalid_zero_Li"], root_nsamp=24)

    assert no_riser.status == "no_driving_head"
    assert no_riser.failure_class == "hydrodynamic_limit"
    assert zero_qtr.status == "validation_error"
    assert negative_h.status == "validation_error"
    assert zero_li.status == "validation_error"
    assert {zero_qtr.failure_class, negative_h.failure_class, zero_li.failure_class} == {"validation_error"}


def test_near_critical_case_is_property_limit_without_root_scan() -> None:
    outcome = run_scenario_case(_cases_by_id()["co2_near_critical"], root_nsamp=24)

    assert outcome.status == "near_critical_region"
    assert outcome.solver_status == "near_critical_region"
    assert outcome.failure_class == "property_limit"
    assert outcome.circulation_factor is None
    assert any("critical temperature" in warning for warning in outcome.warnings)


def test_backend_unavailable_is_structured_property_limit() -> None:
    def unavailable_factory(**kwargs):
        _ = kwargs
        raise BackendUnavailableError("REFPROP backend is not available in this test.")

    outcome = run_scenario_case(
        _cases_by_id()["co2_refprop_backend_probe"],
        root_nsamp=24,
        model_factory=unavailable_factory,
    )

    assert outcome.status == "backend_unavailable"
    assert outcome.solver_status == "backend_unavailable"
    assert outcome.failure_class == "property_limit"
    assert "REFPROP" in str(outcome.failure_reason)


def test_scenario_matrix_report_counts_statuses_and_keeps_fixed_enums() -> None:
    cases = _cases_by_id()
    report = run_scenario_matrix(
        [
            cases["co2_qtr_low"],
            cases["co2_qtr_high_no_root"],
            cases["co2_horizontal_no_riser"],
            cases["co2_invalid_zero_qtr"],
        ],
        root_nsamp=24,
    )

    assert report.status_counts == {
        "working": 1,
        "no_root": 1,
        "no_driving_head": 1,
        "validation_error": 1,
    }
    assert report.failure_class_counts == {
        "none": 1,
        "numerical_failure": 1,
        "hydrodynamic_limit": 1,
        "validation_error": 1,
    }
    assert set(report.status_counts) <= set(SCENARIO_STATUSES)
    assert set(report.failure_class_counts) <= set(SCENARIO_FAILURE_CLASSES)
    assert "qtr_sweep" in report.coverage_tags
    assert report.to_dict()["n_cases"] == 4
