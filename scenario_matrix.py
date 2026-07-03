from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterable

from boiling_heat_transfer import failure_class_from_solver_status
from co2_geometry import LoopGeometry, default_mathcad_geometry
from co2_steady_solver import SteadyLoopInputs
from refrigerant_loop_model import RefrigerantLoopModel
from refrigerant_properties import BackendUnavailableError, PropertyRangeError


SCENARIO_STATUSES = (
    "working",
    "no_root",
    "no_driving_head",
    "near_critical_region",
    "property_out_of_range",
    "validation_error",
    "backend_unavailable",
    "numerical_failure",
)

SCENARIO_FAILURE_CLASSES = (
    "none",
    "validation_error",
    "property_limit",
    "hydrodynamic_limit",
    "numerical_failure",
)

ModelFactory = Callable[..., RefrigerantLoopModel]


@dataclass(frozen=True)
class ScenarioCase:
    case_id: str
    fluid: str
    H: float
    qtr: float
    Li: float
    tcon: float
    property_backend: str = "coolprop"
    tags: tuple[str, ...] = ()
    mode: str = "worksheet_compatible"
    closure_model: str = "zivi"
    friction_model: str = "colebrook_white"
    geometry: LoopGeometry | None = None
    heat_transfer_model: str = "prescribed_heat_input"

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "tags": list(self.tags),
            "fluid": self.fluid,
            "property_backend": self.property_backend,
            "H": self.H,
            "qtr": self.qtr,
            "Li": self.Li,
            "tcon": self.tcon,
            "mode": self.mode,
            "closure_model": self.closure_model,
            "friction_model": self.friction_model,
            "geometry_source": self.geometry.geometry_source if self.geometry is not None else "mathcad_default",
            "heat_transfer_model": self.heat_transfer_model,
        }


@dataclass(frozen=True)
class ScenarioOutcome:
    case_id: str
    tags: tuple[str, ...]
    fluid: str
    property_backend: str
    H: float
    qtr: float
    Li: float
    tcon: float
    status: str
    converged: bool
    solver_status: str
    failure_class: str
    failure_reason: str | None = None
    circulation_factor: float | None = None
    root_bracket: tuple[float, float] | None = None
    n_sign_changes: int = 0
    warnings: tuple[str, ...] = ()
    qcrit_status: str = "not_evaluated"
    geometry_source: str = "mathcad_default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "tags": list(self.tags),
            "fluid": self.fluid,
            "property_backend": self.property_backend,
            "H": self.H,
            "qtr": self.qtr,
            "Li": self.Li,
            "tcon": self.tcon,
            "status": self.status,
            "converged": self.converged,
            "solver_status": self.solver_status,
            "failure_class": self.failure_class,
            "failure_reason": self.failure_reason,
            "circulation_factor": self.circulation_factor,
            "root_bracket": self.root_bracket,
            "n_sign_changes": self.n_sign_changes,
            "warnings": list(self.warnings),
            "qcrit_status": self.qcrit_status,
            "geometry_source": self.geometry_source,
        }


@dataclass(frozen=True)
class ScenarioMatrixReport:
    outcomes: tuple[ScenarioOutcome, ...]

    @property
    def status_counts(self) -> dict[str, int]:
        return dict(Counter(outcome.status for outcome in self.outcomes))

    @property
    def failure_class_counts(self) -> dict[str, int]:
        return dict(Counter(outcome.failure_class for outcome in self.outcomes))

    @property
    def coverage_tags(self) -> tuple[str, ...]:
        tags = {tag for outcome in self.outcomes for tag in outcome.tags}
        return tuple(sorted(tags))

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_cases": len(self.outcomes),
            "status_counts": self.status_counts,
            "failure_class_counts": self.failure_class_counts,
            "coverage_tags": list(self.coverage_tags),
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
        }


def run_scenario_matrix(
    cases: Iterable[ScenarioCase] | None = None,
    *,
    root_nsamp: int = 24,
    model_factory: ModelFactory = RefrigerantLoopModel,
) -> ScenarioMatrixReport:
    selected_cases = tuple(cases) if cases is not None else default_scenario_cases(include_backend_probe=False)
    outcomes = tuple(
        run_scenario_case(case, root_nsamp=root_nsamp, model_factory=model_factory) for case in selected_cases
    )
    return ScenarioMatrixReport(outcomes=outcomes)


def run_scenario_case(
    case: ScenarioCase,
    *,
    root_nsamp: int = 24,
    model_factory: ModelFactory = RefrigerantLoopModel,
) -> ScenarioOutcome:
    if root_nsamp < 3:
        return _outcome(
            case,
            status="validation_error",
            solver_status="validation_error",
            failure_class="validation_error",
            failure_reason="root_nsamp must be at least 3.",
        )
    validation_error = _validate_case(case)
    if validation_error is not None:
        return _outcome(
            case,
            status="validation_error",
            solver_status="validation_error",
            failure_class="validation_error",
            failure_reason=validation_error,
        )
    if case.H == 0.0:
        return _outcome(
            case,
            status="no_driving_head",
            solver_status="no_driving_head",
            failure_class="hydrodynamic_limit",
            failure_reason="H=0 gives no hydrostatic driving head for natural circulation.",
        )

    try:
        if case.geometry is not None:
            case.geometry.validate_current_solver_sections()
        model = model_factory(
            fluid=case.fluid,
            property_backend=case.property_backend,
            geometry=case.geometry,
        )
    except BackendUnavailableError as exc:
        return _outcome(
            case,
            status="backend_unavailable",
            solver_status="backend_unavailable",
            failure_class="property_limit",
            failure_reason=str(exc),
        )
    except ValueError as exc:
        return _outcome(
            case,
            status="validation_error",
            solver_status="validation_error",
            failure_class="validation_error",
            failure_reason=str(exc),
        )
    except Exception as exc:
        return _outcome(
            case,
            status="numerical_failure",
            solver_status="model_initialization_failed",
            failure_class="numerical_failure",
            failure_reason=str(exc),
        )

    inputs = SteadyLoopInputs(
        H=case.H,
        qtr=case.qtr,
        Li=case.Li,
        tcon=case.tcon,
        mode=case.mode,
        closure_model=case.closure_model,
        friction_model=case.friction_model,
        geometry=case.geometry,
        heat_transfer_model=case.heat_transfer_model,
    )

    property_fields = model.steady_solver.property_result_fields(inputs)
    near_critical_warning = property_fields.get("near_critical_warning", "")
    if near_critical_warning:
        return _outcome(
            case,
            status="near_critical_region",
            solver_status="near_critical_region",
            failure_class="property_limit",
            failure_reason=near_critical_warning,
            warnings=(near_critical_warning,),
        )

    try:
        model.properties.state_at_temperature(case.tcon)
        root_search = model.steady_solver.find_circulation_factor(inputs=inputs, nsamp=root_nsamp)
    except PropertyRangeError as exc:
        return _outcome(
            case,
            status="property_out_of_range",
            solver_status="property_out_of_range",
            failure_class="property_limit",
            failure_reason=str(exc),
        )
    except ValueError as exc:
        return _outcome(
            case,
            status="validation_error",
            solver_status="validation_error",
            failure_class="validation_error",
            failure_reason=str(exc),
        )
    except Exception as exc:
        return _outcome(
            case,
            status="numerical_failure",
            solver_status="root_scan_exception",
            failure_class="numerical_failure",
            failure_reason=str(exc),
        )

    if root_search.circulation_factor is not None:
        return _outcome(
            case,
            status="working",
            converged=True,
            solver_status=root_search.solver_status,
            failure_class="none",
            circulation_factor=root_search.circulation_factor,
            root_bracket=root_search.root_bracket,
            n_sign_changes=root_search.n_sign_changes,
        )

    status = _status_from_solver_status(root_search.solver_status)
    failure_class = failure_class_from_solver_status(root_search.solver_status)
    return _outcome(
        case,
        status=status,
        solver_status=root_search.solver_status,
        failure_class=failure_class,
        failure_reason=root_search.failure_reason,
        root_bracket=root_search.root_bracket,
        n_sign_changes=root_search.n_sign_changes,
    )


def default_scenario_cases(*, include_backend_probe: bool = True) -> tuple[ScenarioCase, ...]:
    cases: list[ScenarioCase] = []
    for fluid, tag in (("CO2", "co2_temperature_grid"), ("NH3", "nh3_temperature_grid")):
        for tcon in (-20.0, -10.0, 0.0, 10.0, 20.0):
            cases.append(
                ScenarioCase(
                    case_id=f"{fluid.lower()}_tcon_{_temperature_token(tcon)}",
                    fluid=fluid,
                    H=2.5,
                    qtr=40.0,
                    Li=200.0,
                    tcon=tcon,
                    tags=(tag,),
                )
            )

    cases.extend(
        (
            ScenarioCase("co2_qtr_low", "CO2", 2.5, 5.0, 200.0, 0.0, tags=("qtr_sweep",)),
            ScenarioCase("co2_qtr_nominal", "CO2", 2.5, 40.0, 200.0, 0.0, tags=("qtr_sweep",)),
            ScenarioCase("co2_qtr_high_no_root", "CO2", 2.5, 120.0, 200.0, 0.0, tags=("qtr_sweep",)),
            ScenarioCase("co2_height_low", "CO2", 1.0, 40.0, 200.0, 0.0, tags=("height_sweep",)),
            ScenarioCase("co2_height_nominal", "CO2", 2.5, 40.0, 200.0, 0.0, tags=("height_sweep",)),
            ScenarioCase(
                "co2_high_riser",
                "CO2",
                5.0,
                40.0,
                200.0,
                0.0,
                tags=("height_sweep", "high_riser"),
                geometry=_manual_geometry(riser_height_m=5.0),
            ),
            ScenarioCase("co2_li_short", "CO2", 2.5, 40.0, 50.0, 0.0, tags=("length_sweep",)),
            ScenarioCase("co2_li_nominal", "CO2", 2.5, 40.0, 200.0, 0.0, tags=("length_sweep",)),
            ScenarioCase("co2_li_long_no_root", "CO2", 2.5, 40.0, 400.0, 0.0, tags=("length_sweep",)),
            ScenarioCase(
                "co2_diameter_small_no_root",
                "CO2",
                2.5,
                40.0,
                200.0,
                0.0,
                tags=("diameter_sweep",),
                geometry=_manual_geometry(diameter_m=0.020),
            ),
            ScenarioCase(
                "co2_diameter_nominal",
                "CO2",
                2.5,
                40.0,
                200.0,
                0.0,
                tags=("diameter_sweep",),
                geometry=_manual_geometry(diameter_m=2.0 * 1.325e-2),
            ),
            ScenarioCase(
                "co2_diameter_large",
                "CO2",
                2.5,
                40.0,
                200.0,
                0.0,
                tags=("diameter_sweep",),
                geometry=_manual_geometry(diameter_m=0.040),
            ),
            ScenarioCase(
                "co2_roughness_smooth",
                "CO2",
                2.5,
                40.0,
                200.0,
                0.0,
                tags=("roughness_sweep",),
                geometry=_manual_geometry(roughness_m=1.0e-5),
            ),
            ScenarioCase(
                "co2_roughness_nominal",
                "CO2",
                2.5,
                40.0,
                200.0,
                0.0,
                tags=("roughness_sweep",),
                geometry=_manual_geometry(roughness_m=1.0e-4),
            ),
            ScenarioCase(
                "co2_roughness_rough",
                "CO2",
                2.5,
                40.0,
                200.0,
                0.0,
                tags=("roughness_sweep",),
                geometry=_manual_geometry(roughness_m=5.0e-4),
            ),
            ScenarioCase(
                "co2_horizontal_no_riser",
                "CO2",
                0.0,
                40.0,
                200.0,
                0.0,
                tags=("horizontal_without_riser", "no_driving_head"),
            ),
            ScenarioCase("co2_near_critical", "CO2", 2.5, 40.0, 200.0, 30.0, tags=("near_critical",)),
            ScenarioCase("co2_invalid_zero_qtr", "CO2", 2.5, 0.0, 200.0, 0.0, tags=("invalid_input",)),
            ScenarioCase("co2_invalid_negative_H", "CO2", -1.0, 40.0, 200.0, 0.0, tags=("invalid_input",)),
            ScenarioCase("co2_invalid_zero_Li", "CO2", 2.5, 40.0, 0.0, 0.0, tags=("invalid_input",)),
        )
    )

    if include_backend_probe:
        cases.append(
            ScenarioCase(
                "co2_refprop_backend_probe",
                "CO2",
                2.5,
                40.0,
                200.0,
                0.0,
                property_backend="refprop",
                tags=("backend_unavailable",),
            )
        )
    return tuple(cases)


def _validate_case(case: ScenarioCase) -> str | None:
    for field_name, value in (("H", case.H), ("qtr", case.qtr), ("Li", case.Li), ("tcon", case.tcon)):
        if not math.isfinite(float(value)):
            return f"{field_name} must be finite."
    if case.H < 0.0:
        return "H must be non-negative."
    if case.qtr <= 0.0:
        return "qtr must be a positive finite heat input."
    if case.Li <= 0.0:
        return "Li must be a positive finite evaporator length."
    return None


def _outcome(
    case: ScenarioCase,
    *,
    status: str,
    solver_status: str,
    failure_class: str,
    converged: bool = False,
    failure_reason: str | None = None,
    circulation_factor: float | None = None,
    root_bracket: tuple[float, float] | None = None,
    n_sign_changes: int = 0,
    warnings: tuple[str, ...] = (),
) -> ScenarioOutcome:
    return ScenarioOutcome(
        case_id=case.case_id,
        tags=case.tags,
        fluid=case.fluid,
        property_backend=case.property_backend,
        H=case.H,
        qtr=case.qtr,
        Li=case.Li,
        tcon=case.tcon,
        status=status,
        converged=converged,
        solver_status=solver_status,
        failure_class=failure_class,
        failure_reason=failure_reason,
        circulation_factor=circulation_factor,
        root_bracket=root_bracket,
        n_sign_changes=n_sign_changes,
        warnings=warnings,
        geometry_source=case.geometry.geometry_source if case.geometry is not None else "mathcad_default",
    )


def _status_from_solver_status(solver_status: str) -> str:
    if solver_status == "property_out_of_range":
        return "property_out_of_range"
    if solver_status == "no_root_bracket":
        return "no_root"
    return "numerical_failure"


def _manual_geometry(
    *,
    diameter_m: float = 2.0 * 1.325e-2,
    roughness_m: float = 1.0e-4,
    riser_height_m: float = 2.5,
    evaporator_length_m: float = 200.0,
) -> LoopGeometry:
    sections = tuple(
        replace(
            section,
            hydraulic_diameter_m=diameter_m,
            roughness_m=roughness_m,
            area_m2=math.pi * (0.5 * diameter_m) ** 2,
        )
        for section in default_mathcad_geometry(
            evaporator_length_m=evaporator_length_m,
            riser_height_m=riser_height_m,
        ).sections
    )
    return LoopGeometry.from_sections(sections, geometry_source="manual_sections")


def _temperature_token(value: float) -> str:
    integer_value = int(value)
    prefix = "minus" if integer_value < 0 else ""
    return f"{prefix}{abs(integer_value)}"


__all__ = [
    "SCENARIO_FAILURE_CLASSES",
    "SCENARIO_STATUSES",
    "ScenarioCase",
    "ScenarioMatrixReport",
    "ScenarioOutcome",
    "default_scenario_cases",
    "run_scenario_case",
    "run_scenario_matrix",
]
