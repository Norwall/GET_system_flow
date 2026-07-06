from __future__ import annotations

import pytest

from get_co2_model import CO2MathcadModel


def test_mathcad_preboiling_onset_is_default(co2_model: CO2MathcadModel) -> None:
    result = co2_model.run(2.5, 76.68, 200.0, 0.0)

    assert result["converged"] is True
    assert result["boiling_onset_model"] == "mathcad_baseline"
    assert result["onset_superheat_k"] == pytest.approx(0.0)
    assert result["onset_condenser_pressure_drop_pa"] == pytest.approx(0.0)
    assert result["preboiling_status"] == "valid"
    assert result["raw_preboiling_length_fraction"] == pytest.approx(result["yn"])
    assert "CO2.xmcd" in result["boiling_onset_source"]


def test_ishkov_superheat_onset_is_opt_in_and_reports_iterated_condenser_drop(
    co2_model: CO2MathcadModel,
) -> None:
    baseline = co2_model.run(2.5, 76.68, 200.0, 0.0)
    opt_in = co2_model.run(
        2.5,
        76.68,
        200.0,
        0.0,
        boiling_onset_model="ishkov_superheat",
        onset_superheat_k=1.0,
    )

    assert baseline["converged"] is True
    assert opt_in["converged"] is True
    assert opt_in["boiling_onset_model"] == "ishkov_superheat"
    assert opt_in["onset_superheat_k"] == pytest.approx(1.0)
    assert opt_in["onset_condenser_pressure_drop_pa"] > 0.0
    assert opt_in["preboiling_status"] == "valid"
    assert "Ishkov dissertation eq. (3.3)" in opt_in["boiling_onset_source"]
    assert opt_in["raw_preboiling_length_fraction"] != pytest.approx(
        baseline["raw_preboiling_length_fraction"],
        rel=1e-4,
    )


def test_negative_onset_superheat_is_validation_error(co2_model: CO2MathcadModel) -> None:
    result = co2_model.run(
        2.5,
        76.68,
        200.0,
        0.0,
        boiling_onset_model="ishkov_superheat",
        onset_superheat_k=-0.01,
    )

    assert result["converged"] is False
    assert result["solver_status"] == "validation_error"
    assert "onset_superheat_k" in result["failure_reason"]
    assert result["boiling_onset_model"] == "ishkov_superheat"
