from __future__ import annotations

import pytest

from experimental_regimes import (
    classify_horizontal_evaporator_regime_result,
    classify_vertical_riser_regime_result,
)
from get_co2_model import CO2MathcadModel
from published_regimes import (
    classify_horizontal_evaporator_regime_result as classify_published_horizontal_regime_result,
    classify_vertical_riser_regime_result as classify_published_vertical_regime_result,
)
from two_phase_regimes import (
    classify_horizontal_evaporator_regime,
    classify_vertical_riser_regime,
    summarize_regime_fractions,
)


def test_experimental_horizontal_classifier_preserves_legacy_name_with_metadata() -> None:
    classification = classify_horizontal_evaporator_regime_result(
        mass_quality=0.3,
        gas_volume_fraction=0.5,
        gas_superficial_velocity_m_s=1.0,
        liquid_superficial_velocity_m_s=0.1,
        slip_ratio=2.0,
    )

    assert classification.name == "intermittent"
    assert classify_horizontal_evaporator_regime(0.3, 0.5, 1.0, 0.1, 2.0) == classification.name
    assert classification.status == "experimental"
    assert "no primary source" in classification.source
    assert classification.transition_criteria != ""
    assert classification.confidence == "heuristic"


def test_experimental_vertical_classifier_preserves_legacy_name_with_metadata() -> None:
    classification = classify_vertical_riser_regime_result(
        gas_volume_fraction=0.55,
        gas_superficial_velocity_m_s=2.0,
    )

    assert classification.name == "churn"
    assert classify_vertical_riser_regime(0.55, 2.0) == classification.name
    assert classification.status == "experimental"
    assert classification.transition_criteria == "0.45 <= alpha < 0.80"


def test_published_regime_placeholders_do_not_claim_physical_classification() -> None:
    horizontal = classify_published_horizontal_regime_result(
        mass_quality=0.3,
        gas_volume_fraction=0.5,
        gas_superficial_velocity_m_s=1.0,
        liquid_superficial_velocity_m_s=0.1,
        slip_ratio=2.0,
    )
    vertical = classify_published_vertical_regime_result(
        gas_volume_fraction=0.55,
        gas_superficial_velocity_m_s=2.0,
    )

    assert horizontal.name == "unknown_or_out_of_range"
    assert vertical.name == "unknown_or_out_of_range"
    assert horizontal.status == "not_implemented"
    assert vertical.status == "not_implemented"
    assert "not implemented" in horizontal.transition_criteria
    assert "not implemented" in vertical.transition_criteria


def test_regime_summary_fractions_sum_to_one() -> None:
    summary = summarize_regime_fractions(
        regimes=["bubbly", "bubbly", "annular"],
        segment_lengths_m=[1.0, 2.0, 3.0],
    )

    assert sum(summary.values()) == pytest.approx(1.0)
    assert summary["bubbly"] == pytest.approx(0.5)
    assert summary["annular"] == pytest.approx(0.5)


def test_solver_profiles_expose_regime_metadata(co2_model: CO2MathcadModel) -> None:
    result = co2_model.run_result(2.5, 76.68, 200.0, 0.0)
    result_dict = result.to_dict()
    profile = result.pass_result.evaporator_profile if result.pass_result is not None else None

    assert profile is not None
    assert len(profile.flow_regime_source) == profile.n_points
    assert len(profile.flow_regime_status) == profile.n_points
    assert len(profile.flow_regime_transition_criteria) == profile.n_points
    assert len(profile.flow_regime_confidence) == profile.n_points
    assert "experimental" in result_dict["evaporator_flow_regime_status_summary"]
    assert "no primary source" in result_dict["evaporator_flow_regime_source_summary"]
