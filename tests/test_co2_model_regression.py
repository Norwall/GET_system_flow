from __future__ import annotations

import pytest

from get_co2_model import CO2MathcadModel, DEFAULT_SCENARIOS


EXPECTED_SCENARIOS = {
    "xmcd_default": {
        "fff": 0.30481416770603487,
        "Hy_m": 2.5001239044714176,
        "GG_out_kg_s": 0.06525816267021696,
        "GL_out_kg_s": 0.019891612540347214,
        "phiG1_true": 0.9691134179535452,
        "deltaP_Pa": 16030.971402448258,
        "tav_C": 0.1580324800500546,
    },
    "co2_lower_benchmark_qmin_table4_5": {
        "fff": 67.65620661570541,
        "Hy_m": 2.49984394561584,
        "GG_out_kg_s": 0.002110592637221414,
        "GL_out_kg_s": 0.14279469154543858,
        "phiG1_true": 0.12385367666276557,
        "deltaP_Pa": 5394.179868106589,
        "tav_C": 0.19557872639268295,
    },
    "co2_upper_benchmark_qmax_appG3": {
        "fff": 0.39000431005706565,
        "Hy_m": 2.500117773928945,
        "GG_out_kg_s": 0.06057741286992754,
        "GL_out_kg_s": 0.0236254521113781,
        "phiG1_true": 0.9608193841248607,
        "deltaP_Pa": 15655.588558515346,
        "tav_C": 0.16005043443600156,
    },
    "moderate_regime_q20": {
        "fff": 4.684446237930689,
        "Hy_m": 2.50023127317006,
        "GG_out_kg_s": 0.017020908364688826,
        "GL_out_kg_s": 0.07973353015512956,
        "phiG1_true": 0.671231254281046,
        "deltaP_Pa": 11327.708186053384,
        "tav_C": 0.18242479529319267,
    },
    "hot_regime_q90": {
        "fff": 0.15508021116246737,
        "Hy_m": 2.4999760303587193,
        "GG_out_kg_s": 0.0765940876410997,
        "GL_out_kg_s": 0.011878227285178275,
        "phiG1_true": 0.9840437480317724,
        "deltaP_Pa": 16958.575170003856,
        "tav_C": 0.1530211478858504,
    },
}


@pytest.mark.parametrize("scenario", DEFAULT_SCENARIOS, ids=lambda scenario: scenario.name)
def test_default_scenarios_match_current_baseline(scenario, co2_model: CO2MathcadModel) -> None:
    result = co2_model.run(scenario.H, scenario.qtr, scenario.Li, scenario.tcon)
    expected = EXPECTED_SCENARIOS[scenario.name]

    assert result["converged"] is True
    assert result["fff"] == pytest.approx(expected["fff"], rel=1e-9)
    assert result["Hy_m"] == pytest.approx(expected["Hy_m"], rel=1e-9)
    assert result["GG_out_kg_s"] == pytest.approx(expected["GG_out_kg_s"], rel=1e-9)
    assert result["GL_out_kg_s"] == pytest.approx(expected["GL_out_kg_s"], rel=1e-9)
    assert result["phiG1_true"] == pytest.approx(expected["phiG1_true"], rel=1e-9)
    assert result["deltaP_Pa"] == pytest.approx(expected["deltaP_Pa"], rel=1e-9)
    assert result["tav_C"] == pytest.approx(expected["tav_C"], rel=1e-9)
