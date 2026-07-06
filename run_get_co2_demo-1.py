from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from co2_visualization import (
    plot_closure_comparison,
    plot_evaporator_profile,
    plot_flow_regime_map,
    plot_riser_profile,
    plot_sweep_overview,
)
from get_co2_model import CO2MathcadModel, DEFAULT_SCENARIOS


OUTDIR = Path(__file__).resolve().parent / 'artifacts'


def safe_round(v, n=6):
    try:
        if isinstance(v, bool):
            return v
        return round(float(v), n)
    except Exception:
        return v


def frame_to_text_table(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except ImportError:
        return df.to_string(index=False)


def existing_columns(df: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in df.columns]


def run_scenarios(model: CO2MathcadModel) -> pd.DataFrame:
    rows = []
    for sc in DEFAULT_SCENARIOS:
        out = model.run_result(H=sc.H, qtr=sc.qtr, Li=sc.Li, tcon=sc.tcon).to_dict()
        row = {'scenario': sc.name, **out}
        rows.append(row)
    return pd.DataFrame(rows)


def run_sweep(model: CO2MathcadModel) -> pd.DataFrame:
    q_values = [2.48, 5, 10, 20, 30, 40, 50, 60, 71.18, 76.68, 90, 100, 110, 120, 130]
    rows = []
    for q in q_values:
        out = model.run_result(H=2.5, qtr=float(q), Li=200.0, tcon=0.0).to_dict()
        rows.append({'qtr': q, **out})
    return pd.DataFrame(rows)


def run_closure_comparison(model: CO2MathcadModel, closure_models: list[str]) -> tuple[pd.DataFrame, dict[str, object]]:
    rows = []
    results = {}
    for closure_model in closure_models:
        result_obj = model.run_result(
            H=2.5,
            qtr=76.68,
            Li=200.0,
            tcon=0.0,
            mode="distributed_steady",
            closure_model=closure_model,
        )
        results[closure_model] = result_obj
        rows.append({"closure_model": closure_model, **result_obj.to_dict()})
    return pd.DataFrame(rows), results


def build_report(checks: dict, scenarios: pd.DataFrame, sweep: pd.DataFrame) -> str:
    lines = []
    lines.append('# Python port of GET CO2 Mathcad model')
    lines.append('')
    lines.append('## What was reproduced')
    lines.append('- Internal steady-state solver from the uploaded XMCD workbook for the CO2 case.')
    lines.append('- Interpolated property tables and the nonlinear search for the circulation parameter f.')
    lines.append('- Output quantities aligned with the worksheet/dissertation notation where possible: GG(0), GL(1), GL(0), chiG(1), phiG(1), DeltaP, etc.')
    lines.append('')
    lines.append('## Cached workbook checks')
    for key in checks['expected']:
        lines.append(f"- {key}: expected={checks['expected'][key]!r}, actual={checks['actual'][key]!r}, rel_err={checks['rel_err'][key]:.3e}")
    lines.append('')
    lines.append('## Scenario summary')
    show_cols = ['scenario', 'qtr', 'converged', 'solver_status', 'fff', 'tav_C', 'tmm_C', 'tvih_C', 'GG0_liq_equiv_lph', 'GG0_gas_lph', 'GL1_lph', 'GL0_lph', 'chiG1_mass', 'phiG1_true', 'deltaP_Pa']
    lines.append(frame_to_text_table(scenarios[existing_columns(scenarios, show_cols)]))
    lines.append('')
    lines.append('## Source and limit diagnostics')
    diagnostic_cols = [
        'scenario',
        'fluid',
        'property_backend',
        'model_scientific_status',
        'model_source_status',
        'regime_model',
        'regime_model_source_status',
        'boiling_onset_model',
        'preboiling_status',
        'failure_class',
        'boiling_heat_transfer_status',
        'boiling_heat_transfer_limit',
        'dryout_limit',
        'qcrit_status',
    ]
    lines.append(frame_to_text_table(scenarios[existing_columns(scenarios, diagnostic_cols)]))
    source_gate_rows = scenarios[['scenario', 'source_gate_reasons']] if 'source_gate_reasons' in scenarios else pd.DataFrame()
    if not source_gate_rows.empty:
        lines.append('')
        lines.append('### Source-gate reasons')
        for _, row in source_gate_rows.iterrows():
            reasons = row['source_gate_reasons']
            if isinstance(reasons, list):
                reason_text = '; '.join(str(item) for item in reasons) or 'none'
            else:
                reason_text = str(reasons) if reasons else 'none'
            lines.append(f"- {row['scenario']}: {reason_text}")
    lines.append('')
    lines.append('## Notes on validation')
    lines.append('- The dissertation states that the working model takes evaporator length, condenser height, condenser temperature and heat load as inputs; the same input structure is used here.')
    lines.append('- The dissertation chapter 4 / appendix G gives a CO2 benchmark for H=2.5 m, Li=200 m, tcon=0 C with qmax=71.18 W/m. In the Python port, this point is computable and some quantities are close (for example GG(0) ≈ 235.09 l/h), but the full critical-regime table is not reproduced exactly from the single XMCD workbook alone.')
    lines.append('- The dissertation explicitly defines upper critical heat load through the special limiting condition f=0; that outer critical-load algorithm is not fully encoded in the uploaded workbook and therefore is not claimed as fully reproduced here.')
    lines.append('- In distributed mode the flow-regime map is not just diagnostic anymore for the regime-aware closure: the diagnosed local regime is used to switch the underlying void-fraction and friction model inside the momentum solver.')
    lines.append('- The steady-run result reports `qcrit_status="not_evaluated"` because the separate `critical_loads` sweep is intentionally not launched from this demo.')
    lines.append('- Boiling and dryout fields are diagnostic/source-gated metadata only; published HTC, dryout and CHF correlations are not wired without full primary-source formulas.')
    lines.append('')
    lines.append('## Files')
    lines.append('- get_co2_model.py — model implementation')
    lines.append('- get_co2_results.csv — scenario outputs')
    lines.append('- get_co2_sweep.csv — load sweep outputs')
    lines.append('- get_co2_checks.json — cached-value verification')
    lines.append('- get_co2_sweep.png — publication-style sweep plot')
    lines.append('- get_co2_evaporator_profile.png — distributed steady-state evaporator profile')
    lines.append('- get_co2_riser_profile.png — distributed steady-state riser profile')
    lines.append('- get_co2_closure_comparison.csv — default-case comparison for alternative void-fraction/slip closures')
    lines.append('- get_co2_closure_comparison.png — overlay comparison of closure-model profiles')
    lines.append('- get_co2_flow_regimes.png — diagnostic flow-regime map for evaporator and riser')
    return '\n'.join(lines)


def main() -> None:
    model = CO2MathcadModel()
    OUTDIR.mkdir(parents=True, exist_ok=True)

    checks = model.cached_checks()
    scenarios = run_scenarios(model)
    sweep = run_sweep(model)

    checks_path = OUTDIR / 'get_co2_checks.json'
    results_path = OUTDIR / 'get_co2_results.csv'
    sweep_path = OUTDIR / 'get_co2_sweep.csv'
    plot_path = OUTDIR / 'get_co2_sweep.png'
    profile_plot_path = OUTDIR / 'get_co2_evaporator_profile.png'
    riser_plot_path = OUTDIR / 'get_co2_riser_profile.png'
    closure_comparison_path = OUTDIR / 'get_co2_closure_comparison.csv'
    closure_comparison_plot_path = OUTDIR / 'get_co2_closure_comparison.png'
    flow_regime_plot_path = OUTDIR / 'get_co2_flow_regimes.png'
    report_path = OUTDIR / 'get_co2_report.md'
    distributed_default = model.run_result(H=2.5, qtr=76.68, Li=200.0, tcon=0.0, mode='distributed_steady')
    closure_models = ["worksheet_compatible", "homogeneous_equilibrium", "zivi", "regime_aware"]
    closure_comparison, closure_result_map = run_closure_comparison(model, closure_models)

    checks_path.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
    scenarios.to_csv(results_path, index=False)
    sweep.to_csv(sweep_path, index=False)
    closure_comparison.to_csv(closure_comparison_path, index=False)
    plot_sweep_overview(
        sweep,
        plot_path,
        title='CO2 GET Load Sweep, H=2.5 m, Li=200 m, tcon=0 °C',
    )
    plot_evaporator_profile(
        distributed_default,
        profile_plot_path,
        title='Distributed Steady CO2 Evaporator Profile, qtr=76.68 W/m',
    )
    plot_riser_profile(
        distributed_default,
        riser_plot_path,
        title='Distributed Steady CO2 Riser Profile, qtr=76.68 W/m',
    )
    plot_flow_regime_map(
        distributed_default,
        flow_regime_plot_path,
        title='Diagnostic Flow-Regime Map, Distributed Steady CO2 Case',
    )
    plot_closure_comparison(
        closure_result_map,
        closure_comparison_plot_path,
        title='Closure-Model Comparison, Distributed Steady CO2 Case',
    )
    report_path.write_text(build_report(checks, scenarios, sweep), encoding='utf-8')

    # concise console summary
    summary_cols = ['scenario', 'qtr', 'converged', 'solver_status', 'fff', 'tav_C', 'GG0_liq_equiv_lph', 'GG0_gas_lph', 'GL1_lph', 'chiG1_mass', 'phiG1_true']
    print(scenarios[summary_cols].to_string(index=False))
    print(f'\n[OK] wrote: {results_path.name}, {sweep_path.name}, {checks_path.name}, {plot_path.name}, {profile_plot_path.name}, {riser_plot_path.name}, {flow_regime_plot_path.name}, {closure_comparison_path.name}, {closure_comparison_plot_path.name}, {report_path.name}')


if __name__ == '__main__':
    main()
