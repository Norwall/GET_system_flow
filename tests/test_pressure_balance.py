from __future__ import annotations

import numpy as np
import pytest

from get_co2_model import CO2MathcadModel
from pressure_balance import LoopPressureBalance, hydrostatic_pressure_pa
from two_phase_closures import friction_factor_from_model


def test_worksheet_pressure_balance_is_explicit_and_backward_compatible(co2_model: CO2MathcadModel) -> None:
    result = co2_model.run_result(2.5, 76.68, 200.0, 0.0)
    result_dict = result.to_dict()
    pass_result = result.pass_result

    assert result.converged is True
    assert pass_result is not None
    assert isinstance(pass_result.pressure_balance, LoopPressureBalance)
    assert result_dict["deltaP_Pa"] == pytest.approx(16030.971402448256, rel=1e-12)
    assert result_dict["friction_model"] == "mathcad_compat"

    balance = pass_result.pressure_balance
    assert balance.total_resistance_pa == pytest.approx(pass_result.total_pressure_drop_pa)
    assert balance.total_hydrostatic_pa == pytest.approx(-pass_result.driving_pressure_pa)
    assert balance.residual_pa == pytest.approx(balance.total_resistance_pa - pass_result.driving_pressure_pa)
    assert abs(balance.residual_pa) < 2.0

    section_total = sum(section.delta_p_total_pa for section in balance.sections)
    assert section_total == pytest.approx(balance.residual_pa)
    assert len(result_dict["pressure_balance_terms"]) == 4 * len(balance.sections)
    assert result_dict["pressure_balance_total_friction_pa"] > 0.0
    assert result_dict["pressure_balance_total_acceleration_pa"] == pytest.approx(pass_result.acceleration_pressure_drop_pa)


@pytest.mark.slow
@pytest.mark.distributed
def test_distributed_pressure_balance_separates_riser_hydrostatic_from_resistance(
    co2_model: CO2MathcadModel,
) -> None:
    result = co2_model.run_result(2.5, 76.68, 200.0, 0.0, mode="distributed_steady")
    pass_result = result.pass_result

    assert result.converged is True
    assert pass_result is not None
    assert pass_result.pressure_balance is not None

    balance = pass_result.pressure_balance
    sections = {section.section_name: section for section in balance.sections}

    assert balance.total_resistance_pa == pytest.approx(pass_result.total_pressure_drop_pa)
    assert balance.total_hydrostatic_pa == pytest.approx(-pass_result.driving_pressure_pa)
    assert abs(balance.residual_pa) < 5.0
    assert sections["riser"].delta_p_hydrostatic_pa > 0.0
    assert sections["riser"].delta_p_friction_pa > 0.0
    assert sections["downcomer"].delta_p_hydrostatic_pa < 0.0
    assert pass_result.section_states[1].pressure_drop_pa == pytest.approx(sections["riser"].delta_p_friction_pa)


def test_zero_friction_model_zeros_only_friction_terms(co2_model: CO2MathcadModel) -> None:
    pass_dict = co2_model.one_pass(
        2.5,
        76.68,
        200.0,
        0.0,
        1.0,
        friction_model="zero_friction",
    )

    assert pass_dict is not None
    assert pass_dict["friction_model"] == "zero_friction"
    assert pass_dict["pressure_balance_total_friction_pa"] == pytest.approx(0.0)
    assert pass_dict["pressure_balance_total_acceleration_pa"] > 0.0
    assert pass_dict["deltaP_Pa"] == pytest.approx(pass_dict["pressure_balance_total_resistance_pa"])


def test_hydrostatic_sign_and_zero_head_validation(co2_model: CO2MathcadModel) -> None:
    assert hydrostatic_pressure_pa(1000.0, 2.0) > 0.0
    assert hydrostatic_pressure_pa(1000.0, -2.0) < 0.0
    assert hydrostatic_pressure_pa(1000.0, 0.0) == pytest.approx(0.0)

    zero_head = co2_model.run(0.0, 76.68, 200.0, 0.0)
    negative_head = co2_model.run(-1.0, 76.68, 200.0, 0.0)

    assert zero_head["converged"] is False
    assert zero_head["solver_status"] == "no_driving_head"
    assert negative_head["converged"] is False
    assert negative_head["solver_status"] == "validation_error"


def test_friction_model_dispatcher_exposes_published_and_test_models() -> None:
    reynolds = np.asarray([1000.0, 1.0e5], dtype=float)
    relative_roughness = 1e-4 / (2.0 * 1.325e-2)

    laminar = friction_factor_from_model(reynolds, relative_roughness, "laminar_only")
    colebrook = friction_factor_from_model(reynolds, relative_roughness, "colebrook_white")
    churchill = friction_factor_from_model(reynolds, relative_roughness, "churchill_explicit")
    zero = friction_factor_from_model(reynolds, relative_roughness, "zero_friction")
    legacy = friction_factor_from_model(reynolds, relative_roughness, "mathcad_compat")

    np.testing.assert_allclose(laminar, 64.0 / reynolds)
    assert np.all(colebrook > 0.0)
    assert np.all(churchill > 0.0)
    np.testing.assert_allclose(zero, np.zeros_like(reynolds))
    assert not np.allclose(colebrook, legacy)

    with pytest.raises(ValueError, match="Unsupported friction_model"):
        friction_factor_from_model(1.0e5, relative_roughness, "not_a_model")
