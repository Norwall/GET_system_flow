from __future__ import annotations

import pytest

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
    validate_scenario,
)


def _profile_scenario(H_override_m: float | None = None) -> GETScenario:
    return GETScenario(
        scenario_id="case-1",
        name="Case 1",
        nodes=(
            DesignerNode(id="n1", x_m=0.0, z_m=-2.0),
            DesignerNode(id="n2", x_m=100.0, z_m=-2.0),
            DesignerNode(id="n3", x_m=100.0, z_m=1.0),
            DesignerNode(id="n4", x_m=110.0, z_m=1.0),
            DesignerNode(id="n5", x_m=0.0, z_m=-2.0),
        ),
        segments=(
            DesignerSegment(id="s1", start_node_id="n1", end_node_id="n2", kind="evaporator"),
            DesignerSegment(id="s2", start_node_id="n2", end_node_id="n3", kind="riser"),
            DesignerSegment(id="s3", start_node_id="n3", end_node_id="n4", kind="condenser"),
            DesignerSegment(id="s4", start_node_id="n4", end_node_id="n5", kind="downcomer"),
        ),
        thermal=ThermalConfig(qtr_W_m=5.0),
        solver=SolverConfig(
            tcon_C=0.0,
            mode="worksheet_compatible",
            closure_model="worksheet_compatible",
            H_override_m=H_override_m,
        ),
    )


def test_derive_geometry_from_profile_points() -> None:
    derived = derive_geometry(_profile_scenario())

    assert derived.evaporator_length_m == pytest.approx(100.0)
    assert derived.evaporator_mean_z_m == pytest.approx(-2.0)
    assert derived.evaporator_depth_m == pytest.approx(2.0)
    assert derived.top_z_m == pytest.approx(1.0)
    assert derived.geometric_head_m == pytest.approx(3.0)
    assert derived.H_m == pytest.approx(3.0)
    assert derived.heat_power_W == pytest.approx(500.0)
    assert derived.segments[0].angle_deg == pytest.approx(0.0)
    assert derived.segments[1].angle_deg == pytest.approx(90.0)


def test_h_override_replaces_derived_head() -> None:
    derived = derive_geometry(_profile_scenario(H_override_m=2.5))

    assert derived.geometric_head_m == pytest.approx(3.0)
    assert derived.H_m == pytest.approx(2.5)


def test_save_and_load_scenario_round_trip(tmp_path) -> None:
    scenario = _profile_scenario(H_override_m=2.5)

    path = save_scenario(scenario, tmp_path)
    loaded = load_scenario(path)

    assert path.name == "case-1.json"
    assert scenario_to_dict(loaded) == scenario_to_dict(scenario)


def test_accepts_explicit_experimental_regime_aware_closure() -> None:
    scenario = _profile_scenario()
    scenario = GETScenario(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        nodes=scenario.nodes,
        segments=scenario.segments,
        thermal=scenario.thermal,
        solver=SolverConfig(
            tcon_C=scenario.solver.tcon_C,
            mode=scenario.solver.mode,
            closure_model="experimental_regime_aware",
            H_override_m=scenario.solver.H_override_m,
        ),
    )

    validate_scenario(scenario)


def test_requires_evaporator_segment() -> None:
    scenario = _profile_scenario()
    scenario = GETScenario(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        nodes=scenario.nodes,
        segments=tuple(
            DesignerSegment(
                id=segment.id,
                start_node_id=segment.start_node_id,
                end_node_id=segment.end_node_id,
                kind="connector",
            )
            for segment in scenario.segments
        ),
        thermal=scenario.thermal,
        solver=scenario.solver,
    )

    with pytest.raises(ScenarioValidationError, match="evaporator"):
        derive_geometry(scenario)
