from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


PRESCRIBED_HEAT_INPUT = "prescribed_heat_input"
WALL_COUPLED = "wall_coupled"

_HEAT_TRANSFER_MODEL_ALIASES = {
    PRESCRIBED_HEAT_INPUT: PRESCRIBED_HEAT_INPUT,
    "prescribed": PRESCRIBED_HEAT_INPUT,
    "prescribed_qtr": PRESCRIBED_HEAT_INPUT,
    "fixed_heat_input": PRESCRIBED_HEAT_INPUT,
    WALL_COUPLED: WALL_COUPLED,
    "wall_soil_coupled": WALL_COUPLED,
}

_HTC_SOURCE_WARNING = (
    "Published saturated flow-boiling heat-transfer correlation is not implemented; "
    "boiling heat-transfer limit is diagnostic-only until a primary source is wired."
)
_DRYOUT_SOURCE_WARNING = (
    "Dryout/CHF diagnostic requires a source-specific correlation and is not evaluated "
    "from solver convergence."
)


@dataclass(frozen=True)
class BoilingDiagnostics:
    heat_transfer_model: str
    boiling_heat_transfer_status: str
    boiling_heat_flux_w_m2: float | None = None
    boiling_heat_transfer_limit: str = "not_evaluated_source_required"
    dryout_limit: str = "not_evaluated_source_required"
    hydrodynamic_limit: str = "not_active"
    property_limit: str = "not_active"
    numerical_failure: str = "not_active"
    failure_class: str = "none"
    warnings: tuple[str, ...] = ()

    def to_result_fields(self) -> dict[str, Any]:
        return {
            "heat_transfer_model": self.heat_transfer_model,
            "boiling_heat_transfer_status": self.boiling_heat_transfer_status,
            "boiling_heat_flux_w_m2": self.boiling_heat_flux_w_m2,
            "boiling_heat_transfer_limit": self.boiling_heat_transfer_limit,
            "dryout_limit": self.dryout_limit,
            "hydrodynamic_limit": self.hydrodynamic_limit,
            "property_limit": self.property_limit,
            "numerical_failure": self.numerical_failure,
            "failure_class": self.failure_class,
            "warnings": list(self.warnings),
        }


def normalize_heat_transfer_model(model: str) -> str:
    key = str(model).strip().lower()
    try:
        return _HEAT_TRANSFER_MODEL_ALIASES[key]
    except KeyError as exc:
        valid = ", ".join(sorted({PRESCRIBED_HEAT_INPUT, WALL_COUPLED}))
        raise ValueError(f"Unknown heat_transfer_model {model!r}; valid values are: {valid}.") from exc


def failure_class_from_solver_status(
    solver_status: str,
    *,
    near_critical_warning: str = "",
) -> str:
    if near_critical_warning:
        return "property_limit"
    if solver_status in {"converged", ""}:
        return "none"
    if solver_status == "validation_error":
        return "validation_error"
    if solver_status == "property_out_of_range":
        return "property_limit"
    if solver_status == "no_driving_head":
        return "hydrodynamic_limit"
    if solver_status in {
        "no_root_bracket",
        "root_solver_failed",
        "root_solver_not_converged",
        "internal_pass_failed",
        "aux_temperature_failed",
    }:
        return "numerical_failure"
    return "numerical_failure"


def diagnostics_for_solver_status(
    *,
    heat_transfer_model: str,
    solver_status: str,
    near_critical_warning: str = "",
    failure_reason: str | None = None,
) -> BoilingDiagnostics:
    failure_class = failure_class_from_solver_status(
        solver_status,
        near_critical_warning=near_critical_warning,
    )
    warnings = _diagnostic_warnings(near_critical_warning)
    property_limit = "near_critical_warning" if near_critical_warning else "not_active"
    hydrodynamic_limit = "not_active"
    numerical_failure = "not_active"
    boiling_status = "not_evaluated_solver_not_converged"

    if solver_status == "validation_error":
        boiling_status = "validation_error"
    elif solver_status == "property_out_of_range":
        property_limit = "property_out_of_range"
    elif failure_class == "hydrodynamic_limit":
        hydrodynamic_limit = solver_status
    elif failure_class == "numerical_failure":
        numerical_failure = solver_status

    if heat_transfer_model == WALL_COUPLED:
        boiling_status = "validation_error"
        limit = "requires_wall_boundary"
        warnings = tuple(value for value in warnings if value != _HTC_SOURCE_WARNING)
        if failure_reason:
            warnings = (*warnings, failure_reason)
        return BoilingDiagnostics(
            heat_transfer_model=heat_transfer_model,
            boiling_heat_transfer_status=boiling_status,
            boiling_heat_transfer_limit=limit,
            dryout_limit="not_evaluated_requires_wall_boundary",
            hydrodynamic_limit=hydrodynamic_limit,
            property_limit=property_limit,
            numerical_failure=numerical_failure,
            failure_class=failure_class,
            warnings=warnings,
        )

    return BoilingDiagnostics(
        heat_transfer_model=heat_transfer_model,
        boiling_heat_transfer_status=boiling_status,
        hydrodynamic_limit=hydrodynamic_limit,
        property_limit=property_limit,
        numerical_failure=numerical_failure,
        failure_class=failure_class,
        warnings=warnings,
    )


def diagnose_prescribed_heat_input(
    *,
    qtr_w_per_m: float,
    evaporator_area_m2: float,
    evaporator_hydraulic_diameter_m: float,
    boiling_length_m: float,
    near_critical_warning: str = "",
) -> BoilingDiagnostics:
    perimeter_m = hydraulic_perimeter_m(
        area_m2=evaporator_area_m2,
        hydraulic_diameter_m=evaporator_hydraulic_diameter_m,
    )
    heat_flux_w_m2 = float(qtr_w_per_m) / perimeter_m
    warnings = _diagnostic_warnings(near_critical_warning)
    property_limit = "near_critical_warning" if near_critical_warning else "not_active"
    failure_class = "property_limit" if near_critical_warning else "none"
    status = "diagnostic_only_source_required"
    hydrodynamic_limit = "not_active"
    if boiling_length_m <= 0.0:
        status = "no_boiling_region"
        hydrodynamic_limit = "no_boiling_region"
        failure_class = "hydrodynamic_limit" if not near_critical_warning else failure_class

    return BoilingDiagnostics(
        heat_transfer_model=PRESCRIBED_HEAT_INPUT,
        boiling_heat_transfer_status=status,
        boiling_heat_flux_w_m2=heat_flux_w_m2,
        hydrodynamic_limit=hydrodynamic_limit,
        property_limit=property_limit,
        failure_class=failure_class,
        warnings=warnings,
    )


def hydraulic_perimeter_m(*, area_m2: float, hydraulic_diameter_m: float) -> float:
    area = float(area_m2)
    diameter = float(hydraulic_diameter_m)
    if not math.isfinite(area) or area <= 0.0:
        raise ValueError("evaporator_area_m2 must be a positive finite value.")
    if not math.isfinite(diameter) or diameter <= 0.0:
        raise ValueError("evaporator_hydraulic_diameter_m must be a positive finite value.")
    return 4.0 * area / diameter


def _diagnostic_warnings(near_critical_warning: str) -> tuple[str, ...]:
    warnings = [_HTC_SOURCE_WARNING, _DRYOUT_SOURCE_WARNING]
    if near_critical_warning:
        warnings.append(near_critical_warning)
    return tuple(warnings)


__all__ = [
    "BoilingDiagnostics",
    "PRESCRIBED_HEAT_INPUT",
    "WALL_COUPLED",
    "diagnose_prescribed_heat_input",
    "diagnostics_for_solver_status",
    "failure_class_from_solver_status",
    "hydraulic_perimeter_m",
    "normalize_heat_transfer_model",
]
