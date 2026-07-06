from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


PRESCRIBED_HEAT_INPUT = "prescribed_heat_input"
WALL_COUPLED = "wall_coupled"
CHEN_1962_SOURCE_CANDIDATE = "chen_1962_source_candidate"

_HEAT_TRANSFER_MODEL_ALIASES = {
    PRESCRIBED_HEAT_INPUT: PRESCRIBED_HEAT_INPUT,
    "prescribed": PRESCRIBED_HEAT_INPUT,
    "prescribed_qtr": PRESCRIBED_HEAT_INPUT,
    "fixed_heat_input": PRESCRIBED_HEAT_INPUT,
    WALL_COUPLED: WALL_COUPLED,
    "wall_soil_coupled": WALL_COUPLED,
    CHEN_1962_SOURCE_CANDIDATE: CHEN_1962_SOURCE_CANDIDATE,
    "chen_1962": CHEN_1962_SOURCE_CANDIDATE,
    "chen": CHEN_1962_SOURCE_CANDIDATE,
}

_HTC_SOURCE_WARNING = (
    "Published saturated flow-boiling heat-transfer correlation is not implemented; "
    "boiling heat-transfer limit is diagnostic-only until a primary source is wired."
)
_DRYOUT_SOURCE_WARNING = (
    "Dryout/CHF diagnostic requires a source-specific correlation and is not evaluated "
    "from solver convergence."
)
_CHEN_1962_SOURCE = (
    "J. C. Chen, A correlation for boiling heat transfer to saturated fluids in convective flow, "
    "OSTI ID 4636495, DOI 10.2172/4636495; source candidate, not runtime-released."
)
_CHEN_1962_WARNING = (
    "Chen 1962 saturated convective boiling HTC is recorded as an OSTI source candidate, "
    "but equations, variables, limits, and validation cases are not released into runtime."
)


@dataclass(frozen=True)
class HeatTransferSourceCandidate:
    model: str
    source_status: str
    source: str
    primary_record: str
    local_full_text_ref: str
    blocking_reason: str
    required_audit_checks: tuple[str, ...]

    def to_result_fields(self) -> dict[str, Any]:
        return {
            "boiling_heat_transfer_candidate": self.model,
            "boiling_heat_transfer_source": self.source,
            "boiling_heat_transfer_source_status": self.source_status,
        }


def chen_1962_source_candidate() -> HeatTransferSourceCandidate:
    return HeatTransferSourceCandidate(
        model=CHEN_1962_SOURCE_CANDIDATE,
        source_status="source_candidate_not_released",
        source=_CHEN_1962_SOURCE,
        primary_record="https://www.osti.gov/biblio/4636495",
        local_full_text_ref="https://www.osti.gov/servlets/purl/4636495",
        blocking_reason=_CHEN_1962_WARNING,
        required_audit_checks=(
            "Audit the full report equations, constants, variables, and applicability range.",
            "Add reference HTC values and boundary-condition tests before release.",
            "Decide whether the correlation is diagnostic-only or an active HTC model.",
        ),
    )


@dataclass(frozen=True)
class WallSoilBoundary:
    far_field_temperature_c: float
    effective_conductance_w_m_k: float
    source: str = "designer_soil_effective_conductance"

    def heat_input_w_m(self, saturation_temperature_c: float) -> float:
        far_field_temperature = float(self.far_field_temperature_c)
        saturation_temperature = float(saturation_temperature_c)
        conductance = float(self.effective_conductance_w_m_k)
        if not math.isfinite(far_field_temperature):
            raise ValueError("wall_soil_boundary.far_field_temperature_c must be finite.")
        if not math.isfinite(saturation_temperature):
            raise ValueError("tcon must be finite for wall_coupled heat input.")
        if not math.isfinite(conductance) or conductance <= 0.0:
            raise ValueError("wall_soil_boundary.effective_conductance_w_m_k must be positive and finite.")
        heat_input = conductance * (far_field_temperature - saturation_temperature)
        if not math.isfinite(heat_input) or heat_input <= 0.0:
            raise ValueError(
                "wall_coupled heat input must be positive; far-field soil temperature must exceed tcon."
            )
        return heat_input


@dataclass(frozen=True)
class BoilingDiagnostics:
    heat_transfer_model: str
    boiling_heat_transfer_status: str
    boiling_heat_flux_w_m2: float | None = None
    boiling_heat_transfer_limit: str = "not_evaluated_source_required"
    boiling_heat_transfer_candidate: str = ""
    boiling_heat_transfer_source: str = ""
    boiling_heat_transfer_source_status: str = ""
    dryout_limit: str = "not_evaluated_source_required"
    hydrodynamic_limit: str = "not_active"
    property_limit: str = "not_active"
    numerical_failure: str = "not_active"
    failure_class: str = "none"
    warnings: tuple[str, ...] = ()
    thermal_boundary_model: str = PRESCRIBED_HEAT_INPUT
    wall_soil_temperature_c: float | None = None
    wall_soil_effective_conductance_w_m_k: float | None = None
    wall_soil_delta_t_k: float | None = None
    wall_soil_qtr_w_m: float | None = None
    wall_soil_boundary_source: str = ""

    def to_result_fields(self) -> dict[str, Any]:
        return {
            "heat_transfer_model": self.heat_transfer_model,
            "boiling_heat_transfer_status": self.boiling_heat_transfer_status,
            "boiling_heat_flux_w_m2": self.boiling_heat_flux_w_m2,
            "boiling_heat_transfer_limit": self.boiling_heat_transfer_limit,
            "boiling_heat_transfer_candidate": self.boiling_heat_transfer_candidate,
            "boiling_heat_transfer_source": self.boiling_heat_transfer_source,
            "boiling_heat_transfer_source_status": self.boiling_heat_transfer_source_status,
            "dryout_limit": self.dryout_limit,
            "hydrodynamic_limit": self.hydrodynamic_limit,
            "property_limit": self.property_limit,
            "numerical_failure": self.numerical_failure,
            "failure_class": self.failure_class,
            "warnings": list(self.warnings),
            "thermal_boundary_model": self.thermal_boundary_model,
            "wall_soil_temperature_c": self.wall_soil_temperature_c,
            "wall_soil_effective_conductance_w_m_k": self.wall_soil_effective_conductance_w_m_k,
            "wall_soil_delta_t_k": self.wall_soil_delta_t_k,
            "wall_soil_qtr_w_m": self.wall_soil_qtr_w_m,
            "wall_soil_boundary_source": self.wall_soil_boundary_source,
        }


def normalize_heat_transfer_model(model: str) -> str:
    key = str(model).strip().lower()
    try:
        return _HEAT_TRANSFER_MODEL_ALIASES[key]
    except KeyError as exc:
        valid = ", ".join(sorted({PRESCRIBED_HEAT_INPUT, WALL_COUPLED, CHEN_1962_SOURCE_CANDIDATE}))
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
    wall_soil_boundary: WallSoilBoundary | None = None,
    wall_soil_qtr_w_m: float | None = None,
    tcon_c: float | None = None,
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
        limit = "requires_wall_boundary" if wall_soil_boundary is None else "invalid_wall_boundary"
        warnings = tuple(value for value in warnings if value != _HTC_SOURCE_WARNING)
        if failure_reason:
            warnings = (*warnings, failure_reason)
        return BoilingDiagnostics(
            heat_transfer_model=heat_transfer_model,
            boiling_heat_transfer_status=boiling_status,
            boiling_heat_transfer_limit=limit,
            dryout_limit=(
                "not_evaluated_requires_wall_boundary"
                if wall_soil_boundary is None
                else "not_evaluated_source_required"
            ),
            hydrodynamic_limit=hydrodynamic_limit,
            property_limit=property_limit,
            numerical_failure=numerical_failure,
            failure_class=failure_class,
            warnings=warnings,
            **_wall_soil_result_fields(
                wall_soil_boundary=wall_soil_boundary,
                wall_soil_qtr_w_m=wall_soil_qtr_w_m,
                tcon_c=tcon_c,
            ),
        )

    if heat_transfer_model == CHEN_1962_SOURCE_CANDIDATE:
        candidate = chen_1962_source_candidate()
        warnings = (*warnings, candidate.blocking_reason)
        return BoilingDiagnostics(
            heat_transfer_model=heat_transfer_model,
            boiling_heat_transfer_status="source_candidate_source_required_not_evaluated_solver_not_converged",
            boiling_heat_transfer_limit="not_evaluated_source_required",
            hydrodynamic_limit=hydrodynamic_limit,
            property_limit=property_limit,
            numerical_failure=numerical_failure,
            failure_class=failure_class,
            warnings=warnings,
            **candidate.to_result_fields(),
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
    heat_transfer_model: str = PRESCRIBED_HEAT_INPUT,
    wall_soil_boundary: WallSoilBoundary | None = None,
    tcon_c: float | None = None,
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
    candidate_fields: dict[str, Any] = {}
    if heat_transfer_model == CHEN_1962_SOURCE_CANDIDATE:
        candidate = chen_1962_source_candidate()
        status = "source_candidate_source_required_not_released"
        warnings = (*warnings, candidate.blocking_reason)
        candidate_fields = candidate.to_result_fields()

    return BoilingDiagnostics(
        heat_transfer_model=heat_transfer_model,
        boiling_heat_transfer_status=status,
        boiling_heat_flux_w_m2=heat_flux_w_m2,
        hydrodynamic_limit=hydrodynamic_limit,
        property_limit=property_limit,
        failure_class=failure_class,
        warnings=warnings,
        **_wall_soil_result_fields(
            wall_soil_boundary=wall_soil_boundary,
            wall_soil_qtr_w_m=heat_flux_w_m2 * perimeter_m if wall_soil_boundary is not None else None,
            tcon_c=tcon_c,
        ),
        **candidate_fields,
    )


def wall_coupled_heat_input_w_m(
    wall_soil_boundary: WallSoilBoundary | None,
    *,
    tcon_c: float,
) -> float:
    if wall_soil_boundary is None:
        raise ValueError("heat_transfer_model='wall_coupled' requires wall/soil boundary conditions.")
    return wall_soil_boundary.heat_input_w_m(tcon_c)


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


def _wall_soil_result_fields(
    *,
    wall_soil_boundary: WallSoilBoundary | None,
    wall_soil_qtr_w_m: float | None,
    tcon_c: float | None,
) -> dict[str, Any]:
    if wall_soil_boundary is None:
        return {}
    temperature_c = float(wall_soil_boundary.far_field_temperature_c)
    conductance = float(wall_soil_boundary.effective_conductance_w_m_k)
    delta_t = None if tcon_c is None else temperature_c - float(tcon_c)
    return {
        "thermal_boundary_model": "wall_soil_effective_conductance",
        "wall_soil_temperature_c": temperature_c,
        "wall_soil_effective_conductance_w_m_k": conductance,
        "wall_soil_delta_t_k": delta_t,
        "wall_soil_qtr_w_m": wall_soil_qtr_w_m,
        "wall_soil_boundary_source": wall_soil_boundary.source,
    }


__all__ = [
    "BoilingDiagnostics",
    "CHEN_1962_SOURCE_CANDIDATE",
    "HeatTransferSourceCandidate",
    "PRESCRIBED_HEAT_INPUT",
    "WALL_COUPLED",
    "WallSoilBoundary",
    "chen_1962_source_candidate",
    "diagnose_prescribed_heat_input",
    "diagnostics_for_solver_status",
    "failure_class_from_solver_status",
    "hydraulic_perimeter_m",
    "normalize_heat_transfer_model",
    "wall_coupled_heat_input_w_m",
]
