from __future__ import annotations

import csv
from pathlib import Path

import pytest

from refrigerant_properties import CoolPropSaturationProperties


REFERENCE_DIR = Path(__file__).resolve().parents[1] / "data" / "reference_properties"
REFERENCE_COLUMNS = (
    "temperature_c",
    "pressure_pa",
    "latent_heat_j_kg",
    "rho_l_kg_m3",
    "rho_g_kg_m3",
    "mu_l_pa_s",
    "mu_g_pa_s",
    "cp_l_j_kgk",
    "cp_g_j_kgk",
    "k_l_w_mk",
    "k_g_w_mk",
    "surface_tension_n_m",
)


def _load_reference_rows(filename: str) -> list[dict[str, float]]:
    with (REFERENCE_DIR / filename).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames or ()) == REFERENCE_COLUMNS
        return [{key: float(value) for key, value in row.items()} for row in reader]


def test_nh3_reference_csv_matches_coolprop_backend() -> None:
    properties = CoolPropSaturationProperties("R717")
    rows = _load_reference_rows("nh3_saturation_coolprop.csv")

    assert len(rows) == 5
    previous_pressure = 0.0
    for row in rows:
        state = properties.state_at_temperature(row["temperature_c"])

        assert state.fluid == "NH3"
        assert state.rho_l_kg_m3 > state.rho_g_kg_m3
        assert state.latent_heat_j_kg > 0.0
        assert state.pressure_pa > previous_pressure
        assert state.mu_l_pa_s > 0.0
        assert state.mu_g_pa_s > 0.0

        for field in REFERENCE_COLUMNS[1:]:
            assert getattr(state, field) == pytest.approx(row[field], rel=1e-9, abs=1e-12)

        previous_pressure = state.pressure_pa


def test_co2_reference_csv_matches_coolprop_backend() -> None:
    properties = CoolPropSaturationProperties("R744")
    rows = _load_reference_rows("co2_saturation_coolprop.csv")

    assert len(rows) == 5
    for row in rows:
        state = properties.state_at_temperature(row["temperature_c"])
        assert state.fluid == "CO2"
        assert state.latent_heat_j_kg > 0.0
        assert state.rho_l_kg_m3 > state.rho_g_kg_m3
        assert state.pressure_pa == pytest.approx(row["pressure_pa"], rel=1e-9)
        assert state.latent_heat_j_kg == pytest.approx(row["latent_heat_j_kg"], rel=1e-9)
