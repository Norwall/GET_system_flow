from __future__ import annotations

import pandas as pd

import co2_function_matrix
from co2_function_matrix import MATRIX_COLUMNS, MatrixConfig, build_summary, run_analysis


def _fake_case_result(case) -> dict[str, object]:
    converged = not (case.closure_model == "worksheet_compatible" and case.qtr_W_m > 10.0)
    near_limit = bool(converged and case.closure_model == "regime_aware" and case.qtr_W_m >= 20.0)
    row = {
        "closure_model": case.closure_model,
        "mode": case.mode,
        "H_m": case.H_m,
        "Li_m": case.Li_m,
        "qtr_W_m": case.qtr_W_m,
        "tcon_C": case.tcon_C,
        "U_W": case.qtr_W_m * case.Li_m,
        "functioning": converged,
        "near_limit": near_limit,
        "converged": converged,
        "solver_status": "converged" if converged else "no_root_bracket",
        "failure_reason": None if converged else "fake failure",
        "fff": 1.0 if converged else None,
        "Hy_m": case.H_m if converged else None,
        "tav_C": 0.0 if converged else None,
        "tmm_C": 0.0 if converged else None,
        "tvih_C": 0.0 if converged else None,
        "chiG1_mass": 0.96 if near_limit else 0.2,
        "phiG1_true": 0.995 if near_limit else 0.5,
        "GL1_lph": 0.5 if near_limit else 100.0,
        "GL0_lph": 150.0 if converged else None,
        "GG0_liq_equiv_lph": 50.0 if converged else None,
        "GG0_gas_lph": 500.0 if converged else None,
        "deltaP_Pa": 1000.0 if converged else None,
        "driving_pressure_pa": 1200.0 if converged else None,
        "effective_density_difference_kg_m3": 100.0 if converged else None,
        "evaporator_dominant_flow_regime": "intermittent" if converged else None,
        "riser_dominant_flow_regime": "bubbly" if converged else None,
        "evaporator_flow_regime_summary": "intermittent:100%" if converged else None,
        "riser_flow_regime_summary": "bubbly:100%" if converged else None,
        "closure_name": case.closure_model,
        "property_model_name": "fake",
        "root_bracket": "(1.0, 2.0)" if converged else None,
        "n_sign_changes": 1 if converged else 0,
        "exception_type": None,
        "exception_message": None,
    }
    return {column: row.get(column) for column in MATRIX_COLUMNS}


def test_default_wide_grid_matches_planned_case_count() -> None:
    config = MatrixConfig()

    assert len(config.li_values_m) == 13
    assert len(config.h_values_m) == 13
    assert len(config.qtr_values_w_m) == 29
    assert config.n_cases == 9802
    assert 2.48 in config.qtr_values_w_m
    assert 71.18 in config.qtr_values_w_m
    assert 76.68 in config.qtr_values_w_m


def test_build_summary_extracts_functioning_boundary() -> None:
    rows = [
        _fake_case_result(case)
        for case in co2_function_matrix.iter_cases(
            MatrixConfig(
                li_values_m=(100.0,),
                h_values_m=(1.0,),
                qtr_values_w_m=(10.0, 20.0),
                closure_models=("worksheet_compatible", "regime_aware"),
            )
        )
    ]

    summary = build_summary(pd.DataFrame(rows))
    worksheet = summary[summary["closure_model"] == "worksheet_compatible"].iloc[0]
    regime = summary[summary["closure_model"] == "regime_aware"].iloc[0]

    assert worksheet["qtr_max_working_W_m"] == 10.0
    assert worksheet["qtr_first_failure_W_m"] == 20.0
    assert worksheet["n_failed"] == 1
    assert regime["qtr_max_working_W_m"] == 20.0
    assert regime["qtr_min_near_limit_W_m"] == 20.0


def test_run_analysis_writes_matrix_summary_plots_and_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(co2_function_matrix, "compute_case", _fake_case_result)
    config = MatrixConfig(
        li_values_m=(100.0, 200.0),
        h_values_m=(1.0,),
        qtr_values_w_m=(10.0, 20.0),
        closure_models=("worksheet_compatible", "regime_aware"),
    )

    outputs = run_analysis(
        config=config,
        outdir=tmp_path,
        workers=1,
        resume=False,
        make_plots=True,
    )

    matrix = pd.read_csv(outputs["matrix"])
    summary = pd.read_csv(outputs["summary"])

    assert len(matrix) == config.n_cases
    assert len(summary) == 4
    assert outputs["report"].exists()
    assert "qcrit_heatmap_worksheet_compatible" in outputs
    assert outputs["qcrit_heatmap_worksheet_compatible"].exists()
    assert outputs["qcrit_difference"].exists()
    assert (tmp_path / "co2_function_matrix_qcrit_worksheet_compatible.csv").exists()
    assert "Матрица функционирования CO2-системы" in outputs["report"].read_text(encoding="utf-8")
