from __future__ import annotations

import math
from dataclasses import replace

import pytest

from co2_geometry import LoopGeometry, default_mathcad_geometry
from get_co2_model import CO2MathcadModel
from get_designer_geometry import (
    DesignerNode,
    DesignerSegment,
    GETScenario,
    ScenarioValidationError,
    SolverConfig,
    ThermalConfig,
    derive_geometry,
    load_scenario,
    save_scenario,
    scenario_to_dict,
    solver_inputs_from_scenario,
)


pytestmark = [pytest.mark.slow, pytest.mark.distributed]


def _manual_geometry(
    *,
    diameter_m: float = 2.0 * 1.325e-2,
    roughness_m: float = 1e-4,
    riser_height_m: float = 2.5,
) -> LoopGeometry:
    sections = tuple(
        replace(
            section,
            hydraulic_diameter_m=diameter_m,
            roughness_m=roughness_m,
            area_m2=math.pi * (0.5 * diameter_m) ** 2,
        )
        for section in default_mathcad_geometry(
            evaporator_length_m=200.0,
            riser_height_m=riser_height_m,
        ).sections
    )
    return LoopGeometry.from_sections(sections, geometry_source="manual_sections")


def _designer_scenario(
    *,
    diameter_m: float = 2.0 * 1.325e-2,
    roughness_m: float = 1e-4,
    include_evaporator: bool = True,
    riser_height_m: float = 2.5,
) -> GETScenario:
    downcomer_dx_m = math.sqrt(10.5**2 - riser_height_m**2)
    riser_dx_m = 0.0 if riser_height_m > 0.0 else 1.0
    segments = [
        DesignerSegment("evaporator", "n1", "n2", "evaporator", diameter_m, roughness_m),
        DesignerSegment("riser", "n2", "n3", "riser", diameter_m, roughness_m),
        DesignerSegment("condenser", "n3", "n4", "condenser", diameter_m, roughness_m),
        DesignerSegment("downcomer", "n4", "n5", "downcomer", diameter_m, roughness_m),
    ]
    if not include_evaporator:
        segments[0] = DesignerSegment("connector", "n1", "n2", "connector", diameter_m, roughness_m)
    return GETScenario(
        scenario_id="segmented-case",
        name="Segmented case",
        nodes=(
            DesignerNode("n1", 0.0, -2.0),
            DesignerNode("n2", 200.0, -2.0),
            DesignerNode("n3", 200.0 + riser_dx_m, -2.0 + riser_height_m),
            DesignerNode("n4", 206.5 + riser_dx_m, -2.0 + riser_height_m),
            DesignerNode("n5", 206.5 + riser_dx_m + downcomer_dx_m, -2.0),
        ),
        segments=tuple(segments),
        thermal=ThermalConfig(qtr_W_m=76.68),
        solver=SolverConfig(tcon_C=0.0, mode="distributed_steady", closure_model="worksheet_compatible"),
    )


def test_legacy_default_geometry_baseline_is_unchanged() -> None:
    result = CO2MathcadModel().run_result(
        2.5,
        76.68,
        200.0,
        0.0,
        mode="distributed_steady",
    ).to_dict()

    assert result["converged"] is True
    assert result["geometry_source"] == "mathcad_default"
    assert result["deltaP_Pa"] == pytest.approx(16043.143454892173, rel=1e-9)


def test_manual_section_diameter_changes_pressure_drop() -> None:
    model = CO2MathcadModel()
    baseline = model.one_pass(
        2.5,
        76.68,
        200.0,
        0.0,
        1.0,
        mode="distributed_steady",
        geometry=_manual_geometry(diameter_m=2.0 * 1.325e-2),
    )
    narrower = model.one_pass(
        2.5,
        76.68,
        200.0,
        0.0,
        1.0,
        mode="distributed_steady",
        geometry=_manual_geometry(diameter_m=0.024),
    )

    assert baseline is not None
    assert narrower is not None
    assert narrower["deltaP_Pa"] > baseline["deltaP_Pa"]
    assert narrower["pressure_balance_sections"][0]["hydraulic_diameter_m"] == pytest.approx(0.024)


def test_manual_section_roughness_changes_pressure_drop() -> None:
    model = CO2MathcadModel()
    smooth = model.one_pass(
        2.5,
        76.68,
        200.0,
        0.0,
        1.0,
        mode="distributed_steady",
        geometry=_manual_geometry(roughness_m=1e-5),
    )
    rough = model.one_pass(
        2.5,
        76.68,
        200.0,
        0.0,
        1.0,
        mode="distributed_steady",
        geometry=_manual_geometry(roughness_m=5e-4),
    )

    assert smooth is not None
    assert rough is not None
    assert rough["deltaP_Pa"] != pytest.approx(smooth["deltaP_Pa"])
    assert rough["pressure_balance_sections"][0]["roughness_m"] == pytest.approx(5e-4)


def test_manual_riser_height_changes_hydrostatic_contribution() -> None:
    model = CO2MathcadModel()
    low = model.one_pass(
        2.5,
        76.68,
        200.0,
        0.0,
        1.0,
        mode="distributed_steady",
        geometry=_manual_geometry(riser_height_m=2.5),
    )
    high = model.one_pass(
        4.0,
        76.68,
        200.0,
        0.0,
        1.0,
        mode="distributed_steady",
        geometry=_manual_geometry(riser_height_m=4.0),
    )

    assert low is not None
    assert high is not None
    assert abs(high["pressure_balance_total_hydrostatic_pa"]) > abs(low["pressure_balance_total_hydrostatic_pa"])


def test_designer_round_trip_preserves_geometry_and_builds_solver_geometry(tmp_path) -> None:
    scenario = _designer_scenario(diameter_m=0.03, roughness_m=2e-4)

    path = save_scenario(scenario, tmp_path)
    loaded = load_scenario(path)
    derived = derive_geometry(loaded)
    solver_inputs = solver_inputs_from_scenario(loaded)

    assert scenario_to_dict(loaded) == scenario_to_dict(scenario)
    assert derived.segments[0].hydraulic_diameter_m == pytest.approx(0.03)
    assert derived.segments[0].roughness_m == pytest.approx(2e-4)
    assert solver_inputs["geometry"].geometry_source == "designer"
    assert solver_inputs["geometry"].sections[0].area_m2 == pytest.approx(math.pi * (0.03 / 2.0) ** 2)


def test_designer_validation_rejects_missing_evaporator_and_no_positive_head() -> None:
    with pytest.raises(ScenarioValidationError, match="evaporator"):
        derive_geometry(_designer_scenario(include_evaporator=False))

    flat = _designer_scenario(riser_height_m=0.0)
    with pytest.raises(ScenarioValidationError, match="positive"):
        solver_inputs_from_scenario(flat)
