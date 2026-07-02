from __future__ import annotations

from typing import Any

from co2_geometry import LoopGeometry
from co2_results import SteadyLoopResult
from co2_steady_solver import SteadyLoopInputs, SteadyLoopSolver
from refrigerant_properties import RefrigerantSaturationProperties, create_saturation_properties


class RefrigerantLoopModel:
    """Fluid-agnostic facade for the steady natural-circulation loop solver."""

    def __init__(
        self,
        fluid: str = "CO2",
        property_backend: str = "coolprop",
        geometry: LoopGeometry | None = None,
        allow_property_extrapolation: bool = False,
        properties: RefrigerantSaturationProperties | None = None,
    ) -> None:
        self.geometry = geometry if geometry is not None else LoopGeometry()
        self.properties = (
            properties
            if properties is not None
            else create_saturation_properties(
                fluid=fluid,
                property_backend=property_backend,
                allow_property_extrapolation=allow_property_extrapolation,
            )
        )
        self.steady_solver = SteadyLoopSolver(geometry=self.geometry, properties=self.properties)

    @property
    def fluid(self) -> str:
        return self.properties.fluid

    @property
    def property_backend(self) -> str:
        return self.properties.property_backend

    def _inputs(
        self,
        H: float,
        qtr: float,
        Li: float,
        tcon: float,
        mode: str,
        closure_model: str,
        friction_model: str,
        geometry: LoopGeometry | None,
        heat_transfer_model: str,
    ) -> SteadyLoopInputs:
        return SteadyLoopInputs(
            H=H,
            qtr=qtr,
            Li=Li,
            tcon=tcon,
            mode=mode,
            closure_model=closure_model,
            friction_model=friction_model,
            geometry=geometry,
            heat_transfer_model=heat_transfer_model,
        )

    def run_result(
        self,
        H: float,
        qtr: float,
        Li: float,
        tcon: float,
        mode: str = "worksheet_compatible",
        closure_model: str = "zivi",
        friction_model: str = "colebrook_white",
        geometry: LoopGeometry | None = None,
        heat_transfer_model: str = "prescribed_heat_input",
    ) -> SteadyLoopResult:
        """Return a structured result for the configured refrigerant."""

        return self.steady_solver.solve(
            self._inputs(
                H=H,
                qtr=qtr,
                Li=Li,
                tcon=tcon,
                mode=mode,
                closure_model=closure_model,
                friction_model=friction_model,
                geometry=geometry,
                heat_transfer_model=heat_transfer_model,
            )
        )

    def run(
        self,
        H: float,
        qtr: float,
        Li: float,
        tcon: float,
        mode: str = "worksheet_compatible",
        closure_model: str = "zivi",
        friction_model: str = "colebrook_white",
        geometry: LoopGeometry | None = None,
        heat_transfer_model: str = "prescribed_heat_input",
    ) -> dict[str, Any]:
        """Return a dictionary result for compatibility with reporting code."""

        return self.run_result(
            H=H,
            qtr=qtr,
            Li=Li,
            tcon=tcon,
            mode=mode,
            closure_model=closure_model,
            friction_model=friction_model,
            geometry=geometry,
            heat_transfer_model=heat_transfer_model,
        ).to_dict()

    def solve_f(
        self,
        H: float,
        qtr: float,
        Li: float,
        tcon: float,
        fmin: float = 1e-6,
        fmax: float = 200.0,
        nsamp: int = 220,
        mode: str = "worksheet_compatible",
        closure_model: str = "zivi",
        friction_model: str = "colebrook_white",
        geometry: LoopGeometry | None = None,
        heat_transfer_model: str = "prescribed_heat_input",
    ) -> float | None:
        """Return the circulation factor if the head-balance root is bracketed."""

        root_search = self.steady_solver.find_circulation_factor(
            inputs=self._inputs(
                H=H,
                qtr=qtr,
                Li=Li,
                tcon=tcon,
                mode=mode,
                closure_model=closure_model,
                friction_model=friction_model,
                geometry=geometry,
                heat_transfer_model=heat_transfer_model,
            ),
            fmin=fmin,
            fmax=fmax,
            nsamp=nsamp,
        )
        return root_search.circulation_factor


__all__ = ["RefrigerantLoopModel"]
