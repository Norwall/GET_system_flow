from __future__ import annotations

import math

import pytest

from co2_properties import CO2SaturationProperties
from refrigerant_properties import (
    CoolPropSaturationProperties,
    MathcadCO2SaturationProperties,
    PropertyRangeError,
    RefpropSaturationProperties,
    SaturationState,
    create_saturation_properties,
    normalize_fluid_name,
)


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("CO2", "CO2"),
        ("R744", "CO2"),
        ("CarbonDioxide", "CO2"),
        ("carbon dioxide", "CO2"),
        ("NH3", "NH3"),
        ("R717", "NH3"),
        ("Ammonia", "NH3"),
    ],
)
def test_fluid_aliases_normalize_to_canonical_names(alias: str, canonical: str) -> None:
    assert normalize_fluid_name(alias) == canonical


def test_mathcad_co2_backend_preserves_legacy_baseline_values() -> None:
    properties = CO2SaturationProperties()
    state = properties.state_at_temperature(-10.0)

    assert isinstance(state, SaturationState)
    assert isinstance(properties, MathcadCO2SaturationProperties)
    assert type(properties).__name__ == "CO2SaturationProperties"
    assert properties.fluid == "CO2"
    assert properties.property_backend == "mathcad_table"
    assert properties.pressure_pa(-10.0) == pytest.approx(2647719.0, rel=0.0, abs=0.0)
    assert properties.latent_heat_j_per_kg(-10.0) == pytest.approx(261716.868, rel=0.0, abs=0.0)
    assert state.latent_heat_j_kg == pytest.approx(state.h_g_j_kg - state.h_l_j_kg)
    assert state.v_l_m3_per_kg == state.v_l_m3_kg
    assert state.cp_l_j_per_kgk == state.cp_l_j_kgk


def test_mathcad_co2_backend_blocks_implicit_extrapolation() -> None:
    strict_properties = CO2SaturationProperties()
    explicit_properties = CO2SaturationProperties(allow_property_extrapolation=True)

    with pytest.raises(PropertyRangeError, match="outside allowed range"):
        strict_properties.pressure_pa(-30.0)

    assert math.isfinite(float(explicit_properties.pressure_pa(-30.0)))
    assert "Extrapolation is explicitly enabled" in explicit_properties.property_warning_at_temperature(-30.0)


@pytest.mark.parametrize(
    ("fluid", "temperatures_c"),
    [
        ("CO2", (-20.0, -10.0, 0.0, 10.0, 20.0)),
        ("NH3", (-40.0, -20.0, 0.0, 20.0, 40.0)),
    ],
)
def test_coolprop_saturation_states_are_physical_on_temperature_grid(
    fluid: str,
    temperatures_c: tuple[float, ...],
) -> None:
    properties = CoolPropSaturationProperties(fluid=fluid)
    pressures = []

    for temperature_c in temperatures_c:
        state = properties.state_at_temperature(temperature_c)
        pressures.append(state.pressure_pa)

        assert state.fluid == normalize_fluid_name(fluid)
        assert state.latent_heat_j_kg == pytest.approx(state.h_g_j_kg - state.h_l_j_kg, rel=1e-12)
        assert state.rho_l_kg_m3 > state.rho_g_kg_m3
        assert state.latent_heat_j_kg > 0.0
        assert state.mu_l_pa_s > 0.0
        assert state.mu_g_pa_s > 0.0
        assert state.cp_l_j_kgk > 0.0
        assert state.cp_g_j_kgk > 0.0
        assert state.k_l_w_mk > 0.0
        assert state.k_g_w_mk > 0.0
        assert state.surface_tension_n_m > 0.0
        assert state.dp_sat_dT_pa_per_k > 0.0
        assert properties.temperature_from_pressure_pa(state.pressure_pa) == pytest.approx(temperature_c, abs=1e-8)

    assert pressures == sorted(pressures)


def test_coolprop_backend_reports_near_critical_and_rejects_supercritical_saturation() -> None:
    properties = CoolPropSaturationProperties(fluid="R744")
    near_critical_c = properties.critical_temperature_c - 1.0

    assert "critical temperature" in properties.near_critical_warning_at_temperature(near_critical_c)
    with pytest.raises(PropertyRangeError, match="outside allowed range"):
        properties.state_at_temperature(properties.critical_temperature_c)
    with pytest.raises(PropertyRangeError, match="saturation pressure"):
        properties.temperature_from_pressure_pa(properties.triple_pressure_pa * 0.5)


def test_factory_creates_requested_property_backends() -> None:
    mathcad = create_saturation_properties("CO2", "mathcad_table")
    coolprop = create_saturation_properties("R717", "coolprop")

    assert isinstance(mathcad, MathcadCO2SaturationProperties)
    assert isinstance(coolprop, CoolPropSaturationProperties)
    assert coolprop.fluid == "NH3"

    with pytest.raises(ValueError, match="only available for CO2"):
        create_saturation_properties("NH3", "mathcad_table")


def test_refprop_adapter_fails_with_clear_error_when_backend_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    import CoolProp.CoolProp as coolprop

    def fake_props_si(output: str, *args: object) -> float:
        fluid = str(args[-1]) if args else ""
        if output == "Ttriple":
            return 216.592
        if output == "Tcrit":
            if fluid.startswith("REFPROP::"):
                raise ValueError("REFPROP backend unavailable")
            return 304.1282
        if output == "ptriple":
            return 517964.0
        if output == "pcrit":
            return 7377298.0
        raise AssertionError(f"Unexpected fake PropsSI call: {output!r}")

    monkeypatch.setattr(coolprop, "PropsSI", fake_props_si)

    with pytest.raises(Exception, match="REFPROP backend is not available"):
        RefpropSaturationProperties("CO2")
