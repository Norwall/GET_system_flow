from __future__ import annotations

import pytest

from get_designer_geometry import (
    DesignerNode,
    DesignerSegment,
    GETScenario,
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
