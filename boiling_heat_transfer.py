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
    "but Eq. (17), graphical F/S functions, SI mapping, limits, and validation cases are not released into runtime."
)
_CHEN_1962_LOCAL_FULL_TEXT = "sources/primary/chen_1962_osti_4636495.pdf"
_CHEN_1962_LOCAL_SHA256 = "5DDE91B1FE38B2CE6E4977AEE2A25A61BBEDC83C5A7214802496754E4989017E"


@dataclass(frozen=True)
class Chen1962AuditRecord:
    registry_id: str
    source_status: str
    primary_record: str
    local_full_text_ref: str
    local_sha256: str
    formula_audit_document: str
    audited_pages: tuple[str, ...]
    equation_page_map: tuple[str, ...]
    applicability: tuple[str, ...]
    equation_structure: tuple[str, ...]
    validation_notes: tuple[str, ...]
    release_blockers: tuple[str, ...]

    def to_result_fields(self) -> dict[str, Any]:
        return {
            "boiling_heat_transfer_audit_id": self.registry_id,
            "boiling_heat_transfer_audit_source_status": self.source_status,
            "boiling_heat_transfer_audit_local_full_text": self.local_full_text_ref,
            "boiling_heat_transfer_audit_sha256": self.local_sha256,
            "boiling_heat_transfer_formula_audit_document": self.formula_audit_document,
            "boiling_heat_transfer_audited_pages": list(self.audited_pages),
            "boiling_heat_transfer_equation_page_map": list(self.equation_page_map),
            "boiling_heat_transfer_applicability": list(self.applicability),
            "boiling_heat_transfer_equation_structure": list(self.equation_structure),
            "boiling_heat_transfer_validation_notes": list(self.validation_notes),
            "boiling_heat_transfer_release_blockers": list(self.release_blockers),
        }


def chen_1962_audit_record() -> Chen1962AuditRecord:
    return Chen1962AuditRecord(
        registry_id="HTC-CHEN-1962-SOURCE-CANDIDATE",
        source_status="candidate_only",
        primary_record="https://www.osti.gov/biblio/4636495",
        local_full_text_ref=_CHEN_1962_LOCAL_FULL_TEXT,
        local_sha256=_CHEN_1962_LOCAL_SHA256,
        formula_audit_document="docs/chen_1962_formula_audit_2026-07-06.md",
        audited_pages=("4", "6", "10-19", "20-25", "32-33"),
        equation_page_map=(
            "Page 4: additive micro-convective plus macro-convective structure; scanned formula lines degraded.",
            "Page 6: applicability limits for saturated vertical axial stable flow without slug flow, liquid deficiency, or CHF.",
            "Pages 10-11: text layer verifies Eq. (9) structure as liquid-side Dittus-Boelter form multiplied by F; visual scan confirmation still required.",
            "Pages 12-14: micro branch follows Forster-Zuber basis; S uses effective-to-wall superheat and local two-phase Reynolds number; Eq. (17) remains OCR-degraded.",
            "Page 13: text layer verifies Eq. (18) additive total HTC h = h_mic + h_mac; visual scan confirmation still required.",
            "Pages 14-15: final correlation uses Eqs. (9), (17), and (18); F and S are graphical in Figs. 7 and 8.",
            "Pages 20-25: bibliography, condition/deviation tables and nomenclature require manual verification before SI mapping.",
            "Pages 32-33: F and S curves are graphical and require digitization or authoritative tabulation.",
        ),
        applicability=(
            "Saturated two-phase non-metallic fluid in convective flow.",
            "Vertical axial flow; stable flow; no slug flow; no liquid deficiency.",
            "Heat flux below critical flux.",
            "Usually annular or annular-mist flow.",
            "Approximate vapor quality range 1 to 70 percent.",
        ),
        equation_structure=(
            "Total HTC is an additive micro-convective plus macro-convective coefficient.",
            "Eq. (9) text-layer structure: h_mac = 0.023 * Re_L^0.8 * Pr_L^0.4 * k_L/D * F.",
            "Eq. (18) text-layer structure: h = h_mic + h_mac.",
            "Micro-convective branch is based on the Forster-Zuber pool-boiling form and a suppression factor S; Eq. (17) still requires visual transcription.",
            "F is determined from the Martinelli parameter; S is determined from a local two-phase Reynolds number.",
            "The released report presents F and S graphically in Figures 7 and 8, so runtime use needs digitization or an authoritative tabulation.",
        ),
        validation_notes=(
            "The report compares water and organic-fluid data from nine experimental cases.",
            "The report includes condition ranges in Table I and correlation-comparison deviations in Table II.",
            "The report scope is HTC prediction only; it does not release a project dryout or CHF limit.",
        ),
        release_blockers=(
            "Digitize or otherwise obtain authoritative numeric F and S functions from Figures 7 and 8.",
            "Visually confirm Eq. (9) and Eq. (18), and fully transcribe Eq. (17) from the scan.",
            "Map original variables, imperial units, and property definitions to the project's SI state variables.",
            "Add primary-source reference HTC values and tolerance tests before enabling runtime calculation.",
            "Keep geometry scope explicit: the source is for vertical axial flow, while project scenarios also include horizontal evaporator sections.",
            "Do not use this HTC audit as a dryout or CHF correlation.",
        ),
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
    audit_record: Chen1962AuditRecord | None = None

    def to_result_fields(self) -> dict[str, Any]:
        fields: dict[str, Any] = {
            "boiling_heat_transfer_candidate": self.model,
            "boiling_heat_transfer_source": self.source,
            "boiling_heat_transfer_source_status": self.source_status,
            "boiling_heat_transfer_required_audit_checks": list(self.required_audit_checks),
        }
        if self.audit_record is not None:
            fields.update(self.audit_record.to_result_fields())
        return fields


def chen_1962_source_candidate() -> HeatTransferSourceCandidate:
    return HeatTransferSourceCandidate(
        model=CHEN_1962_SOURCE_CANDIDATE,
        source_status="source_candidate_not_released",
        source=_CHEN_1962_SOURCE,
        primary_record="https://www.osti.gov/biblio/4636495",
        local_full_text_ref="https://www.osti.gov/servlets/purl/4636495",
        blocking_reason=_CHEN_1962_WARNING,
        required_audit_checks=(
            "Digitize or tabulate Chen 1962 graphical F and S functions from the primary report.",
            "Map pages 4, 6, 10-19, 20-25, and 32-33 variables, units, property definitions, and graphical functions into project SI state variables.",
            "Add reference HTC values and boundary-condition tests before release.",
            "Decide released geometry scope before using the vertical-flow correlation in project scenarios.",
        ),
        audit_record=chen_1962_audit_record(),
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
    boiling_heat_transfer_required_audit_checks: tuple[str, ...] | list[str] = ()
    boiling_heat_transfer_audit_id: str = ""
    boiling_heat_transfer_audit_source_status: str = ""
    boiling_heat_transfer_audit_local_full_text: str = ""
    boiling_heat_transfer_audit_sha256: str = ""
    boiling_heat_transfer_formula_audit_document: str = ""
    boiling_heat_transfer_audited_pages: tuple[str, ...] | list[str] = ()
    boiling_heat_transfer_equation_page_map: tuple[str, ...] | list[str] = ()
    boiling_heat_transfer_applicability: tuple[str, ...] | list[str] = ()
    boiling_heat_transfer_equation_structure: tuple[str, ...] | list[str] = ()
    boiling_heat_transfer_validation_notes: tuple[str, ...] | list[str] = ()
    boiling_heat_transfer_release_blockers: tuple[str, ...] | list[str] = ()
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
            "boiling_heat_transfer_required_audit_checks": list(
                self.boiling_heat_transfer_required_audit_checks
            ),
            "boiling_heat_transfer_audit_id": self.boiling_heat_transfer_audit_id,
            "boiling_heat_transfer_audit_source_status": self.boiling_heat_transfer_audit_source_status,
            "boiling_heat_transfer_audit_local_full_text": self.boiling_heat_transfer_audit_local_full_text,
            "boiling_heat_transfer_audit_sha256": self.boiling_heat_transfer_audit_sha256,
            "boiling_heat_transfer_formula_audit_document": self.boiling_heat_transfer_formula_audit_document,
            "boiling_heat_transfer_audited_pages": list(self.boiling_heat_transfer_audited_pages),
            "boiling_heat_transfer_equation_page_map": list(self.boiling_heat_transfer_equation_page_map),
            "boiling_heat_transfer_applicability": list(self.boiling_heat_transfer_applicability),
            "boiling_heat_transfer_equation_structure": list(
                self.boiling_heat_transfer_equation_structure
            ),
            "boiling_heat_transfer_validation_notes": list(self.boiling_heat_transfer_validation_notes),
            "boiling_heat_transfer_release_blockers": list(self.boiling_heat_transfer_release_blockers),
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
    "Chen1962AuditRecord",
    "HeatTransferSourceCandidate",
    "PRESCRIBED_HEAT_INPUT",
    "WALL_COUPLED",
    "WallSoilBoundary",
    "chen_1962_audit_record",
    "chen_1962_source_candidate",
    "diagnose_prescribed_heat_input",
    "diagnostics_for_solver_status",
    "failure_class_from_solver_status",
    "hydraulic_perimeter_m",
    "normalize_heat_transfer_model",
    "wall_coupled_heat_input_w_m",
]
