from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from co2_results import SteadyLoopResult
from two_phase_regimes import FLOW_REGIME_COLORS


COLOR_NAVY = "#18324a"
COLOR_TEAL = "#157a6e"
COLOR_RUST = "#c65d3a"
COLOR_GOLD = "#c79a2b"
COLOR_SLATE = "#60758a"
GRID_COLOR = "#d6dce5"
CLOSURE_COLORS = {
    "worksheet_compatible": COLOR_NAVY,
    "homogeneous_equilibrium": COLOR_RUST,
    "zivi": COLOR_TEAL,
    "regime_aware": COLOR_GOLD,
}


def apply_publication_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#5c6773",
            "axes.linewidth": 0.9,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "legend.frameon": False,
            "legend.fontsize": 9,
            "xtick.color": "#36424f",
            "ytick.color": "#36424f",
            "xtick.major.size": 4,
            "ytick.major.size": 4,
            "grid.color": GRID_COLOR,
            "grid.linewidth": 0.8,
            "grid.alpha": 0.8,
            "lines.linewidth": 2.2,
        }
    )


def _style_axes(axes: Iterable[plt.Axes]) -> None:
    for ax in axes:
        ax.grid(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)


def _point_edges(coordinate: list[float]) -> np.ndarray:
    values = np.asarray(coordinate, dtype=float)
    if values.size == 0:
        return np.asarray([0.0, 1.0], dtype=float)
    if values.size == 1:
        return np.asarray([values[0] - 0.5, values[0] + 0.5], dtype=float)
    midpoints = 0.5 * (values[1:] + values[:-1])
    edges = np.empty(values.size + 1, dtype=float)
    edges[1:-1] = midpoints
    edges[0] = values[0] - (midpoints[0] - values[0])
    edges[-1] = values[-1] + (values[-1] - midpoints[-1])
    return edges


def _contiguous_label_segments(coordinate: list[float], labels: list[str]) -> list[tuple[float, float, str]]:
    if not coordinate or not labels:
        return []
    edges = _point_edges(coordinate)
    segments: list[tuple[float, float, str]] = []
    start_index = 0
    current_label = labels[0]
    for index in range(1, len(labels)):
        if labels[index] != current_label:
            segments.append((float(edges[start_index]), float(edges[index]), current_label))
            start_index = index
            current_label = labels[index]
    segments.append((float(edges[start_index]), float(edges[-1]), current_label))
    return segments


def _shade_regimes(ax: plt.Axes, coordinate: list[float], labels: list[str], alpha: float = 0.12) -> None:
    for start, end, label in _contiguous_label_segments(coordinate, labels):
        ax.axvspan(start, end, color=FLOW_REGIME_COLORS.get(label, "#d7dee7"), alpha=alpha, zorder=0)


def plot_sweep_overview(df: pd.DataFrame, path: Path, title: str) -> None:
    apply_publication_style()
    ok = df[df["converged"] == True].copy()
    if ok.empty:
        return

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    ax1, ax2, ax3, ax4 = axes.flatten()

    ax1.plot(ok["qtr"], ok["chiG1_mass"], color=COLOR_NAVY)
    ax1.set_title("Mass Quality")
    ax1.set_xlabel("qtr, W/m")
    ax1.set_ylabel("chiG1")

    ax2.plot(ok["qtr"], ok["phiG1_true"], color=COLOR_TEAL)
    ax2.set_title("True Gas Volume Fraction")
    ax2.set_xlabel("qtr, W/m")
    ax2.set_ylabel("phiG,true")

    ax3.plot(ok["qtr"], ok["GL1_lph"], color=COLOR_RUST)
    ax3.set_title("Outlet Liquid Flow")
    ax3.set_xlabel("qtr, W/m")
    ax3.set_ylabel("GL1, l/h")

    ax4.plot(ok["qtr"], ok["deltaP_Pa"], color=COLOR_GOLD)
    ax4.set_title("Total Pressure Drop")
    ax4.set_xlabel("qtr, W/m")
    ax4.set_ylabel("DeltaP, Pa")

    failed = df[df["converged"] == False]
    if not failed.empty:
        for ax in axes.flatten():
            ax.scatter(
                failed["qtr"],
                [ax.get_ylim()[0] + 0.03 * (ax.get_ylim()[1] - ax.get_ylim()[0])] * len(failed),
                color=COLOR_SLATE,
                marker="x",
                s=36,
                linewidths=1.2,
                zorder=4,
            )

    fig.suptitle(title, fontsize=15, fontweight="bold", color=COLOR_NAVY)
    _style_axes(axes.flatten())
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_evaporator_profile(result: SteadyLoopResult, path: Path, title: str) -> None:
    apply_publication_style()
    if result.pass_result is None or result.pass_result.evaporator_profile is None:
        return

    profile = result.pass_result.evaporator_profile
    x_m = list(profile.axial_position_m)
    temperature_c = list(profile.local_temperature_c)
    pressure_mpa = [value / 1e6 for value in profile.local_pressure_pa]
    vapor_flow_kg_h = [value * 3600.0 for value in profile.vapor_mass_flow_kg_s]
    pressure_gradient_kpa_m = [value / 1e3 for value in profile.two_phase_pressure_gradient_pa_per_m]

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    ax1, ax2, ax3, ax4 = axes.flatten()

    ax1.plot(x_m, temperature_c, color=COLOR_RUST)
    ax1.set_title("Temperature Along Evaporator")
    ax1.set_xlabel("x, m")
    ax1.set_ylabel("T, degC")

    ax2.plot(x_m, pressure_mpa, color=COLOR_NAVY)
    ax2.set_title("Pressure Along Evaporator")
    ax2.set_xlabel("x, m")
    ax2.set_ylabel("p, MPa")

    ax3.plot(x_m, vapor_flow_kg_h, color=COLOR_TEAL)
    ax3.set_title("Vapor Generation Profile")
    ax3.set_xlabel("x, m")
    ax3.set_ylabel("GG, kg/h")

    ax4.plot(x_m, pressure_gradient_kpa_m, color=COLOR_GOLD)
    ax4.set_title("Pressure-Gradient Profile")
    ax4.set_xlabel("x, m")
    ax4.set_ylabel("dp/dx, kPa/m")

    boiling_onset_x_m = result.pass_result.boiling_onset_position_m
    regime_labels = list(profile.flow_regime)
    for ax in axes.flatten():
        _shade_regimes(ax, x_m, regime_labels)
        ax.axvspan(0.0, boiling_onset_x_m, color="#eef2f6", alpha=0.8, zorder=0)
        ax.axvline(boiling_onset_x_m, color=COLOR_SLATE, linestyle="--", linewidth=1.2)
        ax.text(
            boiling_onset_x_m,
            ax.get_ylim()[1],
            "boiling onset",
            color=COLOR_SLATE,
            fontsize=8,
            ha="left",
            va="top",
        )

    fig.suptitle(title, fontsize=15, fontweight="bold", color=COLOR_NAVY)
    _style_axes(axes.flatten())
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_riser_profile(result: SteadyLoopResult, path: Path, title: str) -> None:
    apply_publication_style()
    if result.pass_result is None or result.pass_result.riser_profile is None:
        return

    profile = result.pass_result.riser_profile
    height_m = list(profile.height_m)
    temperature_c = list(profile.local_temperature_c)
    pressure_mpa = [value / 1e6 for value in profile.local_pressure_pa]
    mixture_density = list(profile.mixture_density_kg_m3)
    gas_fraction = list(profile.gas_volume_fraction)
    regime_labels = list(profile.flow_regime)

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    ax1, ax2, ax3, ax4 = axes.flatten()

    ax1.plot(height_m, temperature_c, color=COLOR_RUST)
    ax1.set_title("Riser Saturation Temperature")
    ax1.set_xlabel("z, m")
    ax1.set_ylabel("T, degC")

    ax2.plot(height_m, pressure_mpa, color=COLOR_NAVY)
    ax2.set_title("Riser Pressure")
    ax2.set_xlabel("z, m")
    ax2.set_ylabel("p, MPa")

    ax3.plot(height_m, mixture_density, color=COLOR_TEAL)
    ax3.set_title("Riser Mixture Density")
    ax3.set_xlabel("z, m")
    ax3.set_ylabel("rho_mix, kg/m^3")

    ax4.plot(height_m, gas_fraction, color=COLOR_GOLD)
    ax4.set_title("Riser Gas Volume Fraction")
    ax4.set_xlabel("z, m")
    ax4.set_ylabel("phiG")

    for ax in axes.flatten():
        _shade_regimes(ax, height_m, regime_labels)

    fig.suptitle(title, fontsize=15, fontweight="bold", color=COLOR_NAVY)
    _style_axes(axes.flatten())
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_closure_comparison(results: dict[str, SteadyLoopResult], path: Path, title: str) -> None:
    apply_publication_style()
    if not results:
        return

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    ax1, ax2, ax3, ax4 = axes.flatten()

    for closure_name, result in results.items():
        if result.pass_result is None or result.pass_result.evaporator_profile is None or result.pass_result.riser_profile is None:
            continue
        color = CLOSURE_COLORS.get(closure_name, COLOR_SLATE)
        evap = result.pass_result.evaporator_profile
        riser = result.pass_result.riser_profile
        label = closure_name.replace("_", " ")

        ax1.plot(evap.axial_position_m, evap.local_temperature_c, color=color, label=label)
        ax2.plot(evap.axial_position_m, [value / 1e6 for value in evap.local_pressure_pa], color=color, label=label)
        ax3.plot(riser.height_m, riser.gas_volume_fraction, color=color, label=label)
        ax4.plot(riser.height_m, riser.mixture_density_kg_m3, color=color, label=label)

    ax1.set_title("Evaporator Temperature")
    ax1.set_xlabel("x, m")
    ax1.set_ylabel("T, degC")

    ax2.set_title("Evaporator Pressure")
    ax2.set_xlabel("x, m")
    ax2.set_ylabel("p, MPa")

    ax3.set_title("Riser Gas Volume Fraction")
    ax3.set_xlabel("z, m")
    ax3.set_ylabel("phiG")

    ax4.set_title("Riser Mixture Density")
    ax4.set_xlabel("z, m")
    ax4.set_ylabel("rho_mix, kg/m^3")

    handles, labels = ax1.get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=min(3, len(handles)), frameon=False, bbox_to_anchor=(0.5, 1.02))

    fig.suptitle(title, fontsize=15, fontweight="bold", color=COLOR_NAVY)
    _style_axes(axes.flatten())
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_flow_regime_map(result: SteadyLoopResult, path: Path, title: str) -> None:
    apply_publication_style()
    if result.pass_result is None or result.pass_result.evaporator_profile is None or result.pass_result.riser_profile is None:
        return

    evaporator = result.pass_result.evaporator_profile
    riser = result.pass_result.riser_profile

    fig, axes = plt.subplots(2, 1, figsize=(11, 4.8), constrained_layout=True)
    evaporator_ax, riser_ax = axes

    used_labels: list[str] = []
    for start, end, label in _contiguous_label_segments(list(evaporator.axial_position_m), list(evaporator.flow_regime)):
        evaporator_ax.broken_barh([(start, max(end - start, 1e-9))], (0.15, 0.7), facecolors=FLOW_REGIME_COLORS.get(label, "#d7dee7"))
        if label not in used_labels:
            used_labels.append(label)
    for start, end, label in _contiguous_label_segments(list(riser.height_m), list(riser.flow_regime)):
        riser_ax.broken_barh([(start, max(end - start, 1e-9))], (0.15, 0.7), facecolors=FLOW_REGIME_COLORS.get(label, "#d7dee7"))
        if label not in used_labels:
            used_labels.append(label)

    evaporator_ax.set_title("Horizontal Evaporator Flow Regimes")
    evaporator_ax.set_xlabel("x, m")
    evaporator_ax.set_xlim(min(evaporator.axial_position_m), max(evaporator.axial_position_m))
    evaporator_ax.set_yticks([])
    evaporator_ax.set_ylim(0.0, 1.0)
    evaporator_ax.text(
        0.01,
        0.88,
        f"dominant: {result.pass_result.evaporator_dominant_flow_regime}",
        transform=evaporator_ax.transAxes,
        color=COLOR_NAVY,
        fontsize=9,
        ha="left",
        va="top",
    )

    riser_ax.set_title("Vertical Riser Flow Regimes")
    riser_ax.set_xlabel("z, m")
    riser_ax.set_xlim(min(riser.height_m), max(riser.height_m))
    riser_ax.set_yticks([])
    riser_ax.set_ylim(0.0, 1.0)
    riser_ax.text(
        0.01,
        0.88,
        f"dominant: {result.pass_result.riser_dominant_flow_regime}",
        transform=riser_ax.transAxes,
        color=COLOR_NAVY,
        fontsize=9,
        ha="left",
        va="top",
    )

    legend_handles = [
        Patch(color=FLOW_REGIME_COLORS.get(label, "#d7dee7"))
        for label in used_labels
    ]
    if legend_handles:
        fig.legend(
            legend_handles,
            [label.replace("_", " ") for label in used_labels],
            loc="lower center",
            ncol=min(4, len(legend_handles)),
            frameon=False,
            bbox_to_anchor=(0.5, -0.08),
        )

    fig.suptitle(title, fontsize=14, fontweight="bold", color=COLOR_NAVY)
    _style_axes(axes)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
