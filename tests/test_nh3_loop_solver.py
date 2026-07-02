from __future__ import annotations

import pytest

from co2_geometry import LoopGeometry
from co2_steady_solver import SteadyLoopInputs
from refrigerant_loop_model import RefrigerantLoopModel
from refrigerant_properties import CoolPropSaturationProperties


def test_nh3_loop_solver_converges_on_nominal_coolprop_case() -> None:
    model = RefrigerantLoopModel(fluid="Ammonia", property_backend="coolprop")
    data = model.run(H=2.5, qtr=76.68, Li=200.0, tcon=0.0)

    assert isinstance(model.properties, CoolPropSaturationProperties)
    assert data["converged"] is True
    assert data["solver_status"] == "converged"
    assert data["fluid"] == "NH3"
    assert data["fluid_cas"] == "7664-41-7"
    assert data["refrigerant_name"] == "Ammonia"
    assert data["property_backend"] == "coolprop"
    assert data["property_model_name"] == "CoolPropSaturationProperties"
    assert data["fff"] == pytest.approx(0.3980164527274948, rel=1e-9)
    assert data["outlet_mass_quality"] > 0.0


def test_same_geometry_object_solves_co2_and_nh3_with_different_results() -> None:
    geometry = LoopGeometry().with_default_sections(evaporator_length_m=200.0, riser_height_m=2.5)
    co2_model = RefrigerantLoopModel(fluid="CO2", property_backend="coolprop", geometry=geometry)
    nh3_model = RefrigerantLoopModel(fluid="NH3", property_backend="coolprop", geometry=geometry)

    co2 = co2_model.run(H=2.5, qtr=40.0, Li=200.0, tcon=0.0)
    nh3 = nh3_model.run(H=2.5, qtr=40.0, Li=200.0, tcon=0.0)

    assert co2["converged"] is True
    assert nh3["converged"] is True
    assert co2["fluid"] == "CO2"
    assert nh3["fluid"] == "NH3"
    assert co2["geometry_source"] == nh3["geometry_source"] == geometry.geometry_source
    assert co2["fff"] != pytest.approx(nh3["fff"], rel=1e-6)
    assert co2["deltaP_Pa"] != pytest.approx(nh3["deltaP_Pa"], rel=1e-6)


def test_nh3_rejects_mathcad_table_backend() -> None:
    with pytest.raises(ValueError, match="only available for CO2"):
        RefrigerantLoopModel(fluid="R717", property_backend="mathcad_table")


def test_nh3_high_heat_load_reports_structured_no_root_status() -> None:
    model = RefrigerantLoopModel(fluid="NH3", property_backend="coolprop")
    data = model.run(H=2.5, qtr=120.0, Li=200.0, tcon=0.0)

    assert data["converged"] is False
    assert data["solver_status"] == "no_root_bracket"
    assert data["failure_reason"]
    assert data["fluid"] == "NH3"
    assert data["property_backend"] == "coolprop"


@pytest.mark.parametrize(
    ("name", "qtr", "tcon", "expected_f"),
    [
        ("small_qtr", 5.0, 0.0, 65.94164948151939),
        ("low_saturation_temperature", 30.0, -20.0, 3.942149943485161),
        ("upper_temperature_grid_point", 76.68, 40.0, 0.67702933296906),
    ],
)
def test_nh3_additional_scenarios_are_structured(
    name: str,
    qtr: float,
    tcon: float,
    expected_f: float,
) -> None:
    model = RefrigerantLoopModel(fluid="NH3", property_backend="coolprop")
    data = model.run(H=2.5, qtr=qtr, Li=200.0, tcon=tcon)

    assert name
    assert data["converged"] is True
    assert data["solver_status"] == "converged"
    assert data["fluid"] == "NH3"
    assert data["fff"] == pytest.approx(expected_f, rel=1e-9)


@pytest.mark.slow
@pytest.mark.distributed
def test_nh3_distributed_one_pass_builds_profiles_without_co2_tables() -> None:
    model = RefrigerantLoopModel(fluid="NH3", property_backend="coolprop")
    inputs = SteadyLoopInputs(
        H=2.5,
        qtr=40.0,
        Li=200.0,
        tcon=0.0,
        mode="distributed_steady",
        closure_model="zivi",
        friction_model="colebrook_white",
    )

    pass_result = model.steady_solver.one_pass(
        inputs=inputs,
        circulation_factor=2.6901983306018518,
        ngrid=25,
    )

    assert pass_result is not None
    assert pass_result.evaporator_profile is not None
    assert pass_result.riser_profile is not None
    assert pass_result.evaporator_profile.n_points == 25
    assert pass_result.riser_profile.n_points > 0
    assert pass_result.outlet_mass_quality > 0.0
