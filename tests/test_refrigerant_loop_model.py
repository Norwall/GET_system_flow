from __future__ import annotations

import pytest

from co2_results import SteadyLoopResult
from refrigerant_loop_model import RefrigerantLoopModel


def test_refrigerant_loop_model_runs_co2_coolprop_with_published_defaults() -> None:
    model = RefrigerantLoopModel(fluid="R744", property_backend="coolprop")
    result = model.run_result(H=2.5, qtr=40.0, Li=200.0, tcon=0.0)
    data = result.to_dict()

    assert isinstance(result, SteadyLoopResult)
    assert result.converged is True
    assert data["fluid"] == "CO2"
    assert data["fluid_cas"] == "124-38-9"
    assert data["refrigerant_name"] == "CarbonDioxide"
    assert data["property_backend"] == "coolprop"
    assert data["property_model_name"] == "CoolPropSaturationProperties"
    assert data["model_scientific_status"] == "published"
    assert data["regime_model"] == "published_regime_map"
    assert data["regime_model_scientific_status"] == "published"
    assert data["regime_model_source_status"] == "source_required"
    assert data["friction_model"] == "colebrook_white"
    assert data["heat_transfer_model"] == "prescribed_heat_input"
    assert data["boiling_heat_transfer_status"] == "diagnostic_only_source_required"
    assert "source_required" in data["evaporator_flow_regime_status_summary"]
    assert "Wojtan" in data["evaporator_flow_regime_source_summary"]
    assert "zivi" in data["closure_name"]
    assert data["fff"] == pytest.approx(0.61331227093134, rel=1e-9)


def test_refrigerant_loop_model_solve_f_uses_same_facade_defaults() -> None:
    model = RefrigerantLoopModel(fluid="CO2", property_backend="coolprop")

    circulation_factor = model.solve_f(H=2.5, qtr=40.0, Li=200.0, tcon=0.0, nsamp=40)

    assert circulation_factor == pytest.approx(0.61331227093134, rel=1e-9)
