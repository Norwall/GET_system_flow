from __future__ import annotations

import pytest

from critical_loads import (
    QCRIT_SOURCE_F_ZERO,
    CriticalLoadConfig,
    CriticalLoadPoint,
    find_critical_loads,
)
from boiling_heat_transfer import WallSoilBoundary
from get_co2_model import CO2MathcadModel


def _point(qtr: float, status: str, **kwargs) -> CriticalLoadPoint:
    return CriticalLoadPoint(qtr_w_m=float(qtr), status=status, solver_status=status, **kwargs)


def test_fake_scan_finds_lower_upper_and_f_zero_boundaries() -> None:
    def evaluate(qtr: float) -> CriticalLoadPoint:
        if qtr == 0.0:
            return _point(qtr, "no_boiling", failure_class="hydrodynamic_limit")
        if qtr < 2.0:
            return _point(qtr, "no_root", failure_class="numerical_failure")
        if qtr <= 10.0:
            return _point(qtr, "working", circulation_factor=1.0)
        return _point(qtr, "no_root", failure_class="numerical_failure")

    config = CriticalLoadConfig(
        H=1.0,
        Li=10.0,
        tcon=0.0,
        qtr_min_w_m=0.0,
        qtr_max_w_m=12.0,
        qtr_step_w_m=2.0,
        boundary_tolerance_w_m=0.01,
    )
    report = find_critical_loads(
        evaluate=evaluate,
        f_zero_residual=lambda qtr: qtr - 9.0,
        config=config,
    )

    assert report.qcrit_status == "evaluated"
    assert report.lower_critical_load_w_m == pytest.approx(2.0, abs=0.02)
    assert report.upper_scan_load.qtr_w_m == pytest.approx(10.0, abs=0.02)
    assert report.upper_f_zero_load.qtr_w_m == pytest.approx(9.0, abs=0.02)
    assert report.upper_critical_load_w_m == report.upper_f_zero_load.qtr_w_m
    assert report.upper_f_zero_load.point is not None
    assert report.upper_f_zero_load.point.status == "f_to_zero_limit"
    assert report.upper_f_zero_load.point.source_formula_id == QCRIT_SOURCE_F_ZERO
    assert report.scan_points[0].status == "no_boiling"


def test_fake_scan_reports_multiple_roots_without_choosing_branch() -> None:
    config = CriticalLoadConfig(
        H=1.0,
        Li=10.0,
        tcon=0.0,
        qtr_min_w_m=1.0,
        qtr_max_w_m=3.0,
        qtr_step_w_m=1.0,
    )
    report = find_critical_loads(
        evaluate=lambda qtr: _point(qtr, "multiple_roots", n_sign_changes=2),
        f_zero_residual=lambda qtr: None,
        config=config,
    )

    assert report.qcrit_status == "failed"
    assert report.lower_critical_load.status == "no_working_solution"
    assert {point.status for point in report.scan_points} == {"multiple_roots"}


@pytest.mark.parametrize("status", ["near_critical_region", "property_out_of_range"])
def test_fake_scan_keeps_property_limits_separate(status: str) -> None:
    config = CriticalLoadConfig(
        H=1.0,
        Li=10.0,
        tcon=0.0,
        qtr_min_w_m=1.0,
        qtr_max_w_m=2.0,
        qtr_step_w_m=1.0,
    )
    report = find_critical_loads(
        evaluate=lambda qtr: _point(qtr, status, failure_class="property_limit"),
        f_zero_residual=lambda qtr: None,
        config=config,
    )

    assert report.qcrit_status == "failed"
    assert all(point.failure_class == "property_limit" for point in report.scan_points)
    assert {point.status for point in report.scan_points} == {status}


def test_co2_mathcad_qcrit_smoke_uses_f_zero_limit_not_old_heatmap_name() -> None:
    model = CO2MathcadModel()
    steady = model.run(2.5, 76.68, 200.0, 0.0)
    report = model.critical_loads(
        H=2.5,
        Li=200.0,
        tcon=0.0,
        qtr_min_w_m=0.0,
        qtr_max_w_m=160.0,
        qtr_step_w_m=40.0,
        boundary_tolerance_w_m=5.0,
        nsamp=80,
        ngrid=80,
    )

    assert steady["qcrit_status"] == "not_evaluated"
    assert report.qcrit_status == "evaluated"
    assert report.lower_critical_load_w_m is not None
    assert report.lower_critical_load_w_m < 10.0
    assert report.upper_f_zero_load.qtr_w_m is not None
    assert 110.0 < report.upper_f_zero_load.qtr_w_m < 130.0
    assert report.upper_f_zero_load.point is not None
    assert report.upper_f_zero_load.point.circulation_factor == pytest.approx(0.0)
    assert report.to_dict()["qcrit_model"] == "dissertation_scan_plus_f_zero"


def test_wall_coupled_qcrit_rejects_prescribed_qtr_sweep() -> None:
    model = CO2MathcadModel()

    report = model.critical_loads(
        H=2.5,
        Li=200.0,
        tcon=0.0,
        heat_transfer_model="wall_coupled",
        wall_soil_boundary=WallSoilBoundary(
            far_field_temperature_c=5.0,
            effective_conductance_w_m_k=10.0,
        ),
        qtr_min_w_m=0.0,
        qtr_max_w_m=10.0,
        qtr_step_w_m=5.0,
        nsamp=20,
        ngrid=20,
    )

    assert report.qcrit_status == "failed"
    assert any(point.status == "validation_error" for point in report.scan_points)
    assert any("prescribed-qtr sweep" in (point.failure_reason or "") for point in report.scan_points)
