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
            "riser_dominant_flow_regime": "churn",
        },
        "integers": {
            "n_control_volumes": 400,
            "n_riser_points": 120,
        },
        "numbers": {
            "fff": 0.30170998571277113,
            "Hy_m": 2.500285191193341,
            "deltaP_Pa": 16043.143454892173,
            "phiG_formula": 0.7877491017385333,
            "outlet_slip_ratio": 8.591520522671694,
            "chiG1_mass": 0.7682202725459117,
            "GG_out_kg_s": 0.06497951058368544,
            "GL_out_kg_s": 0.0196049672098266,
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
            "fff": 0.481749461899962,
            "Hy_m": 2.500262263834316,
            "deltaP_Pa": 19394.934108957692,
            "phiG_formula": 0.9523658792045884,
            "outlet_slip_ratio": 1.0,
            "chiG1_mass": 0.6748779235038543,
            "GG_out_kg_s": 0.06493977822988263,
            "GL_out_kg_s": 0.03128470321814883,
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
            "fff": 0.43738100768191307,
            "Hy_m": 2.5002675759218236,
            "deltaP_Pa": 18568.899367983526,
            "phiG_formula": 0.911880087016484,
            "outlet_slip_ratio": 2.1274619264815424,
            "chiG1_mass": 0.6957097628642775,
            "GG_out_kg_s": 0.0649495067145274,
            "GL_out_kg_s": 0.028407680695243173,
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
            "fff": 3.450422932790453,
            "Hy_m": 2.4965784747149824,
            "deltaP_Pa": 11514.820108598056,
            "phiG_formula": 0.5669668560673378,
            "outlet_slip_ratio": 2.1254673231014776,
            "chiG1_mass": 0.2246977456079644,
            "GG_out_kg_s": 0.06446642292750566,
            "GL_out_kg_s": 0.2224364240640338,
        },
    },
]


def test_regime_aware_is_alias_for_experimental_regime_aware() -> None:
    assert normalize_closure_model("regime_aware") == "experimental_regime_aware"
    assert normalize_closure_model("experimental_regime_aware") == "experimental_regime_aware"
    assert closure_model_scientific_status("regime_aware") == "experimental"
    assert closure_model_scientific_status("experimental_regime_aware") == "experimental"


@pytest.mark.slow
@pytest.mark.distributed
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
    assert legacy["model_source_status"] == "experimental_no_primary_source"
    assert explicit["model_source_status"] == "experimental_no_primary_source"
    assert any("closure_model=experimental_regime_aware" in reason for reason in explicit["source_gate_reasons"])
    assert any("regime_model=experimental_regime_aware" in reason for reason in explicit["source_gate_reasons"])
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


@pytest.mark.slow
@pytest.mark.distributed
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
@pytest.mark.slow
@pytest.mark.distributed
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
