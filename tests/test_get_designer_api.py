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


def test_api_reports_source_gate_pipeline(tmp_path) -> None:
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient

    from get_designer_api import create_app

    client = TestClient(create_app(tmp_path))

    response = client.get("/api/source-gates")

    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert "policy_documents" in payload
    assert "source_gates" in payload
    assert "milestone_groups" in payload
    assert "parallel_work_orders" in payload
    assert "next_priorities" in payload
    assert "docs/source_gate_unresolved_questions.md" in payload["policy_documents"]
    assert payload["next_priorities"][0]["source_id"] == "HTC-CHEN-1962-SOURCE-CANDIDATE"
    chen_gate = next(
        gate
        for gate in payload["source_gates"]
        if gate["source_id"] == "HTC-CHEN-1962-SOURCE-CANDIDATE"
    )
    assert chen_gate["current_blocking_stage"] == "audit_formulas_and_limits"
    assert chen_gate["audit_stage"] == "formula_scope_audit"
    assert chen_gate["release_basis"] == "technical_report"
    assert chen_gate["allowed_release_bases"] == ["technical_report"]
    assert any(
        criterion["criterion_id"] == "reference_tests"
        and criterion["status"] == "blocked"
        for criterion in chen_gate["release_criteria"]
    )
    groups = {group["group_id"]: group for group in payload["milestone_groups"]}
    assert groups["local_candidate_audit"]["source_ids"] == [
        "HTC-CHEN-1962-SOURCE-CANDIDATE"
    ]
    work_orders = {item["source_id"]: item for item in payload["parallel_work_orders"]}
    assert work_orders["HTC-CHEN-1962-SOURCE-CANDIDATE"]["audit_stage"] == "formula_scope_audit"


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


def test_api_critical_loads_is_explicit_endpoint(tmp_path) -> None:
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient

    from get_designer_api import create_app

    client = TestClient(create_app(tmp_path))
    payload = scenario_to_dict(_api_run_scenario())
    payload["critical_loads"] = {
        "qtr_min_w_m": 0.0,
        "qtr_max_w_m": 12.0,
        "qtr_step_w_m": 6.0,
        "boundary_tolerance_w_m": 1.0,
        "nsamp": 6,
        "ngrid": 12,
    }

    response = client.post("/api/critical-loads", json=payload)

    assert response.status_code == 200
    report = response.json()["critical_loads"]
    assert report["qcrit_model"] == "dissertation_scan_plus_f_zero"
    assert report["qcrit_status"] in {"evaluated", "partial", "failed"}
    assert report["qtr_max_w_m"] == pytest.approx(12.0)
    assert report["n_scan_points"] > 0
