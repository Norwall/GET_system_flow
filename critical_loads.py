from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Callable, Literal

from scipy.optimize import root_scalar

from boiling_heat_transfer import WALL_COUPLED, WallSoilBoundary, normalize_heat_transfer_model
from co2_geometry import LoopGeometry
from co2_steady_solver import SteadyLoopInputs, SteadyLoopSolver
from refrigerant_properties import PropertyRangeError


QCRIT_MODEL = "dissertation_scan_plus_f_zero"
QCRIT_SOURCE_SCAN = "QCRIT-DISSERTATION-SCAN"
QCRIT_SOURCE_F_ZERO = "QCRIT-DISSERTATION-F-ZERO"

QcritPointStatus = Literal[
    "working",
    "no_boiling",
    "no_root",
    "multiple_roots",
    "f_to_zero_limit",
    "dryout_limit",
    "property_out_of_range",
    "near_critical_region",
    "numerical_failure",
    "validation_error",
]


@dataclass(frozen=True)
class CriticalLoadConfig:
    H: float
    Li: float
    tcon: float
    mode: str = "worksheet_compatible"
    closure_model: str = "worksheet_compatible"
    regime_model: str = "experimental_regime_aware"
    friction_model: str = "mathcad_compat"
    geometry: LoopGeometry | None = None
    heat_transfer_model: str = "prescribed_heat_input"
    wall_soil_boundary: WallSoilBoundary | None = None
    qtr_min_w_m: float = 0.0
    qtr_max_w_m: float = 150.0
    qtr_step_w_m: float = 1.0
    boundary_tolerance_w_m: float = 0.01
    fmin: float = 1.0e-8
    fmax: float = 1.0e5
    nsamp: int = 220
    ngrid: int = 240
    f_zero_tolerance: float = 1.0e-6
    quality_tolerance: float = 1.0e-6
    void_fraction_tolerance: float = 1.0e-6
    max_qtr_extensions: int = 2
    qtr_extension_factor: float = 1.5

    def validate(self) -> None:
        if not math.isfinite(self.H):
            raise ValueError("H must be finite.")
        if not math.isfinite(self.Li) or self.Li <= 0.0:
            raise ValueError("Li must be a positive finite value.")
        if not math.isfinite(self.tcon):
            raise ValueError("tcon must be finite.")
        if self.qtr_min_w_m < 0.0:
            raise ValueError("qtr_min_w_m must be non-negative.")
        if self.qtr_max_w_m <= self.qtr_min_w_m:
            raise ValueError("qtr_max_w_m must be greater than qtr_min_w_m.")
        if self.qtr_step_w_m <= 0.0:
            raise ValueError("qtr_step_w_m must be positive.")
        if self.boundary_tolerance_w_m <= 0.0:
            raise ValueError("boundary_tolerance_w_m must be positive.")
        if self.fmin <= 0.0 or self.fmax <= self.fmin:
            raise ValueError("fmin and fmax must define a positive increasing interval.")
        if self.nsamp < 3:
            raise ValueError("nsamp must be at least 3.")
        if self.ngrid < 10:
            raise ValueError("ngrid must be at least 10.")
        if self.max_qtr_extensions < 0:
            raise ValueError("max_qtr_extensions must be non-negative.")
        if self.qtr_extension_factor <= 1.0:
            raise ValueError("qtr_extension_factor must be greater than 1.")

    def steady_inputs(self, qtr: float) -> SteadyLoopInputs:
        return SteadyLoopInputs(
            H=self.H,
            qtr=qtr,
            Li=self.Li,
            tcon=self.tcon,
            mode=self.mode,
            closure_model=self.closure_model,
            regime_model=self.regime_model,
            friction_model=self.friction_model,
            geometry=self.geometry,
            heat_transfer_model=self.heat_transfer_model,
            wall_soil_boundary=self.wall_soil_boundary,
        )


@dataclass(frozen=True)
class CriticalLoadPoint:
    qtr_w_m: float
    status: QcritPointStatus
    solver_status: str = ""
    failure_reason: str | None = None
    failure_class: str = "none"
    circulation_factor: float | None = None
    root_bracket: tuple[float, float] | None = None
    n_sign_changes: int = 0
    head_residual_m: float | None = None
    required_head_m: float | None = None
    boiling_length_m: float | None = None
    outlet_mass_quality: float | None = None
    outlet_void_fraction: float | None = None
    source_formula_id: str = QCRIT_SOURCE_SCAN

    @property
    def is_working_solution(self) -> bool:
        return self.status == "working"

    def to_dict(self) -> dict[str, object]:
        return {
            "qtr_w_m": self.qtr_w_m,
            "status": self.status,
            "solver_status": self.solver_status,
            "failure_reason": self.failure_reason,
            "failure_class": self.failure_class,
            "circulation_factor": self.circulation_factor,
            "root_bracket": self.root_bracket,
            "n_sign_changes": self.n_sign_changes,
            "head_residual_m": self.head_residual_m,
            "required_head_m": self.required_head_m,
            "boiling_length_m": self.boiling_length_m,
            "outlet_mass_quality": self.outlet_mass_quality,
            "outlet_void_fraction": self.outlet_void_fraction,
            "source_formula_id": self.source_formula_id,
        }


@dataclass(frozen=True)
class CriticalLoadBoundary:
    boundary: str
    qtr_w_m: float | None
    status: str
    source_formula_id: str
    lower_bracket_w_m: float | None = None
    upper_bracket_w_m: float | None = None
    point: CriticalLoadPoint | None = None
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "boundary": self.boundary,
            "qtr_w_m": self.qtr_w_m,
            "status": self.status,
            "source_formula_id": self.source_formula_id,
            "lower_bracket_w_m": self.lower_bracket_w_m,
            "upper_bracket_w_m": self.upper_bracket_w_m,
            "point": self.point.to_dict() if self.point is not None else None,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True)
class CriticalLoadReport:
    qcrit_model: str
    qcrit_status: str
    config: CriticalLoadConfig
    lower_critical_load: CriticalLoadBoundary
    upper_scan_load: CriticalLoadBoundary
    upper_f_zero_load: CriticalLoadBoundary
    scan_points: tuple[CriticalLoadPoint, ...]
    fluid: str = ""
    property_backend: str = ""
    property_source: str = ""
    warnings: tuple[str, ...] = ()

    @property
    def lower_critical_load_w_m(self) -> float | None:
        return self.lower_critical_load.qtr_w_m

    @property
    def upper_critical_load_w_m(self) -> float | None:
        if self.upper_f_zero_load.qtr_w_m is not None:
            return self.upper_f_zero_load.qtr_w_m
        return self.upper_scan_load.qtr_w_m

    def to_dict(self) -> dict[str, object]:
        return {
            "qcrit_model": self.qcrit_model,
            "qcrit_status": self.qcrit_status,
            "fluid": self.fluid,
            "property_backend": self.property_backend,
            "property_source": self.property_source,
            "H": self.config.H,
            "Li": self.config.Li,
            "tcon": self.config.tcon,
            "mode": self.config.mode,
            "closure_model": self.config.closure_model,
            "friction_model": self.config.friction_model,
            "qtr_min_w_m": self.config.qtr_min_w_m,
            "qtr_max_w_m": self.config.qtr_max_w_m,
            "qtr_step_w_m": self.config.qtr_step_w_m,
            "lower_critical_load_w_m": self.lower_critical_load_w_m,
            "upper_critical_load_w_m": self.upper_critical_load_w_m,
            "lower_critical_load": self.lower_critical_load.to_dict(),
            "upper_scan_load": self.upper_scan_load.to_dict(),
            "upper_f_zero_load": self.upper_f_zero_load.to_dict(),
            "n_scan_points": len(self.scan_points),
            "scan_points": [point.to_dict() for point in self.scan_points],
            "warnings": list(self.warnings),
        }


Evaluator = Callable[[float], CriticalLoadPoint]
ResidualEvaluator = Callable[[float], float | None]


class CriticalLoadSolver:
    def __init__(self, steady_solver: SteadyLoopSolver, config: CriticalLoadConfig) -> None:
        config.validate()
        self.steady_solver = steady_solver
        self.config = config

    def solve(self) -> CriticalLoadReport:
        return find_critical_loads(
            evaluate=self.evaluate_qtr,
            f_zero_residual=self.f_zero_residual,
            f_zero_point=self.evaluate_f_zero_qtr,
            config=self.config,
            fluid=getattr(self.steady_solver.properties, "fluid", ""),
            property_backend=getattr(self.steady_solver.properties, "property_backend", ""),
            property_source=getattr(self.steady_solver.properties, "property_source", ""),
        )

    def evaluate_qtr(self, qtr_w_m: float) -> CriticalLoadPoint:
        qtr = float(qtr_w_m)
        if not math.isfinite(qtr) or qtr < 0.0:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="validation_error",
                solver_status="validation_error",
                failure_reason="qtr must be a non-negative finite value.",
                failure_class="validation_error",
            )
        if qtr == 0.0:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="no_boiling",
                solver_status="no_boiling",
                failure_reason="Zero heat input cannot produce a boiling section.",
                failure_class="hydrodynamic_limit",
            )
        if self.config.H <= 0.0:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="no_root",
                solver_status="no_driving_head",
                failure_reason="No positive hydrostatic driving head is available.",
                failure_class="hydrodynamic_limit",
            )

        try:
            heat_transfer_model = normalize_heat_transfer_model(self.config.heat_transfer_model)
        except ValueError as exc:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="validation_error",
                solver_status="validation_error",
                failure_reason=str(exc),
                failure_class="validation_error",
            )
        if heat_transfer_model == WALL_COUPLED:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="validation_error",
                solver_status="validation_error",
                failure_reason=(
                    "wall_coupled qcrit is not supported by the prescribed-qtr sweep; "
                    "run the steady solver with wall_soil_boundary or scan boundary parameters explicitly."
                ),
                failure_class="validation_error",
            )

        inputs = self.config.steady_inputs(qtr)
        property_fields = self.steady_solver.property_result_fields(inputs)
        near_critical_warning = property_fields.get("near_critical_warning", "")
        if near_critical_warning:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="near_critical_region",
                solver_status="near_critical_region",
                failure_reason=near_critical_warning,
                failure_class="property_limit",
            )
        try:
            self.steady_solver.properties.state_at_temperature(self.config.tcon)
        except PropertyRangeError as exc:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="property_out_of_range",
                solver_status="property_out_of_range",
                failure_reason=str(exc),
                failure_class="property_limit",
            )

        try:
            root_search = self.steady_solver.find_circulation_factor(
                inputs=inputs,
                fmin=self.config.fmin,
                fmax=self.config.fmax,
                nsamp=self.config.nsamp,
            )
        except Exception as exc:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="numerical_failure",
                solver_status="root_search_exception",
                failure_reason=str(exc),
                failure_class="numerical_failure",
            )

        if root_search.n_sign_changes > 1:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="multiple_roots",
                solver_status="multiple_roots",
                failure_reason="More than one circulation-factor root was detected.",
                failure_class="hydrodynamic_limit",
                circulation_factor=root_search.circulation_factor,
                root_bracket=root_search.root_bracket,
                n_sign_changes=root_search.n_sign_changes,
            )
        if root_search.circulation_factor is None:
            return self._point_from_root_failure(qtr, root_search.solver_status, root_search.failure_reason)

        try:
            pass_result = self.steady_solver.one_pass(
                inputs=inputs,
                circulation_factor=root_search.circulation_factor,
                ngrid=self.config.ngrid,
            )
        except PropertyRangeError as exc:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="property_out_of_range",
                solver_status="property_out_of_range",
                failure_reason=str(exc),
                failure_class="property_limit",
                circulation_factor=root_search.circulation_factor,
                root_bracket=root_search.root_bracket,
                n_sign_changes=root_search.n_sign_changes,
            )
        except Exception as exc:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="numerical_failure",
                solver_status="one_pass_exception",
                failure_reason=str(exc),
                failure_class="numerical_failure",
                circulation_factor=root_search.circulation_factor,
                root_bracket=root_search.root_bracket,
                n_sign_changes=root_search.n_sign_changes,
            )
        if pass_result is None:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="no_boiling",
                solver_status="no_boiling",
                failure_reason="No finite steady pass exists; the boiling section may be absent.",
                failure_class="hydrodynamic_limit",
                circulation_factor=root_search.circulation_factor,
                root_bracket=root_search.root_bracket,
                n_sign_changes=root_search.n_sign_changes,
            )

        status: QcritPointStatus = "working"
        failure_reason = None
        failure_class = "none"
        if pass_result.boiling_length_m <= self.config.boundary_tolerance_w_m:
            status = "no_boiling"
            failure_reason = "Boiling section length is effectively zero."
            failure_class = "hydrodynamic_limit"
        elif (
            root_search.circulation_factor <= self.config.f_zero_tolerance
            or pass_result.outlet_mass_quality >= 1.0 - self.config.quality_tolerance
            or pass_result.outlet_gas_volume_fraction_closure >= 1.0 - self.config.void_fraction_tolerance
        ):
            status = "f_to_zero_limit"
            failure_reason = "The solution is at the f -> 0 upper critical limit."
            failure_class = "hydrodynamic_limit"

        return CriticalLoadPoint(
            qtr_w_m=qtr,
            status=status,
            solver_status="converged",
            failure_reason=failure_reason,
            failure_class=failure_class,
            circulation_factor=root_search.circulation_factor,
            root_bracket=root_search.root_bracket,
            n_sign_changes=root_search.n_sign_changes,
            head_residual_m=pass_result.required_head_m - self.config.H,
            required_head_m=pass_result.required_head_m,
            boiling_length_m=pass_result.boiling_length_m,
            outlet_mass_quality=pass_result.outlet_mass_quality,
            outlet_void_fraction=pass_result.outlet_gas_volume_fraction_closure,
        )

    def f_zero_residual(self, qtr_w_m: float) -> float | None:
        qtr = float(qtr_w_m)
        if not math.isfinite(qtr) or qtr <= 0.0:
            return None
        inputs = self.config.steady_inputs(qtr)
        try:
            pass_result = self.steady_solver.one_pass(
                inputs=inputs,
                circulation_factor=0.0,
                ngrid=self.config.ngrid,
            )
        except (PropertyRangeError, ValueError):
            return None
        if pass_result is None or not math.isfinite(pass_result.required_head_m):
            return None
        return pass_result.required_head_m - self.config.H

    def evaluate_f_zero_qtr(self, qtr_w_m: float) -> CriticalLoadPoint:
        qtr = float(qtr_w_m)
        inputs = self.config.steady_inputs(qtr)
        try:
            pass_result = self.steady_solver.one_pass(
                inputs=inputs,
                circulation_factor=0.0,
                ngrid=self.config.ngrid,
            )
        except PropertyRangeError as exc:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="property_out_of_range",
                solver_status="property_out_of_range",
                failure_reason=str(exc),
                failure_class="property_limit",
                circulation_factor=0.0,
                source_formula_id=QCRIT_SOURCE_F_ZERO,
            )
        except Exception as exc:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="numerical_failure",
                solver_status="f_zero_pass_exception",
                failure_reason=str(exc),
                failure_class="numerical_failure",
                circulation_factor=0.0,
                source_formula_id=QCRIT_SOURCE_F_ZERO,
            )
        if pass_result is None:
            return CriticalLoadPoint(
                qtr_w_m=qtr,
                status="no_boiling",
                solver_status="no_boiling",
                failure_reason="No finite f=0 pass exists.",
                failure_class="hydrodynamic_limit",
                circulation_factor=0.0,
                source_formula_id=QCRIT_SOURCE_F_ZERO,
            )
        return CriticalLoadPoint(
            qtr_w_m=qtr,
            status="f_to_zero_limit",
            solver_status="f_zero_limit",
            failure_reason="Upper critical limit evaluated with f=0.",
            failure_class="hydrodynamic_limit",
            circulation_factor=0.0,
            head_residual_m=pass_result.required_head_m - self.config.H,
            required_head_m=pass_result.required_head_m,
            boiling_length_m=pass_result.boiling_length_m,
            outlet_mass_quality=pass_result.outlet_mass_quality,
            outlet_void_fraction=pass_result.outlet_gas_volume_fraction_closure,
            source_formula_id=QCRIT_SOURCE_F_ZERO,
        )

    def _point_from_root_failure(
        self,
        qtr_w_m: float,
        solver_status: str,
        failure_reason: str | None,
    ) -> CriticalLoadPoint:
        if solver_status == "property_out_of_range":
            status: QcritPointStatus = "property_out_of_range"
            failure_class = "property_limit"
        elif solver_status == "no_root_bracket":
            status = "no_root"
            failure_class = "numerical_failure"
        else:
            status = "numerical_failure"
            failure_class = "numerical_failure"
        return CriticalLoadPoint(
            qtr_w_m=qtr_w_m,
            status=status,
            solver_status=solver_status,
            failure_reason=failure_reason,
            failure_class=failure_class,
        )


def solve_critical_loads(
    steady_solver: SteadyLoopSolver,
    *,
    H: float,
    Li: float,
    tcon: float,
    mode: str = "worksheet_compatible",
    closure_model: str = "worksheet_compatible",
    regime_model: str = "experimental_regime_aware",
    friction_model: str = "mathcad_compat",
    geometry: LoopGeometry | None = None,
    heat_transfer_model: str = "prescribed_heat_input",
    wall_soil_boundary: WallSoilBoundary | None = None,
    qtr_min_w_m: float = 0.0,
    qtr_max_w_m: float = 150.0,
    qtr_step_w_m: float = 1.0,
    boundary_tolerance_w_m: float = 0.01,
    fmin: float = 1.0e-8,
    fmax: float = 1.0e5,
    nsamp: int = 220,
    ngrid: int = 240,
) -> CriticalLoadReport:
    config = CriticalLoadConfig(
        H=H,
        Li=Li,
        tcon=tcon,
        mode=mode,
        closure_model=closure_model,
        regime_model=regime_model,
        friction_model=friction_model,
        geometry=geometry,
        heat_transfer_model=heat_transfer_model,
        wall_soil_boundary=wall_soil_boundary,
        qtr_min_w_m=qtr_min_w_m,
        qtr_max_w_m=qtr_max_w_m,
        qtr_step_w_m=qtr_step_w_m,
        boundary_tolerance_w_m=boundary_tolerance_w_m,
        fmin=fmin,
        fmax=fmax,
        nsamp=nsamp,
        ngrid=ngrid,
    )
    return CriticalLoadSolver(steady_solver=steady_solver, config=config).solve()


def find_critical_loads(
    *,
    evaluate: Evaluator,
    f_zero_residual: ResidualEvaluator,
    f_zero_point: Evaluator | None = None,
    config: CriticalLoadConfig,
    fluid: str = "",
    property_backend: str = "",
    property_source: str = "",
) -> CriticalLoadReport:
    config.validate()
    scan_points = _scan_points_with_extensions(evaluate, config)
    lower = _lower_boundary(evaluate, config, scan_points)
    upper_scan = _upper_scan_boundary(evaluate, config, scan_points)
    upper_f_zero = _upper_f_zero_boundary(
        f_zero_point or evaluate,
        f_zero_residual,
        config,
    )
    warnings = _report_warnings(config, upper_scan, upper_f_zero)
    qcrit_status = _report_status(lower, upper_scan, upper_f_zero)
    return CriticalLoadReport(
        qcrit_model=QCRIT_MODEL,
        qcrit_status=qcrit_status,
        config=config,
        lower_critical_load=lower,
        upper_scan_load=upper_scan,
        upper_f_zero_load=upper_f_zero,
        scan_points=tuple(scan_points),
        fluid=fluid,
        property_backend=property_backend,
        property_source=property_source,
        warnings=warnings,
    )


def _scan_points_with_extensions(evaluate: Evaluator, config: CriticalLoadConfig) -> list[CriticalLoadPoint]:
    points: list[CriticalLoadPoint] = []
    qtr_max = config.qtr_max_w_m
    extensions = 0
    while True:
        start = config.qtr_min_w_m if not points else points[-1].qtr_w_m + config.qtr_step_w_m
        points.extend(evaluate(qtr) for qtr in _qtr_grid(start, qtr_max, config.qtr_step_w_m))
        if not points:
            break
        has_working = any(point.is_working_solution for point in points)
        high_side_failure = has_working and any(
            not point.is_working_solution for point in points[_last_working_index(points) + 1 :]
        )
        if high_side_failure or not has_working or extensions >= config.max_qtr_extensions:
            break
        if points[-1].is_working_solution:
            qtr_max *= config.qtr_extension_factor
            extensions += 1
            continue
        break
    return points


def _lower_boundary(
    evaluate: Evaluator,
    config: CriticalLoadConfig,
    points: list[CriticalLoadPoint],
) -> CriticalLoadBoundary:
    for index, point in enumerate(points):
        if not point.is_working_solution:
            continue
        if index == 0:
            return CriticalLoadBoundary(
                boundary="lower",
                qtr_w_m=None,
                status="not_bracketed_low",
                source_formula_id=QCRIT_SOURCE_SCAN,
                failure_reason="The first scanned point is already a working solution.",
            )
        lower = points[index - 1]
        refined = _refine_boundary(
            evaluate=evaluate,
            config=config,
            low=lower,
            high=point,
            working_on_high=True,
        )
        return CriticalLoadBoundary(
            boundary="lower",
            qtr_w_m=refined.qtr_w_m,
            status="evaluated",
            source_formula_id=QCRIT_SOURCE_SCAN,
            lower_bracket_w_m=lower.qtr_w_m,
            upper_bracket_w_m=point.qtr_w_m,
            point=refined,
        )
    return CriticalLoadBoundary(
        boundary="lower",
        qtr_w_m=None,
        status="no_working_solution",
        source_formula_id=QCRIT_SOURCE_SCAN,
        failure_reason="No working solution was found in the scanned interval.",
    )


def _upper_scan_boundary(
    evaluate: Evaluator,
    config: CriticalLoadConfig,
    points: list[CriticalLoadPoint],
) -> CriticalLoadBoundary:
    last_working = None
    for point in points:
        if point.is_working_solution:
            last_working = point
            continue
        if last_working is not None:
            refined = _refine_boundary(
                evaluate=evaluate,
                config=config,
                low=last_working,
                high=point,
                working_on_high=False,
            )
            return CriticalLoadBoundary(
                boundary="upper_scan",
                qtr_w_m=refined.qtr_w_m,
                status="evaluated",
                source_formula_id=QCRIT_SOURCE_SCAN,
                lower_bracket_w_m=last_working.qtr_w_m,
                upper_bracket_w_m=point.qtr_w_m,
                point=refined,
            )
    return CriticalLoadBoundary(
        boundary="upper_scan",
        qtr_w_m=None,
        status="not_bracketed_high",
        source_formula_id=QCRIT_SOURCE_SCAN,
        failure_reason="The scan did not find a high-side failure after a working interval.",
    )


def _upper_f_zero_boundary(
    evaluate: Evaluator,
    f_zero_residual: ResidualEvaluator,
    config: CriticalLoadConfig,
) -> CriticalLoadBoundary:
    previous_qtr = None
    previous_residual = None
    qtr_max = config.qtr_max_w_m
    for _ in range(config.max_qtr_extensions + 1):
        for qtr in _qtr_grid(config.qtr_min_w_m, qtr_max, config.qtr_step_w_m):
            residual = f_zero_residual(qtr)
            if residual is None or not math.isfinite(residual):
                continue
            if previous_qtr is not None and previous_residual is not None:
                if residual == 0.0:
                    return _f_zero_boundary_from_qtr(evaluate, qtr, previous_qtr, qtr)
                if previous_residual == 0.0 or previous_residual * residual < 0.0:
                    try:
                        solution = root_scalar(
                            lambda value: _residual_or_nan(f_zero_residual, value),
                            bracket=[previous_qtr, qtr],
                            method="brentq",
                            xtol=config.boundary_tolerance_w_m,
                            rtol=1.0e-10,
                        )
                    except ValueError as exc:
                        return CriticalLoadBoundary(
                            boundary="upper_f_zero",
                            qtr_w_m=None,
                            status="numerical_failure",
                            source_formula_id=QCRIT_SOURCE_F_ZERO,
                            lower_bracket_w_m=previous_qtr,
                            upper_bracket_w_m=qtr,
                            failure_reason=str(exc),
                        )
                    if solution.converged:
                        return _f_zero_boundary_from_qtr(evaluate, float(solution.root), previous_qtr, qtr)
            previous_qtr = qtr
            previous_residual = residual
        qtr_max *= config.qtr_extension_factor
    return CriticalLoadBoundary(
        boundary="upper_f_zero",
        qtr_w_m=None,
        status="not_bracketed",
        source_formula_id=QCRIT_SOURCE_F_ZERO,
        failure_reason="No sign change was found for Hy(q, f=0) - H.",
    )


def _f_zero_boundary_from_qtr(
    evaluate: Evaluator,
    qtr: float,
    lower_bracket: float,
    upper_bracket: float,
) -> CriticalLoadBoundary:
    point = evaluate(qtr)
    point = replace(
        point,
        status="f_to_zero_limit",
        circulation_factor=0.0,
        source_formula_id=QCRIT_SOURCE_F_ZERO,
    )
    return CriticalLoadBoundary(
        boundary="upper_f_zero",
        qtr_w_m=qtr,
        status="evaluated",
        source_formula_id=QCRIT_SOURCE_F_ZERO,
        lower_bracket_w_m=lower_bracket,
        upper_bracket_w_m=upper_bracket,
        point=point,
    )


def _refine_boundary(
    *,
    evaluate: Evaluator,
    config: CriticalLoadConfig,
    low: CriticalLoadPoint,
    high: CriticalLoadPoint,
    working_on_high: bool,
) -> CriticalLoadPoint:
    low_qtr = low.qtr_w_m
    high_qtr = high.qtr_w_m
    best = high if working_on_high else low
    while abs(high_qtr - low_qtr) > config.boundary_tolerance_w_m:
        mid_qtr = 0.5 * (low_qtr + high_qtr)
        mid = evaluate(mid_qtr)
        if mid.is_working_solution:
            best = mid
            if working_on_high:
                high_qtr = mid_qtr
            else:
                low_qtr = mid_qtr
        else:
            if working_on_high:
                low_qtr = mid_qtr
            else:
                high_qtr = mid_qtr
    return best


def _qtr_grid(start: float, stop: float, step: float) -> tuple[float, ...]:
    values = []
    current = float(start)
    while current <= stop + step * 1.0e-9:
        values.append(round(current, 12))
        current += step
    return tuple(values)


def _last_working_index(points: list[CriticalLoadPoint]) -> int:
    for index in range(len(points) - 1, -1, -1):
        if points[index].is_working_solution:
            return index
    return -1


def _residual_or_nan(f_zero_residual: ResidualEvaluator, qtr: float) -> float:
    residual = f_zero_residual(qtr)
    if residual is None:
        return float("nan")
    return residual


def _report_warnings(
    config: CriticalLoadConfig,
    upper_scan: CriticalLoadBoundary,
    upper_f_zero: CriticalLoadBoundary,
) -> tuple[str, ...]:
    warnings = []
    if upper_scan.qtr_w_m is not None and upper_f_zero.qtr_w_m is not None:
        mismatch = abs(upper_scan.qtr_w_m - upper_f_zero.qtr_w_m)
        threshold = max(config.qtr_step_w_m, config.boundary_tolerance_w_m)
        if mismatch > threshold:
            warnings.append(
                "upper_scan_and_f_zero_limits_differ; use upper_f_zero_load for the dissertation f=0 limit"
            )
    return tuple(warnings)


def _report_status(
    lower: CriticalLoadBoundary,
    upper_scan: CriticalLoadBoundary,
    upper_f_zero: CriticalLoadBoundary,
) -> str:
    if lower.qtr_w_m is not None and upper_f_zero.qtr_w_m is not None:
        return "evaluated"
    if lower.qtr_w_m is not None or upper_scan.qtr_w_m is not None or upper_f_zero.qtr_w_m is not None:
        return "partial"
    return "failed"


__all__ = [
    "CriticalLoadBoundary",
    "CriticalLoadConfig",
    "CriticalLoadPoint",
    "CriticalLoadReport",
    "CriticalLoadSolver",
    "QCRIT_MODEL",
    "QCRIT_SOURCE_F_ZERO",
    "QCRIT_SOURCE_SCAN",
    "find_critical_loads",
    "solve_critical_loads",
]
