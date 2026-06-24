from __future__ import annotations

from typing import cast

import pytest

from get_co2_model import CO2MathcadModel


Q_VALUES = [2.48, 5, 10, 20, 30, 40, 50, 60, 71.18, 76.68, 90, 100, 110, 120, 130]


@pytest.mark.slow
def test_heat_load_sweep_convergence_map_matches_baseline(co2_model: CO2MathcadModel) -> None:
    expected_converged = {q: True for q in Q_VALUES[:-1]}
    expected_converged[130] = False

    actual_converged = {}
    for q in Q_VALUES:
        result = co2_model.run(2.5, float(q), 200.0, 0.0)
        actual_converged[q] = cast(bool, result["converged"])

    assert actual_converged == expected_converged


@pytest.mark.slow
def test_heat_load_sweep_preserves_expected_trends(co2_model: CO2MathcadModel) -> None:
    circulation_factors = []
    true_gas_fractions = []
    for q in Q_VALUES[:-1]:
        result = co2_model.run(2.5, float(q), 200.0, 0.0)
        assert result["converged"] is True
        assert result["Hy_m"] == pytest.approx(2.5, abs=5e-4)
        circulation_factors.append(cast(float, result["fff"]))
        true_gas_fractions.append(cast(float, result["phiG1_true"]))

    assert circulation_factors == pytest.approx(sorted(circulation_factors, reverse=True), rel=0.0, abs=0.0)
    assert true_gas_fractions == pytest.approx(sorted(true_gas_fractions), rel=0.0, abs=0.0)
