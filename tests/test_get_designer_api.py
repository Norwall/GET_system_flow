from __future__ import annotations

import pytest

from get_designer_geometry import (
    DesignerNode,
    DesignerSegment,
    GETScenario,
    SoilConfig,
    SoilLayer,
    SolverConfig,
    ThermalConfig,
    scenario_to_dict,
)


def _api_scenario() -> GETScenario:
    return GETScenario(
        scenario_id="api-case",
        name="API case",
        nodes=(
            DesignerNode(id="n1", x_m=0.0, z_m=-2.0),
            DesignerNode(id="n2", x_m=20.0, z_m=-2.0),
            DesignerNode(id="n3", x_m=20.0, z_m=0.5),
        ),
        segments=(
            DesignerSegment(id="s1", start_node_id="n1", end_node_id="n2", kind="evaporator"),
            DesignerSegment(id="s2", start_node_id="n2", end_node_id="n3", kind="riser"),
        ),
        thermal=ThermalConfig(qtr_W_m=10.0),
        solver=SolverConfig(tcon_C=0.0, mode="worksheet_compatible", closure_model="worksheet_compatible"),
    )


def _api_run_scenario() -> GETScenario:
    return GETScenario(
        scenario_id="api-run-case",
        name="API run case",
        nodes=(
            DesignerNode(id="n1", x_m=0.0, z_m=-2.0),
            DesignerNode(id="n2", x_m=100.0, z_m=-2.0),
            DesignerNode(id="n3", x_m=100.0, z_m=0.5),
            DesignerNode(id="n4", x_m=106.5, z_m=0.5),
            DesignerNode(id="n5", x_m=0.0, z_m=-2.0),
        ),
        segments=(
            DesignerSegment(id="s1", start_node_id="n1", end_node_id="n2", kind="evaporator"),
            DesignerSegment(id="s2", start_node_id="n2", end_node_id="n3", kind="riser"),
            DesignerSegment(id="s3", start_node_id="n3", end_node_id="n4", kind="condenser"),
            DesignerSegment(id="s4", start_node_id="n4", end_node_id="n5", kind="downcomer"),
        ),
        thermal=ThermalConfig(qtr_W_m=10.0),
        solver=SolverConfig(
            tcon_C=0.0,
            mode="worksheet_compatible",
            closure_model="worksheet_compatible",
            fluid="CO2",
            property_backend="mathcad_table",
            regime_model="experimental_regime_aware",
            friction_model="mathcad_compat",
            heat_transfer_model="prescribed_heat_input",
        ),
    )


def _api_wall_coupled_scenario() -> GETScenario:
    scenario = _api_run_scenario()
    return GETScenario(
        scenario_id="api-wall-case",
        name="API wall case",
        nodes=scenario.nodes,
        segments=scenario.segments,
        thermal=ThermalConfig(qtr_W_m=1.0),
        soil=SoilConfig(
            effective_conductance_W_mK=10.0,
            layers=(
                SoilLayer(
                    name="warm-soil",
                    top_z_m=0.0,
                    bottom_z_m=-10.0,
                    initial_temperature_C=5.0,
                ),
            ),
        ),
        solver=SolverConfig(
            tcon_C=0.0,
            mode="worksheet_compatible",
            closure_model="worksheet_compatible",
            fluid="CO2",
            property_backend="mathcad_table",
            regime_model="experimental_regime_aware",
            friction_model="mathcad_compat",
            heat_transfer_model="wall_coupled",
        ),
    )


def test_api_derives_and_saves_scenarios(tmp_path) -> None:
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient

    from get_designer_api import create_app

    client = TestClient(create_app(tmp_path))
    scenario_payload = scenario_to_dict(_api_scenario())

    derive_response = client.post("/api/derive", json=scenario_payload)
    assert derive_response.status_code == 200
    assert derive_response.json()["derived"]["evaporator_length_m"] == pytest.approx(20.0)

    save_response = client.post("/api/scenarios", json=scenario_payload)
    assert save_response.status_code == 200
    assert (tmp_path / "api-case.json").exists()

    list_response = client.get("/api/scenarios")
    assert list_response.status_code == 200
    assert list_response.json()["scenarios"][0]["scenario_id"] == "api-case"


def test_api_run_returns_source_and_limit_diagnostics(tmp_path) -> None:
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient

    from get_designer_api import create_app

    client = TestClient(create_app(tmp_path))

    response = client.post("/api/run", json=scenario_to_dict(_api_run_scenario()))

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["fluid"] == "CO2"
    assert result["property_backend"] == "mathcad_table"
    assert result["regime_model"] == "experimental_regime_aware"
    assert result["friction_model"] == "mathcad_compat"
    assert result["heat_transfer_model"] == "prescribed_heat_input"
    assert "model_source_status" in result
    assert "source_gate_reasons" in result
    assert "failure_class" in result
    assert result["qcrit_status"] == "not_evaluated"
    assert result["dryout_limit"] == "not_evaluated_source_required"


def test_api_run_wall_coupled_returns_derived_boundary_fields(tmp_path) -> None:
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient

    from get_designer_api import create_app

    client = TestClient(create_app(tmp_path))

    response = client.post("/api/run", json=scenario_to_dict(_api_wall_coupled_scenario()))

    assert response.status_code == 200
    derived = response.json()["derived"]
    result = response.json()["result"]
    assert derived["qtr_W_m"] == pytest.approx(50.0)
    assert derived["thermal_boundary_model"] == "wall_soil_effective_conductance"
    assert result["heat_transfer_model"] == "wall_coupled"
    assert result["qtr"] == pytest.approx(50.0)
    assert result["thermal_boundary_model"] == "wall_soil_effective_conductance"
    assert result["wall_soil_qtr_w_m"] == pytest.approx(50.0)
