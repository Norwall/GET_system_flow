from __future__ import annotations

import pytest

from get_co2_model import CO2MathcadModel


def test_cached_checks_match_expected_baseline(co2_model: CO2MathcadModel) -> None:
    checks = co2_model.cached_checks()

    assert checks["actual"]["px_m10_Pa"] == pytest.approx(checks["expected"]["px_m10_Pa"], rel=0.0, abs=0.0)
    assert checks["actual"]["rx_m10_J_kg"] == pytest.approx(checks["expected"]["rx_m10_J_kg"], rel=0.0, abs=0.0)
    assert checks["actual"]["RV1_default"] == pytest.approx(checks["expected"]["RV1_default"], rel=1e-12)
    assert checks["actual"]["R2x"] == pytest.approx(checks["expected"]["R2x"], rel=0.0, abs=0.0)
