from __future__ import annotations

import pytest

from get_co2_model import CO2MathcadModel
from two_phase_closures import closure_model_scientific_status, normalize_closure_model


BASELINE_MODE_CASES = [
    {
        "name": "worksheet_compatible",
        "mode": "worksheet_compatible",
        "closure_model": "worksheet_compatible",
        "strings": {
            "model_mode": "worksheet_compatible",
            "closure_name": "worksheet_compatible+darcy_friction_factor+martinelli+chisholm",
            "model_scientific_status": "mathcad_compatible",
            "property_model_name": "CO2SaturationProperties",
            "outlet_selected_void_fraction_model": "worksheet_compatible",
            "outlet_selected_friction_model": "lockhart_martinelli_chisholm",
            "evaporator_dominant_flow_regime": "intermittent",
            "riser_dominant_flow_regime": "",
        },
        "integers": {
            "n_control_volumes": 1200,
            "n_riser_points": 0,
        },
        "numbers": {
            "fff": 0.30481416770603487,
            "Hy_m": 2.5001239044714176,
            "deltaP_Pa": 16030.971402448256,
            "phiG_formula": 0.786884389628336,
            "outlet_slip_ratio": 8.497850527857805,
            "chiG1_mass": 0.7663926593915501,
            "GG_out_kg_s": 0.06525816267021696,
            "GL_out_kg_s": 0.019891612540347214,
        },
    },
    {
        "name": "distributed_steady",
        "mode": "distributed_steady",
        "closure_model": "worksheet_compatible",
        "strings": {
            "model_mode": "distributed_steady",
            "closure_name": "worksheet_compatible+darcy_friction_factor+martinelli+chisholm",
            "model_scientific_status": "mathcad_compatible",
            "property_model_name": "CO2SaturationProperties",
            "outlet_selected_void_fraction_model": "worksheet_compatible",
            "outlet_selected_friction_model": "lockhart_martinelli_chisholm",
            "evaporator_dominant_flow_regime": "intermittent",
            "riser_dominant_flow_regime": "annular",
        },
        "integers": {
            "n_control_volumes": 400,
            "n_riser_points": 120,
        },
        "numbers": {
            "fff": 0.11018535025633225,
            "Hy_m": 2.5002064862874662,
            "deltaP_Pa": 17444.84960847512,
            "phiG_formula": 0.8565320826921419,
            "outlet_slip_ratio": 14.60462767095319,
            "chiG1_mass": 0.9007504915905336,
            "GG_out_kg_s": 0.0650225893279156,
            "GL_out_kg_s": 0.007164536779670036,
        },
    },
    {
        "name": "homogeneous_equilibrium",
        "mode": "distributed_steady",
        "closure_model": "homogeneous_equilibrium",
        "strings": {
            "model_mode": "distributed_steady",
            "closure_name": "homogeneous_equilibrium+darcy_friction_factor+martinelli+chisholm",
            "model_scientific_status": "published",
            "property_model_name": "CO2SaturationProperties",
            "outlet_selected_void_fraction_model": "homogeneous_equilibrium",
            "outlet_selected_friction_model": "lockhart_martinelli_chisholm",
            "evaporator_dominant_flow_regime": "annular",
            "riser_dominant_flow_regime": "annular_mist",
        },
        "integers": {
            "n_control_volumes": 400,
            "n_riser_points": 120,
        },
        "numbers": {
            "fff": 0.3309227012014245,
            "Hy_m": 2.5002370448478053,
            "deltaP_Pa": 19690.70390223789,
            "phiG_formula": 0.9667525533311069,
            "outlet_slip_ratio": 1.0,
            "chiG1_mass": 0.7513584365923728,
            "GG_out_kg_s": 0.06497301645321994,
            "GL_out_kg_s": 0.021501046109904137,
        },
    },
    {
        "name": "zivi",
        "mode": "distributed_steady",
        "closure_model": "zivi",
        "strings": {
            "model_mode": "distributed_steady",
            "closure_name": "zivi+darcy_friction_factor+martinelli+chisholm",
            "model_scientific_status": "published",
            "property_model_name": "CO2SaturationProperties",
            "outlet_selected_void_fraction_model": "zivi",
            "outlet_selected_friction_model": "lockhart_martinelli_chisholm",
            "evaporator_dominant_flow_regime": "annular",
            "riser_dominant_flow_regime": "annular",
        },
        "integers": {
            "n_control_volumes": 400,
            "n_riser_points": 120,
        },
        "numbers": {
            "fff": 0.2793138114349253,
            "Hy_m": 2.5002353527703285,
            "deltaP_Pa": 19182.601465537555,
            "phiG_formula": 0.9418369731937626,
            "outlet_slip_ratio": 2.126721265256866,
            "chiG1_mass": 0.7816690409043294,
            "GG_out_kg_s": 0.06498450237677074,
            "GL_out_kg_s": 0.018151069043057785,
        },
    },
    {
        "name": "regime_aware",
        "mode": "distributed_steady",
        "closure_model": "regime_aware",
        "strings": {
            "model_mode": "distributed_steady",
            "closure_name": (
                "experimental_regime_aware(alias:regime_aware)"
                "+regime_selected_void_fraction+regime_selected_friction"
            ),
            "model_scientific_status": "experimental",
            "property_model_name": "CO2SaturationProperties",
            "outlet_selected_void_fraction_model": "zivi",
            "outlet_selected_friction_model": "separated_shear",
            "evaporator_dominant_flow_regime": "intermittent",
            "riser_dominant_flow_regime": "churn",
        },
        "integers": {
            "n_control_volumes": 400,
            "n_riser_points": 120,
        },
        "numbers": {
            "fff": 1.6173249125137548,
            "Hy_m": 2.500539957645635,
            "deltaP_Pa": 14989.217987579203,
            "phiG_formula": 0.7361831809587851,
            "outlet_slip_ratio": 2.1244198170836435,
            "chiG1_mass": 0.3820694921058047,
            "GG_out_kg_s": 0.06479198876991078,
            "GL_out_kg_s": 0.10478969756888813,
        },
    },
]


def test_regime_aware_is_alias_for_experimental_regime_aware() -> None:
    assert normalize_closure_model("regime_aware") == "experimental_regime_aware"
    assert normalize_closure_model("experimental_regime_aware") == "experimental_regime_aware"
    assert closure_model_scientific_status("regime_aware") == "experimental"
    assert closure_model_scientific_status("experimental_regime_aware") == "experimental"


def test_experimental_regime_aware_preserves_legacy_regime_aware_numerics() -> None:
    model = CO2MathcadModel()

    legacy = model.run(
        2.5,
        76.68,
        200.0,
        0.0,
        mode="distributed_steady",
        closure_model="regime_aware",
    )
    explicit = model.run(
        2.5,
        76.68,
        200.0,
        0.0,
        mode="distributed_steady",
        closure_model="experimental_regime_aware",
    )

    assert legacy["converged"] is True
    assert explicit["converged"] is True
    assert legacy["model_scientific_status"] == "experimental"
    assert explicit["model_scientific_status"] == "experimental"
    assert "alias:regime_aware" in str(legacy["closure_name"])
    assert "experimental_regime_aware" in str(explicit["closure_name"])

    for key in (
        "fff",
        "Hy_m",
        "deltaP_Pa",
        "phiG_formula",
        "outlet_slip_ratio",
    ):
        assert explicit[key] == pytest.approx(legacy[key], rel=0.0, abs=0.0)


def test_closure_scientific_status_is_exposed_for_baseline_modes() -> None:
    model = CO2MathcadModel()

    worksheet = model.run(2.5, 76.68, 200.0, 0.0, closure_model="worksheet_compatible")
    homogeneous = model.run(
        2.5,
        76.68,
        200.0,
        0.0,
        mode="distributed_steady",
        closure_model="homogeneous_equilibrium",
    )
    zivi = model.run(
        2.5,
        76.68,
        200.0,
        0.0,
        mode="distributed_steady",
        closure_model="zivi",
    )

    assert worksheet["model_scientific_status"] == "mathcad_compatible"
    assert homogeneous["model_scientific_status"] == "published"
    assert zivi["model_scientific_status"] == "published"


@pytest.mark.parametrize("case", BASELINE_MODE_CASES, ids=[case["name"] for case in BASELINE_MODE_CASES])
def test_current_mode_baselines_are_fixed(case, co2_model: CO2MathcadModel) -> None:
    result = co2_model.run(
        2.5,
        76.68,
        200.0,
        0.0,
        mode=case["mode"],
        closure_model=case["closure_model"],
    )

    assert result["converged"] is True

    for key, expected_value in case["strings"].items():
        assert result[key] == expected_value
    for key, expected_value in case["integers"].items():
        assert result[key] == expected_value
    for key, expected_value in case["numbers"].items():
        assert result[key] == pytest.approx(expected_value, rel=1e-9)
