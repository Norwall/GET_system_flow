from __future__ import annotations

from pathlib import Path
from typing import Any

from get_designer_geometry import (
    DEFAULT_SCENARIO_DIR,
    ScenarioValidationError,
    critical_loads_from_scenario,
    default_scenario,
    derive_geometry,
    derived_geometry_to_dict,
    list_scenario_files,
    load_scenario,
    run_scenario,
    safe_scenario_id,
    save_scenario,
    scenario_from_dict,
    scenario_to_dict,
)
from source_gate_pipeline import source_gate_report


def create_app(scenario_directory: Path = DEFAULT_SCENARIO_DIR) -> Any:
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:
        raise RuntimeError("Install the web extra: python -m pip install -e .[web]") from exc

    app = FastAPI(title="GET Designer API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/scenarios")
    def list_scenarios() -> dict[str, Any]:
        scenarios = []
        for path in list_scenario_files(scenario_directory):
            try:
                scenario = load_scenario(path)
            except (OSError, ValueError):
                continue
            scenarios.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "name": scenario.name,
                    "path": str(path),
                }
            )
        return {"scenarios": scenarios}

    @app.get("/api/source-gates")
    def source_gates_endpoint() -> dict[str, Any]:
        return source_gate_report(Path(__file__).resolve().parent)

    @app.get("/api/scenarios/demo")
    def get_demo_scenario() -> dict[str, Any]:
        scenario = default_scenario()
        return {
            "scenario": scenario_to_dict(scenario),
            "derived": derived_geometry_to_dict(derive_geometry(scenario)),
        }

    @app.get("/api/scenarios/{scenario_id}")
    def get_scenario(scenario_id: str) -> dict[str, Any]:
        path = scenario_directory / f"{safe_scenario_id(scenario_id)}.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Scenario not found.")
        try:
            scenario = load_scenario(path)
            derived = derive_geometry(scenario)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"scenario": scenario_to_dict(scenario), "derived": derived_geometry_to_dict(derived)}

    @app.post("/api/scenarios")
    def save_scenario_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            scenario = scenario_from_dict(payload)
            path = save_scenario(scenario, scenario_directory)
            derived = derive_geometry(scenario)
        except (OSError, ScenarioValidationError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "scenario": scenario_to_dict(scenario),
            "derived": derived_geometry_to_dict(derived),
            "path": str(path),
        }

    @app.post("/api/derive")
    def derive_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            scenario = scenario_from_dict(payload)
            derived = derive_geometry(scenario)
        except ScenarioValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "scenario": scenario_to_dict(scenario),
            "derived": derived_geometry_to_dict(derived),
        }

    @app.post("/api/run")
    def run_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            scenario = scenario_from_dict(payload)
            derived = derive_geometry(scenario)
            result = run_scenario(scenario)
        except ScenarioValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "scenario": scenario_to_dict(scenario),
            "derived": derived_geometry_to_dict(derived),
            "result": result.to_dict(),
        }

    @app.post("/api/critical-loads")
    def critical_loads_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            scenario = scenario_from_dict(payload)
            derived = derive_geometry(scenario)
            options = _critical_load_options(payload.get("critical_loads", {}))
            report = critical_loads_from_scenario(scenario, **options)
        except ScenarioValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "scenario": scenario_to_dict(scenario),
            "derived": derived_geometry_to_dict(derived),
            "critical_loads": report.to_dict(),
        }

    web_dist = Path(__file__).resolve().parent / "web" / "dist"
    if web_dist.exists():
        app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")

    return app


def _critical_load_options(data: Any) -> dict[str, Any]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ScenarioValidationError("critical_loads must be an object when provided.")
    allowed = {
        "qtr_min_w_m",
        "qtr_max_w_m",
        "qtr_step_w_m",
        "boundary_tolerance_w_m",
        "fmin",
        "fmax",
        "nsamp",
        "ngrid",
    }
    unexpected = sorted(set(data) - allowed)
    if unexpected:
        raise ScenarioValidationError(f"Unsupported critical-load option(s): {unexpected!r}.")
    return {key: data[key] for key in allowed if key in data}


try:
    app = create_app()
except RuntimeError:
    app = None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
