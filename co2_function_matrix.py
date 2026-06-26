from __future__ import annotations

import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap

from co2_visualization import apply_publication_style
from get_co2_model import CO2MathcadModel


MODE = "distributed_steady"
TCON_C = 0.0
DEFAULT_CLOSURES = ("worksheet_compatible", "regime_aware")
KEY_QTR_SLICES_W_M = (71.18, 76.68, 90.0, 110.0, 120.0, 130.0)
BASELINE_H_M = 2.5
BASELINE_LI_M = 200.0
NEAR_LIMIT_CHI_G = 0.95
NEAR_LIMIT_PHI_G = 0.99
NEAR_LIMIT_GL1_LPH = 1.0

INPUT_COLUMNS = [
    "closure_model",
    "mode",
    "H_m",
    "Li_m",
    "qtr_W_m",
    "tcon_C",
    "U_W",
]
STATUS_COLUMNS = [
    "functioning",
    "near_limit",
    "converged",
    "solver_status",
    "failure_reason",
    "exception_type",
    "exception_message",
]
OUTPUT_COLUMNS = [
    "fff",
    "Hy_m",
    "tav_C",
    "tmm_C",
    "tvih_C",
    "chiG1_mass",
    "phiG1_true",
    "GL1_lph",
    "GL0_lph",
    "GG0_liq_equiv_lph",
    "GG0_gas_lph",
    "deltaP_Pa",
    "driving_pressure_pa",
    "effective_density_difference_kg_m3",
    "evaporator_dominant_flow_regime",
    "riser_dominant_flow_regime",
    "evaporator_flow_regime_summary",
    "riser_flow_regime_summary",
    "closure_name",
    "property_model_name",
    "root_bracket",
    "n_sign_changes",
]
MATRIX_COLUMNS = INPUT_COLUMNS + STATUS_COLUMNS + OUTPUT_COLUMNS
CASE_KEY_COLUMNS = ["closure_model", "mode", "H_m", "Li_m", "qtr_W_m", "tcon_C"]

SUMMARY_COLUMNS = [
    "closure_model",
    "mode",
    "H_m",
    "Li_m",
    "n_cases",
    "n_working",
    "n_failed",
    "n_near_limit",
    "qtr_max_working_W_m",
    "qtr_first_failure_W_m",
    "qtr_min_near_limit_W_m",
    "U_max_working_W",
    "best_functioning_status",
    "has_nonmonotonic_status",
]

PLOT_FILENAMES = {
    "difference": "co2_qcrit_difference_heatmap.png",
    "baseline": "co2_baseline_trends_li200_h2p5.png",
}

_WORKER_MODEL: CO2MathcadModel | None = None


@dataclass(frozen=True)
class MatrixCase:
    closure_model: str
    H_m: float
    Li_m: float
    qtr_W_m: float
    tcon_C: float = TCON_C
    mode: str = MODE


@dataclass(frozen=True)
class MatrixConfig:
    li_values_m: tuple[float, ...] = field(default_factory=lambda: tuple(default_li_values()))
    h_values_m: tuple[float, ...] = field(default_factory=lambda: tuple(default_h_values()))
    qtr_values_w_m: tuple[float, ...] = field(default_factory=lambda: tuple(default_qtr_values()))
    closure_models: tuple[str, ...] = DEFAULT_CLOSURES
    tcon_C: float = TCON_C
    mode: str = MODE

    @property
    def n_cases(self) -> int:
        return (
            len(self.li_values_m)
            * len(self.h_values_m)
            * len(self.qtr_values_w_m)
            * len(self.closure_models)
        )


def default_li_values() -> list[float]:
    return _float_range(50.0, 350.0, 25.0)


def default_h_values() -> list[float]:
    return _float_range(1.0, 4.0, 0.25)


def default_qtr_values() -> list[float]:
    regular_values = [float(value) for value in range(5, 131, 5)]
    benchmark_values = [2.48, 71.18, 76.68]
    return sorted({round(value, 6) for value in regular_values + benchmark_values})


def smoke_config() -> MatrixConfig:
    return MatrixConfig(
        li_values_m=(BASELINE_LI_M,),
        h_values_m=(BASELINE_H_M,),
        qtr_values_w_m=(76.68, 130.0),
        closure_models=DEFAULT_CLOSURES,
    )


def default_worker_count() -> int:
    return max(1, min(4, (os.cpu_count() or 2) - 1))


def iter_cases(config: MatrixConfig) -> Iterable[MatrixCase]:
    for closure_model in config.closure_models:
        for li_m in config.li_values_m:
            for h_m in config.h_values_m:
                for qtr_w_m in config.qtr_values_w_m:
                    yield MatrixCase(
                        closure_model=closure_model,
                        H_m=float(h_m),
                        Li_m=float(li_m),
                        qtr_W_m=float(qtr_w_m),
                        tcon_C=float(config.tcon_C),
                        mode=config.mode,
                    )


def compute_case(case: MatrixCase) -> dict[str, object]:
    row = _base_case_row(case)
    try:
        model = _worker_model()
        result = model.run_result(
            H=case.H_m,
            qtr=case.qtr_W_m,
            Li=case.Li_m,
            tcon=case.tcon_C,
            mode=case.mode,
            closure_model=case.closure_model,
        )
        result_dict = result.to_dict()
        row.update({column: result_dict.get(column) for column in OUTPUT_COLUMNS})
        row["converged"] = bool(result_dict.get("converged", False))
        row["solver_status"] = result_dict.get("solver_status")
        row["failure_reason"] = result_dict.get("failure_reason")
        row["functioning"] = bool(row["converged"])
        row["near_limit"] = _near_limit(row)
    except Exception as exc:  # pragma: no cover - defensive path for long sweeps.
        row["functioning"] = False
        row["near_limit"] = False
        row["converged"] = False
        row["solver_status"] = "exception"
        row["failure_reason"] = str(exc)
        row["exception_type"] = type(exc).__name__
        row["exception_message"] = str(exc)
    return _normalize_row(row)


def run_analysis(
    config: MatrixConfig,
    outdir: Path,
    workers: int | None = None,
    resume: bool = True,
    max_cases: int | None = None,
    make_plots: bool = True,
) -> dict[str, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    matrix_path = outdir / "co2_function_matrix_long.csv"
    summary_path = outdir / "co2_function_matrix_summary.csv"
    report_path = outdir / "co2_function_matrix_report.md"

    df = run_matrix(
        config=config,
        path=matrix_path,
        workers=workers,
        resume=resume,
        max_cases=max_cases,
    )
    summary = build_summary(df)
    write_summary_artifacts(summary=summary, outdir=outdir, summary_path=summary_path)
    plot_paths = write_plots(df=df, summary=summary, outdir=outdir) if make_plots else {}
    report_path.write_text(
        build_report(df=df, summary=summary, plot_paths=plot_paths, config=config),
        encoding="utf-8",
    )

    outputs = {
        "matrix": matrix_path,
        "summary": summary_path,
        "report": report_path,
    }
    outputs.update(plot_paths)
    return outputs


def run_matrix(
    config: MatrixConfig,
    path: Path,
    workers: int | None = None,
    resume: bool = True,
    max_cases: int | None = None,
    flush_every: int = 10,
) -> pd.DataFrame:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_existing_matrix(path) if resume else _empty_matrix_frame()
    existing_keys = _existing_case_keys(existing)
    pending_cases = [case for case in iter_cases(config) if _case_key(case) not in existing_keys]
    if max_cases is not None:
        pending_cases = pending_cases[:max(0, max_cases)]

    if not resume and path.exists():
        path.unlink()

    if pending_cases:
        worker_count = default_worker_count() if workers is None else max(1, int(workers))
        new_rows = _compute_pending_cases(
            cases=pending_cases,
            path=path,
            workers=worker_count,
            write_header=not path.exists() or path.stat().st_size == 0,
            flush_every=flush_every,
        )
        new_df = pd.DataFrame(new_rows, columns=MATRIX_COLUMNS)
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = existing
        if not path.exists():
            combined.to_csv(path, index=False)

    combined = _sort_and_deduplicate(combined)
    combined.to_csv(path, index=False)
    return combined


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    normalized = df.copy()
    normalized["functioning"] = normalized["functioning"].map(_truthy)
    normalized["near_limit"] = normalized["near_limit"].map(_truthy)
    rows: list[dict[str, object]] = []
    for (closure_model, mode, h_m, li_m), group in normalized.groupby(
        ["closure_model", "mode", "H_m", "Li_m"],
        dropna=False,
    ):
        group = group.sort_values("qtr_W_m")
        working = group[group["functioning"]]
        failed = group[~group["functioning"]]
        near = group[group["near_limit"]]
        qtr_max_working = _max_or_nan(working["qtr_W_m"])
        qtr_first_failure = _min_or_nan(failed["qtr_W_m"])
        qtr_min_near_limit = _min_or_nan(near["qtr_W_m"])
        u_max_working = _max_or_nan(working["U_W"])
        status_sequence = list(group["functioning"])
        rows.append(
            {
                "closure_model": closure_model,
                "mode": mode,
                "H_m": float(h_m),
                "Li_m": float(li_m),
                "n_cases": int(len(group)),
                "n_working": int(len(working)),
                "n_failed": int(len(failed)),
                "n_near_limit": int(len(near)),
                "qtr_max_working_W_m": qtr_max_working,
                "qtr_first_failure_W_m": qtr_first_failure,
                "qtr_min_near_limit_W_m": qtr_min_near_limit,
                "U_max_working_W": u_max_working,
                "best_functioning_status": "working" if len(working) else "not_working",
                "has_nonmonotonic_status": _has_nonmonotonic_status(status_sequence),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS).sort_values(
        ["closure_model", "Li_m", "H_m"],
        ignore_index=True,
    )


def write_summary_artifacts(summary: pd.DataFrame, outdir: Path, summary_path: Path) -> dict[str, Path]:
    summary.to_csv(summary_path, index=False)
    paths = {"summary": summary_path}
    for closure_model, closure_summary in summary.groupby("closure_model"):
        qcrit_path = outdir / f"co2_function_matrix_qcrit_{_slug(closure_model)}.csv"
        power_path = outdir / f"co2_function_matrix_umax_{_slug(closure_model)}.csv"
        _summary_pivot(closure_summary, "qtr_max_working_W_m").to_csv(qcrit_path)
        _summary_pivot(closure_summary, "U_max_working_W").to_csv(power_path)
        paths[f"qcrit_{closure_model}"] = qcrit_path
        paths[f"umax_{closure_model}"] = power_path
    return paths


def write_plots(df: pd.DataFrame, summary: pd.DataFrame, outdir: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    paths.update(_plot_qcrit_heatmaps(summary, outdir))
    difference_path = _plot_qcrit_difference(summary, outdir)
    if difference_path is not None:
        paths["qcrit_difference"] = difference_path
    paths.update(_plot_status_slices(df, outdir))
    paths.update(_plot_boundary_curves(summary, outdir))
    baseline_path = _plot_baseline_trends(df, outdir)
    if baseline_path is not None:
        paths["baseline_trends"] = baseline_path
    return paths


def build_report(
    df: pd.DataFrame,
    summary: pd.DataFrame,
    plot_paths: dict[str, Path],
    config: MatrixConfig,
) -> str:
    lines: list[str] = []
    lines.append("# Матрица функционирования CO2-системы")
    lines.append("")
    lines.append("## Расчетная сетка")
    lines.append(f"- Режим модели: `{config.mode}`.")
    lines.append(f"- Температура конденсации: `{config.tcon_C:g} °C`.")
    lines.append(f"- Длины испарителя Li: `{_format_range(config.li_values_m)} м`.")
    lines.append(f"- Высоты H: `{_format_range(config.h_values_m)} м`.")
    lines.append(f"- Тепловые нагрузки qtr: `{len(config.qtr_values_w_m)}` уровней, от `{min(config.qtr_values_w_m):g}` до `{max(config.qtr_values_w_m):g}` Вт/м.")
    lines.append(f"- Closure-модели: `{', '.join(config.closure_models)}`.")
    lines.append("")
    lines.append("## Критерий")
    lines.append("- `functioning=True`: стационарный distributed-расчет сошелся.")
    lines.append("- `near_limit=True`: расчет сошелся, но `chiG1_mass >= 0.95`, или `phiG1_true >= 0.99`, или `GL1_lph <= 1.0`.")
    lines.append("- Матрица показывает расчетную область сходимости текущей модели, а не полный внешний алгоритм критических нагрузок из диссертации.")
    lines.append("")
    lines.append("## Сводка")
    lines.append(f"- Всего строк в матрице: `{len(df)}`.")
    if not df.empty:
        lines.append(f"- Сошедшихся расчетов: `{int(df['functioning'].map(_truthy).sum())}`.")
        lines.append(f"- Предельных, но сошедшихся расчетов: `{int(df['near_limit'].map(_truthy).sum())}`.")
    lines.append("")
    lines.extend(_report_closure_conclusions(summary))
    lines.extend(_report_closure_comparison(summary))
    lines.append("")
    lines.append("## Файлы")
    lines.append("- `co2_function_matrix_long.csv` - полная матрица расчетных точек.")
    lines.append("- `co2_function_matrix_summary.csv` - максимум рабочей нагрузки и первая точка отказа для каждой пары Li/H/closure.")
    for key, path in sorted(plot_paths.items()):
        lines.append(f"- `{path.name}` - {key}.")
    return "\n".join(lines) + "\n"


def _compute_pending_cases(
    cases: list[MatrixCase],
    path: Path,
    workers: int,
    write_header: bool,
    flush_every: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    buffer: list[dict[str, object]] = []

    def flush() -> None:
        nonlocal write_header
        if not buffer:
            return
        pd.DataFrame(buffer, columns=MATRIX_COLUMNS).to_csv(
            path,
            mode="a",
            header=write_header,
            index=False,
        )
        write_header = False
        buffer.clear()

    if workers <= 1:
        for case in cases:
            row = compute_case(case)
            rows.append(row)
            buffer.append(row)
            if len(buffer) >= flush_every:
                flush()
    else:
        with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker_model) as executor:
            futures = [executor.submit(compute_case, case) for case in cases]
            for future in as_completed(futures):
                row = future.result()
                rows.append(row)
                buffer.append(row)
                if len(buffer) >= flush_every:
                    flush()
    flush()
    return rows


def _plot_qcrit_heatmaps(summary: pd.DataFrame, outdir: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for closure_model, closure_summary in summary.groupby("closure_model"):
        pivot = _summary_pivot(closure_summary, "qtr_max_working_W_m")
        if pivot.empty:
            continue
        path = outdir / f"co2_qcrit_heatmap_{_slug(closure_model)}.png"
        _plot_heatmap(
            pivot=pivot,
            path=path,
            title=f"Max functioning qtr, {closure_model}",
            colorbar_label="qtr max, W/m",
            cmap="viridis",
        )
        paths[f"qcrit_heatmap_{closure_model}"] = path
    return paths


def _plot_qcrit_difference(summary: pd.DataFrame, outdir: Path) -> Path | None:
    closures = set(summary["closure_model"]) if not summary.empty else set()
    if not {"worksheet_compatible", "regime_aware"}.issubset(closures):
        return None
    base = summary[summary["closure_model"] == "worksheet_compatible"][
        ["H_m", "Li_m", "qtr_max_working_W_m"]
    ].rename(columns={"qtr_max_working_W_m": "worksheet"})
    regime = summary[summary["closure_model"] == "regime_aware"][
        ["H_m", "Li_m", "qtr_max_working_W_m"]
    ].rename(columns={"qtr_max_working_W_m": "regime"})
    merged = base.merge(regime, on=["H_m", "Li_m"], how="inner")
    if merged.empty:
        return None
    merged["delta_qtr_W_m"] = merged["regime"] - merged["worksheet"]
    pivot = merged.pivot(index="Li_m", columns="H_m", values="delta_qtr_W_m").sort_index().sort_index(axis=1)
    path = outdir / PLOT_FILENAMES["difference"]
    _plot_heatmap(
        pivot=pivot,
        path=path,
        title="regime_aware minus worksheet_compatible qtr limit",
        colorbar_label="Delta qtr, W/m",
        cmap="coolwarm",
    )
    return path


def _plot_status_slices(df: pd.DataFrame, outdir: Path) -> dict[str, Path]:
    if df.empty:
        return {}
    paths: dict[str, Path] = {}
    qtr_values = [value for value in KEY_QTR_SLICES_W_M if value in set(df["qtr_W_m"])]
    if not qtr_values:
        qtr_values = sorted(df["qtr_W_m"].unique())[:6]
    for closure_model, closure_df in df.groupby("closure_model"):
        available = [value for value in qtr_values if value in set(closure_df["qtr_W_m"])]
        if not available:
            continue
        path = outdir / f"co2_status_slices_{_slug(closure_model)}.png"
        _plot_status_slice_grid(closure_df, available[:6], path, closure_model)
        paths[f"status_slices_{closure_model}"] = path
    return paths


def _plot_boundary_curves(summary: pd.DataFrame, outdir: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    selected_h = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    for closure_model, closure_summary in summary.groupby("closure_model"):
        if closure_summary.empty:
            continue
        available_h = [value for value in selected_h if value in set(closure_summary["H_m"])]
        if not available_h:
            available_h = sorted(closure_summary["H_m"].unique())[:7]
        path = outdir / f"co2_boundary_curves_{_slug(closure_model)}.png"
        apply_publication_style()
        fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
        for h_m in available_h:
            line = closure_summary[closure_summary["H_m"] == h_m].sort_values("Li_m")
            ax.plot(line["Li_m"], line["qtr_max_working_W_m"], marker="o", label=f"H={h_m:g} m")
        ax.set_title(f"Functioning boundary by evaporator length, {closure_model}")
        ax.set_xlabel("Li, m")
        ax.set_ylabel("qtr max, W/m")
        ax.legend(loc="best", ncol=2)
        _style_axes([ax])
        fig.savefig(path, dpi=220, bbox_inches="tight")
        plt.close(fig)
        paths[f"boundary_curves_{closure_model}"] = path
    return paths


def _plot_baseline_trends(df: pd.DataFrame, outdir: Path) -> Path | None:
    if df.empty:
        return None
    baseline = df[
        np.isclose(df["H_m"].astype(float), BASELINE_H_M)
        & np.isclose(df["Li_m"].astype(float), BASELINE_LI_M)
    ].copy()
    if baseline.empty:
        return None
    path = outdir / PLOT_FILENAMES["baseline"]
    apply_publication_style()
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    metrics = [
        ("fff", "Circulation factor f"),
        ("phiG1_true", "True gas volume fraction"),
        ("GL1_lph", "Outlet liquid flow, l/h"),
        ("deltaP_Pa", "Total pressure drop, Pa"),
    ]
    for ax, (column, title) in zip(axes.flatten(), metrics):
        for closure_model, closure_df in baseline.groupby("closure_model"):
            closure_df = closure_df.sort_values("qtr_W_m")
            working = closure_df[closure_df["functioning"].map(_truthy)]
            if not working.empty and column in working:
                ax.plot(working["qtr_W_m"], working[column], marker="o", label=closure_model)
            failed = closure_df[~closure_df["functioning"].map(_truthy)]
            if not failed.empty:
                y_min, y_max = ax.get_ylim()
                y_marker = y_min + 0.04 * (y_max - y_min if y_max > y_min else 1.0)
                ax.scatter(failed["qtr_W_m"], [y_marker] * len(failed), marker="x", s=40)
        ax.set_title(title)
        ax.set_xlabel("qtr, W/m")
    axes.flatten()[0].legend(loc="best")
    fig.suptitle("Baseline trends, Li=200 m, H=2.5 m")
    _style_axes(axes.flatten())
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_heatmap(pivot: pd.DataFrame, path: Path, title: str, colorbar_label: str, cmap: str) -> None:
    apply_publication_style()
    fig, ax = plt.subplots(figsize=(10, 7), constrained_layout=True)
    values = pivot.to_numpy(dtype=float)
    masked_values = np.ma.masked_invalid(values)
    im = ax.imshow(masked_values, origin="lower", aspect="auto", cmap=cmap)
    ax.set_title(title)
    ax.set_xlabel("H, m")
    ax.set_ylabel("Li, m")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{float(value):g}" for value in pivot.columns], rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([f"{float(value):g}" for value in pivot.index])
    fig.colorbar(im, ax=ax, label=colorbar_label)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_status_slice_grid(df: pd.DataFrame, qtr_values: list[float], path: Path, closure_model: str) -> None:
    apply_publication_style()
    n_plots = len(qtr_values)
    ncols = 3 if n_plots > 2 else n_plots
    nrows = int(math.ceil(n_plots / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, 3.5 * nrows), constrained_layout=True)
    axes_array = np.atleast_1d(axes).flatten()
    cmap = ListedColormap(["#c65d3a", "#c79a2b", "#157a6e"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], cmap.N)
    for ax, qtr in zip(axes_array, qtr_values):
        qdf = df[np.isclose(df["qtr_W_m"].astype(float), qtr)].copy()
        qdf["status_value"] = qdf.apply(_status_value, axis=1)
        pivot = qdf.pivot(index="Li_m", columns="H_m", values="status_value").sort_index().sort_index(axis=1)
        values = pivot.to_numpy(dtype=float)
        ax.imshow(values, origin="lower", aspect="auto", cmap=cmap, norm=norm)
        ax.set_title(f"qtr={qtr:g} W/m")
        ax.set_xlabel("H, m")
        ax.set_ylabel("Li, m")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([f"{float(value):g}" for value in pivot.columns], rotation=45, ha="right")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels([f"{float(value):g}" for value in pivot.index])
    for ax in axes_array[n_plots:]:
        ax.set_visible(False)
    fig.suptitle(f"Functioning status slices, {closure_model}")
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _report_closure_conclusions(summary: pd.DataFrame) -> list[str]:
    lines = ["## Выводы по closure-моделям"]
    if summary.empty:
        lines.append("- Данных для выводов пока нет.")
        return lines
    for closure_model, closure_summary in summary.groupby("closure_model"):
        working_summary = closure_summary.dropna(subset=["qtr_max_working_W_m"])
        if working_summary.empty:
            lines.append(f"- `{closure_model}`: рабочие точки в рассчитанной сетке не найдены.")
            continue
        best_q = working_summary.loc[working_summary["qtr_max_working_W_m"].idxmax()]
        best_u = working_summary.loc[working_summary["U_max_working_W"].idxmax()]
        mean_q = working_summary["qtr_max_working_W_m"].mean()
        near_count = int(closure_summary["n_near_limit"].sum())
        fail_count = int(closure_summary["n_failed"].sum())
        lines.append(
            "- "
            f"`{closure_model}`: максимум qtr=`{best_q['qtr_max_working_W_m']:g}` Вт/м "
            f"при Li=`{best_q['Li_m']:g}` м, H=`{best_q['H_m']:g}` м; "
            f"максимальная мощность U=`{best_u['U_max_working_W']:g}` Вт; "
            f"средний предел qtr по Li/H=`{mean_q:.2f}` Вт/м; "
            f"отказов `{fail_count}`, предельных режимов `{near_count}`."
        )
    return lines


def _report_closure_comparison(summary: pd.DataFrame) -> list[str]:
    lines = ["", "## Сравнение closure-моделей"]
    closures = set(summary["closure_model"]) if not summary.empty else set()
    if not {"worksheet_compatible", "regime_aware"}.issubset(closures):
        lines.append("- Для сравнения нужны обе closure-модели.")
        return lines
    base = summary[summary["closure_model"] == "worksheet_compatible"][
        ["H_m", "Li_m", "qtr_max_working_W_m"]
    ].rename(columns={"qtr_max_working_W_m": "worksheet"})
    regime = summary[summary["closure_model"] == "regime_aware"][
        ["H_m", "Li_m", "qtr_max_working_W_m"]
    ].rename(columns={"qtr_max_working_W_m": "regime"})
    merged = base.merge(regime, on=["H_m", "Li_m"], how="inner")
    if merged.empty:
        lines.append("- Общих Li/H-точек для сравнения нет.")
        return lines
    merged["delta"] = merged["regime"] - merged["worksheet"]
    lines.append(
        "- "
        f"`regime_aware` выше `worksheet_compatible` в `{int((merged['delta'] > 0).sum())}` Li/H-точках, "
        f"ниже в `{int((merged['delta'] < 0).sum())}` Li/H-точках; "
        f"средняя разница `{merged['delta'].mean():.2f}` Вт/м."
    )
    return lines


def _base_case_row(case: MatrixCase) -> dict[str, object]:
    return {
        "closure_model": case.closure_model,
        "mode": case.mode,
        "H_m": case.H_m,
        "Li_m": case.Li_m,
        "qtr_W_m": case.qtr_W_m,
        "tcon_C": case.tcon_C,
        "U_W": case.qtr_W_m * case.Li_m,
        "functioning": False,
        "near_limit": False,
        "converged": False,
        "solver_status": "not_run",
        "failure_reason": None,
        "exception_type": None,
        "exception_message": None,
    }


def _normalize_row(row: dict[str, object]) -> dict[str, object]:
    for column in MATRIX_COLUMNS:
        row.setdefault(column, None)
    return {column: row[column] for column in MATRIX_COLUMNS}


def _worker_model() -> CO2MathcadModel:
    global _WORKER_MODEL
    if _WORKER_MODEL is None:
        _WORKER_MODEL = CO2MathcadModel()
    return _WORKER_MODEL


def _init_worker_model() -> None:
    _worker_model()


def _near_limit(row: dict[str, object]) -> bool:
    if not _truthy(row.get("converged")):
        return False
    chi_g = _as_float(row.get("chiG1_mass"))
    phi_g = _as_float(row.get("phiG1_true"))
    gl1 = _as_float(row.get("GL1_lph"))
    return (
        (not math.isnan(chi_g) and chi_g >= NEAR_LIMIT_CHI_G)
        or (not math.isnan(phi_g) and phi_g >= NEAR_LIMIT_PHI_G)
        or (not math.isnan(gl1) and gl1 <= NEAR_LIMIT_GL1_LPH)
    )


def _status_value(row: pd.Series) -> int:
    if not _truthy(row.get("functioning")):
        return 0
    if _truthy(row.get("near_limit")):
        return 1
    return 2


def _read_existing_matrix(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return _empty_matrix_frame()
    df = pd.read_csv(path)
    for column in MATRIX_COLUMNS:
        if column not in df:
            df[column] = None
    return _sort_and_deduplicate(df[MATRIX_COLUMNS])


def _empty_matrix_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=MATRIX_COLUMNS)


def _sort_and_deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return _empty_matrix_frame()
    deduped = df.drop_duplicates(subset=CASE_KEY_COLUMNS, keep="last")
    return deduped.sort_values(CASE_KEY_COLUMNS, ignore_index=True)


def _existing_case_keys(df: pd.DataFrame) -> set[tuple[object, ...]]:
    if df.empty:
        return set()
    return {
        _case_key_from_values(
            row["closure_model"],
            row["mode"],
            row["H_m"],
            row["Li_m"],
            row["qtr_W_m"],
            row["tcon_C"],
        )
        for _, row in df.iterrows()
    }


def _case_key(case: MatrixCase) -> tuple[object, ...]:
    return _case_key_from_values(
        case.closure_model,
        case.mode,
        case.H_m,
        case.Li_m,
        case.qtr_W_m,
        case.tcon_C,
    )


def _case_key_from_values(
    closure_model: object,
    mode: object,
    h_m: object,
    li_m: object,
    qtr_w_m: object,
    tcon_c: object,
) -> tuple[object, ...]:
    return (
        str(closure_model),
        str(mode),
        round(float(h_m), 6),
        round(float(li_m), 6),
        round(float(qtr_w_m), 6),
        round(float(tcon_c), 6),
    )


def _summary_pivot(summary: pd.DataFrame, value_column: str) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    return summary.pivot(index="Li_m", columns="H_m", values=value_column).sort_index().sort_index(axis=1)


def _has_nonmonotonic_status(status_sequence: list[bool]) -> bool:
    seen_failure = False
    for status in status_sequence:
        if not status:
            seen_failure = True
        elif seen_failure:
            return True
    return False


def _float_range(start: float, stop: float, step: float) -> list[float]:
    values: list[float] = []
    current = start
    while current <= stop + step * 1e-9:
        values.append(round(current, 6))
        current += step
    return values


def _as_float(value: object) -> float:
    try:
        if value is None or value == "":
            return float("nan")
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _max_or_nan(series: pd.Series) -> float:
    return float(series.max()) if not series.empty else float("nan")


def _min_or_nan(series: pd.Series) -> float:
    return float(series.min()) if not series.empty else float("nan")


def _slug(value: object) -> str:
    return str(value).replace(" ", "_").replace("/", "_").replace("+", "plus")


def _format_range(values: Iterable[float]) -> str:
    values = tuple(values)
    if not values:
        return "empty"
    if len(values) == 1:
        return f"{values[0]:g}"
    return f"{min(values):g}..{max(values):g}, n={len(values)}"


def _style_axes(axes: Iterable[plt.Axes]) -> None:
    for ax in axes:
        ax.grid(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
