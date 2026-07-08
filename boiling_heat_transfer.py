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
    "but candidate F/S graph digitization, SI mapping, limits, and validation cases are not released into runtime."
)
_CHEN_1962_LOCAL_FULL_TEXT = "sources/primary/chen_1962_osti_4636495.pdf"
_CHEN_1962_LOCAL_SHA256 = "5DDE91B1FE38B2CE6E4977AEE2A25A61BBEDC83C5A7214802496754E4989017E"
_CHEN_1962_HTC_SOURCE_TO_SI = 5.678263341
_CHEN_1962_THERMAL_CONDUCTIVITY_SOURCE_TO_SI = 1.730734666
_CHEN_1962_HEAT_CAPACITY_SOURCE_TO_SI = 4186.8
_CHEN_1962_DENSITY_SOURCE_TO_SI = 16.018463374
_CHEN_1962_VISCOSITY_SOURCE_TO_SI = 4.133788732e-4
_CHEN_1962_LATENT_HEAT_SOURCE_TO_SI = 2326.0
_CHEN_1962_SURFACE_TENSION_SOURCE_TO_SI = 14.593902937
_CHEN_1962_PRESSURE_SOURCE_TO_SI = 47.880258980
_CHEN_1962_FOOT_TO_METER = 0.3048
_CHEN_1962_GC_HR = 4.1697567e8
_CHEN_1962_FIG7_INVERSE_MARTINELLI_MIN = 0.1
_CHEN_1962_FIG7_INVERSE_MARTINELLI_MAX = 100.0
_CHEN_1962_FIG8_TWO_PHASE_REYNOLDS_MIN = 1.5e4
_CHEN_1962_FIG8_TWO_PHASE_REYNOLDS_MAX = 7.0e5
_CHEN_1962_SOURCE_QUALITY_MIN = 0.01
_CHEN_1962_SOURCE_QUALITY_MAX = 0.70


@dataclass(frozen=True)
class Chen1962CandidateHeatTransferResult:
    """Candidate-only Chen 1962 source-unit calculation; not a released runtime HTC."""

    h_macro_w_m2_k: float
    h_micro_w_m2_k: float
    h_total_w_m2_k: float
    h_macro_source: float
    h_micro_source: float
    h_total_source: float
    f_factor: float
    suppression_factor: float
    source_status: str = "candidate_only_not_runtime_released"


@dataclass(frozen=True)
class Chen1962CandidateFlowBoilingResult:
    """Candidate-only end-to-end Chen graph-to-HTC calculation; not runtime."""

    inverse_martinelli_parameter: float
    f_factor: float
    two_phase_reynolds: float
    suppression_factor: float
    heat_transfer: Chen1962CandidateHeatTransferResult
    source_status: str = "candidate_only_not_runtime_released"


@dataclass(frozen=True)
class WojtanTh3337CandidateDryoutBoundaryResult:
    """Candidate-only TH3337/Wojtan dryout-boundary transcription; not runtime dryout."""

    dryout_inception_quality: float
    dryout_completion_quality: float
    source_status: str = "candidate_only_not_runtime_released"


@dataclass(frozen=True)
class WojtanTh2978CandidateDryoutLimitResult:
    """Candidate-only TH2978 rendered-page dryout-limit transcription; not runtime."""

    dryout_inception_quality: float
    dryout_completion_quality: float
    source_status: str = "candidate_only_not_runtime_released"


@dataclass(frozen=True)
class Chen1962AuditRecord:
    registry_id: str
    source_status: str
    primary_record: str
    local_full_text_ref: str
    local_sha256: str
    formula_audit_document: str
    graph_digitization_document: str
    graph_review_document: str
    si_mapping_document: str
    validation_tables_document: str
    reference_value_audit_document: str
    scope_audit_document: str
    hand_calculation_document: str
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
            "boiling_heat_transfer_graph_digitization_document": self.graph_digitization_document,
            "boiling_heat_transfer_graph_review_document": self.graph_review_document,
            "boiling_heat_transfer_si_mapping_document": self.si_mapping_document,
            "boiling_heat_transfer_validation_tables_document": self.validation_tables_document,
            "boiling_heat_transfer_reference_value_audit_document": (
                self.reference_value_audit_document
            ),
            "boiling_heat_transfer_scope_audit_document": self.scope_audit_document,
            "boiling_heat_transfer_hand_calculation_document": self.hand_calculation_document,
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
        graph_digitization_document="docs/chen_1962_graph_digitization_2026-07-07.md",
        graph_review_document="docs/chen_1962_graph_review_2026-07-08.md",
        si_mapping_document="docs/chen_1962_si_mapping_2026-07-07.md",
        validation_tables_document="docs/chen_1962_validation_tables_2026-07-07.md",
        reference_value_audit_document="docs/chen_1962_reference_value_audit_2026-07-08.md",
        scope_audit_document="docs/chen_1962_scope_audit_2026-07-08.md",
        hand_calculation_document="docs/chen_1962_hand_calculation_2026-07-08.md",
        audited_pages=("4", "6", "10-19", "20-25", "32-35"),
        equation_page_map=(
            "Page 4: additive micro-convective plus macro-convective structure; scanned formula lines degraded.",
            "Page 6: applicability limits for saturated vertical axial stable flow without slug flow, liquid deficiency, or CHF.",
            "Pages 10-11: visual scan verifies Eq. (9) as liquid-side Dittus-Boelter form multiplied by F.",
            "Pages 12-14: visual scan verifies Eq. (17) as the Forster-Zuber-based micro-convective branch multiplied by suppression factor S.",
            "Page 13: visual scan verifies Eq. (18) additive total HTC h = h_mic + h_mac.",
            "Pages 14-15: final correlation uses Eqs. (9), (17), and (18); F and S are graphical in Figs. 7 and 8.",
            "Pages 20-25: bibliography, condition/deviation tables and nomenclature require manual verification before SI mapping.",
            "Pages 32-33: F and S curves are graphical; candidate digitization is recorded in docs/chen_1962_graph_digitization_2026-07-07.md and rendered graph review is recorded in docs/chen_1962_graph_review_2026-07-08.md.",
            "Pages 34-35: Figs. 9 and 10 are comparison plots; docs/chen_1962_reference_value_audit_2026-07-08.md records no printed pointwise HTC table in the audited report pages.",
            "Pages 20-21: nomenclature records the source English-unit convention used for candidate SI mapping in docs/chen_1962_si_mapping_2026-07-07.md.",
        ),
        applicability=(
            "Saturated two-phase non-metallic fluid in convective flow.",
            "Vertical axial flow; stable flow; no slug flow; no liquid deficiency.",
            "Heat flux below critical flux.",
            "Usually annular or annular-mist flow.",
            "Approximate vapor quality range 1 to 70 percent.",
            "Scope audit keeps release eligibility vertical-heated-flow only; the current horizontal evaporator is unsupported.",
        ),
        equation_structure=(
            "Total HTC is an additive micro-convective plus macro-convective coefficient.",
            "Eq. (9) scan-verified structure: h_mac = 0.023 * Re_L^0.8 * Pr_L^0.4 * k_L/D * F.",
            "Eq. (18) text-layer structure: h = h_mic + h_mac.",
            "Eq. (17) scan-verified Forster-Zuber-based structure: h_mic = 0.00122 * (k_L^0.79 * Cp_L^0.45 * rho_L^0.49 * g_c^0.25) / (sigma^0.5 * mu_L^0.29 * lambda^0.24 * rho_v^0.24) * DeltaT^0.24 * DeltaP^0.75 * S.",
            "F is determined from the Martinelli parameter; S is determined from a local two-phase Reynolds number.",
            "The released report presents F and S graphically in Figures 7 and 8; candidate digitization and rendered review exist but runtime use needs an accepted release-grade interpolation decision and reference tests.",
            "Candidate SI mapping helper keeps Chen's source coefficient by converting SI inputs to source units, evaluating Eqs. (9), (17), and (18), then converting h back to W/(m^2 K).",
            "Candidate graph-axis helpers compute 1/X_tt from vapor quality and phase properties and R = Re_L*F^1.25 for Fig. 8; they are not selectable runtime HTC inputs.",
            "Candidate arithmetic fixtures for the direct Eqs. (9)/(17)/(18) path and graph-to-SI composition are documented in docs/chen_1962_hand_calculation_2026-07-08.md.",
        ),
        validation_notes=(
            "The report compares water and organic-fluid data from nine experimental cases.",
            "Table I contains condition ranges only: fluid, geometry, flow direction, pressure, liquid flow velocity, quality, and heat flux.",
            "Table II contains average percent deviations only; it has no raw HTC measurements or pointwise predicted HTC values.",
            "Manual Table I/II transcription is recorded in docs/chen_1962_validation_tables_2026-07-07.md.",
            "Reference-value audit in docs/chen_1962_reference_value_audit_2026-07-08.md found no printed pointwise HTC cases in the audited report pages.",
            "Scope audit in docs/chen_1962_scope_audit_2026-07-08.md fixes the source maximum as vertical heated axial flow with 0.01 <= x <= 0.70.",
            "Candidate hand-calculation arithmetic is recorded in docs/chen_1962_hand_calculation_2026-07-08.md; it is not a pointwise Chen report validation case.",
            "The report scope is HTC prediction only; it does not release a project dryout or CHF limit.",
        ),
        release_blockers=(
            "Accept the reviewed F and S graph digitization from docs/chen_1962_graph_digitization_2026-07-07.md and docs/chen_1962_graph_review_2026-07-08.md as release-grade interpolation proof or obtain authoritative numeric tables.",
            "Review candidate SI mapping and graph-axis helpers from docs/chen_1962_si_mapping_2026-07-07.md before selectable runtime release.",
            "Promote the documented candidate hand calculation to release-grade proof or add primary-source HTC reference values from another source before enabling runtime calculation.",
            "Implement vertical-heated-flow-only geometry guards from docs/chen_1962_scope_audit_2026-07-08.md before any selectable runtime release.",
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
            "Review candidate Chen 1962 F and S graph digitization or obtain authoritative tabulation from the primary report.",
            "Review candidate source-unit to SI, graph-axis, and graph-to-SI helpers for pages 4, 6, 10-19, 20-25, and 32-33 before runtime implementation.",
            "Add reference HTC values and boundary-condition tests before release.",
            "Decide released geometry scope before using the vertical-flow correlation in project scenarios.",
        ),
        audit_record=chen_1962_audit_record(),
    )


def chen_1962_candidate_f_factor(inverse_martinelli_parameter: float) -> float:
    """Candidate Fig. 7 fit for F as a function of 1/X_tt; not release-grade."""

    y_value = _positive_finite(
        inverse_martinelli_parameter,
        "inverse_martinelli_parameter",
    )
    if not (
        _CHEN_1962_FIG7_INVERSE_MARTINELLI_MIN
        <= y_value
        <= _CHEN_1962_FIG7_INVERSE_MARTINELLI_MAX
    ):
        raise ValueError(
            "inverse_martinelli_parameter must stay within Chen Fig. 7 candidate "
            "digitization range 0.1 <= 1/X_tt <= 100."
        )
    return 2.35 * ((y_value + 0.213) ** 0.736)


def chen_1962_candidate_inverse_martinelli_parameter(
    *,
    mass_quality: float,
    liquid_density_kg_m3: float,
    vapor_density_kg_m3: float,
    liquid_viscosity_pa_s: float,
    vapor_viscosity_pa_s: float,
) -> float:
    """Candidate Fig. 7 abscissa 1/X_tt from Chen's nomenclature; not released."""

    quality = _open_unit_interval(mass_quality, "mass_quality")
    liquid_fraction = 1.0 - quality
    rho_l = _positive_finite(liquid_density_kg_m3, "liquid_density_kg_m3")
    rho_v = _positive_finite(vapor_density_kg_m3, "vapor_density_kg_m3")
    mu_l = _positive_finite(liquid_viscosity_pa_s, "liquid_viscosity_pa_s")
    mu_v = _positive_finite(vapor_viscosity_pa_s, "vapor_viscosity_pa_s")
    return (
        ((quality / liquid_fraction) ** 0.9)
        * ((rho_l / rho_v) ** 0.5)
        * ((mu_v / mu_l) ** 0.1)
    )


def chen_1962_candidate_two_phase_reynolds(
    *,
    reynolds_liquid: float,
    f_factor: float,
) -> float:
    """Candidate Fig. 8 abscissa Re_L*F^1.25; not release-grade."""

    re_l = _positive_finite(reynolds_liquid, "reynolds_liquid")
    f_value = _positive_finite(f_factor, "f_factor")
    return re_l * (f_value ** 1.25)


def chen_1962_candidate_suppression_factor(two_phase_reynolds: float) -> float:
    """Candidate Fig. 8 fit for S as a function of Re_L*F^1.25; not release-grade."""

    reynolds = _positive_finite(two_phase_reynolds, "two_phase_reynolds")
    if not (
        _CHEN_1962_FIG8_TWO_PHASE_REYNOLDS_MIN
        <= reynolds
        <= _CHEN_1962_FIG8_TWO_PHASE_REYNOLDS_MAX
    ):
        raise ValueError(
            "two_phase_reynolds must stay within Chen Fig. 8 candidate digitization "
            "range 1.5e4 <= Re_L*F^1.25 <= 7e5."
        )
    return 1.0 / (1.0 + 1.024e-5 * (reynolds ** 1.0397))


def chen_1962_candidate_heat_transfer_coefficient_si(
    *,
    reynolds_liquid: float,
    prandtl_liquid: float,
    diameter_m: float,
    liquid_thermal_conductivity_w_m_k: float,
    liquid_heat_capacity_j_kg_k: float,
    liquid_density_kg_m3: float,
    vapor_density_kg_m3: float,
    liquid_viscosity_pa_s: float,
    surface_tension_n_m: float,
    latent_heat_j_kg: float,
    wall_superheat_k: float,
    vapor_pressure_difference_pa: float,
    f_factor: float,
    suppression_factor: float,
) -> Chen1962CandidateHeatTransferResult:
    """Evaluate scan-verified Chen 1962 Eqs. (9), (17), and (18) as a candidate helper.

    The calculation follows docs/chen_1962_si_mapping_2026-07-07.md: SI inputs
    are converted to Chen's source units, the original coefficients are used,
    and the source HTC is converted back to W/(m^2 K). The helper is not wired
    into the solver as a released heat-transfer model.
    """

    re_l = _positive_finite(reynolds_liquid, "reynolds_liquid")
    pr_l = _positive_finite(prandtl_liquid, "prandtl_liquid")
    diameter_ft = _positive_finite(diameter_m, "diameter_m") / _CHEN_1962_FOOT_TO_METER
    k_source = (
        _positive_finite(
            liquid_thermal_conductivity_w_m_k,
            "liquid_thermal_conductivity_w_m_k",
        )
        / _CHEN_1962_THERMAL_CONDUCTIVITY_SOURCE_TO_SI
    )
    cp_source = (
        _positive_finite(liquid_heat_capacity_j_kg_k, "liquid_heat_capacity_j_kg_k")
        / _CHEN_1962_HEAT_CAPACITY_SOURCE_TO_SI
    )
    rho_l_source = (
        _positive_finite(liquid_density_kg_m3, "liquid_density_kg_m3")
        / _CHEN_1962_DENSITY_SOURCE_TO_SI
    )
    rho_v_source = (
        _positive_finite(vapor_density_kg_m3, "vapor_density_kg_m3")
        / _CHEN_1962_DENSITY_SOURCE_TO_SI
    )
    mu_l_source = (
        _positive_finite(liquid_viscosity_pa_s, "liquid_viscosity_pa_s")
        / _CHEN_1962_VISCOSITY_SOURCE_TO_SI
    )
    sigma_source = (
        _positive_finite(surface_tension_n_m, "surface_tension_n_m")
        / _CHEN_1962_SURFACE_TENSION_SOURCE_TO_SI
    )
    latent_source = (
        _positive_finite(latent_heat_j_kg, "latent_heat_j_kg")
        / _CHEN_1962_LATENT_HEAT_SOURCE_TO_SI
    )
    superheat_f = _positive_finite(wall_superheat_k, "wall_superheat_k") * 9.0 / 5.0
    pressure_source = (
        _positive_finite(vapor_pressure_difference_pa, "vapor_pressure_difference_pa")
        / _CHEN_1962_PRESSURE_SOURCE_TO_SI
    )
    f_value = _positive_finite(f_factor, "f_factor")
    s_value = _positive_finite(suppression_factor, "suppression_factor")
    if s_value > 1.0:
        raise ValueError("suppression_factor must be in the candidate graph range 0 < S <= 1.")

    h_macro_source = 0.023 * (re_l ** 0.8) * (pr_l ** 0.4) * (k_source / diameter_ft) * f_value
    h_micro_source = (
        0.00122
        * (
            (k_source ** 0.79)
            * (cp_source ** 0.45)
            * (rho_l_source ** 0.49)
            * (_CHEN_1962_GC_HR ** 0.25)
        )
        / (
            (sigma_source ** 0.5)
            * (mu_l_source ** 0.29)
            * (latent_source ** 0.24)
            * (rho_v_source ** 0.24)
        )
        * (superheat_f ** 0.24)
        * (pressure_source ** 0.75)
        * s_value
    )
    h_total_source = h_macro_source + h_micro_source
    return Chen1962CandidateHeatTransferResult(
        h_macro_w_m2_k=h_macro_source * _CHEN_1962_HTC_SOURCE_TO_SI,
        h_micro_w_m2_k=h_micro_source * _CHEN_1962_HTC_SOURCE_TO_SI,
        h_total_w_m2_k=h_total_source * _CHEN_1962_HTC_SOURCE_TO_SI,
        h_macro_source=h_macro_source,
        h_micro_source=h_micro_source,
        h_total_source=h_total_source,
        f_factor=f_value,
        suppression_factor=s_value,
    )


def chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si(
    *,
    mass_quality: float,
    reynolds_liquid: float,
    prandtl_liquid: float,
    diameter_m: float,
    liquid_thermal_conductivity_w_m_k: float,
    liquid_heat_capacity_j_kg_k: float,
    liquid_density_kg_m3: float,
    vapor_density_kg_m3: float,
    liquid_viscosity_pa_s: float,
    vapor_viscosity_pa_s: float,
    surface_tension_n_m: float,
    latent_heat_j_kg: float,
    wall_superheat_k: float,
    vapor_pressure_difference_pa: float,
) -> Chen1962CandidateFlowBoilingResult:
    """Evaluate the complete candidate Chen graph-to-HTC path; not released.

    This helper composes the candidate Fig. 7 abscissa, Fig. 7 `F` fit, Fig. 8
    abscissa, Fig. 8 `S` fit, and source-unit SI mapping. It is deliberately
    separate from the selectable solver path because the graph digitization,
    geometry scope, and source/reference HTC validation remain unreleased.
    """

    quality = _open_unit_interval(mass_quality, "mass_quality")
    if not (_CHEN_1962_SOURCE_QUALITY_MIN <= quality <= _CHEN_1962_SOURCE_QUALITY_MAX):
        raise ValueError(
            "mass_quality must stay within Chen 1962 candidate source scope "
            "0.01 <= x <= 0.70."
        )
    inverse_martinelli = chen_1962_candidate_inverse_martinelli_parameter(
        mass_quality=quality,
        liquid_density_kg_m3=liquid_density_kg_m3,
        vapor_density_kg_m3=vapor_density_kg_m3,
        liquid_viscosity_pa_s=liquid_viscosity_pa_s,
        vapor_viscosity_pa_s=vapor_viscosity_pa_s,
    )
    f_value = chen_1962_candidate_f_factor(inverse_martinelli)
    two_phase_reynolds = chen_1962_candidate_two_phase_reynolds(
        reynolds_liquid=reynolds_liquid,
        f_factor=f_value,
    )
    suppression = chen_1962_candidate_suppression_factor(two_phase_reynolds)
    heat_transfer = chen_1962_candidate_heat_transfer_coefficient_si(
        reynolds_liquid=reynolds_liquid,
        prandtl_liquid=prandtl_liquid,
        diameter_m=diameter_m,
        liquid_thermal_conductivity_w_m_k=liquid_thermal_conductivity_w_m_k,
        liquid_heat_capacity_j_kg_k=liquid_heat_capacity_j_kg_k,
        liquid_density_kg_m3=liquid_density_kg_m3,
        vapor_density_kg_m3=vapor_density_kg_m3,
        liquid_viscosity_pa_s=liquid_viscosity_pa_s,
        surface_tension_n_m=surface_tension_n_m,
        latent_heat_j_kg=latent_heat_j_kg,
        wall_superheat_k=wall_superheat_k,
        vapor_pressure_difference_pa=vapor_pressure_difference_pa,
        f_factor=f_value,
        suppression_factor=suppression,
    )
    return Chen1962CandidateFlowBoilingResult(
        inverse_martinelli_parameter=inverse_martinelli,
        f_factor=f_value,
        two_phase_reynolds=two_phase_reynolds,
        suppression_factor=suppression,
        heat_transfer=heat_transfer,
    )


def wojtan_th3337_candidate_dryout_inception_quality(
    *,
    gas_weber_number: float,
    gas_froude_number: float,
    vapor_density_kg_m3: float,
    liquid_density_kg_m3: float,
    heat_flux_ratio_q_qcrit: float,
) -> float:
    """Candidate TH3337 Eq. (7.19) dryout inception quality xdi; not released."""

    we_g, fr_g, density_ratio, heat_flux_ratio = _wojtan_th3337_dryout_inputs(
        gas_weber_number=gas_weber_number,
        gas_froude_number=gas_froude_number,
        vapor_density_kg_m3=vapor_density_kg_m3,
        liquid_density_kg_m3=liquid_density_kg_m3,
        heat_flux_ratio_q_qcrit=heat_flux_ratio_q_qcrit,
    )
    value = 0.58 * math.exp(
        0.52
        - 0.235
        * (we_g ** 0.17)
        * (fr_g ** 0.37)
        * (density_ratio ** 0.25)
        * (heat_flux_ratio ** 0.70)
    )
    return _positive_finite(value, "dryout_inception_quality")


def wojtan_th3337_candidate_dryout_completion_quality(
    *,
    gas_weber_number: float,
    gas_froude_number: float,
    vapor_density_kg_m3: float,
    liquid_density_kg_m3: float,
    heat_flux_ratio_q_qcrit: float,
) -> float:
    """Candidate TH3337 Eq. (7.20) dryout completion quality xde; not released."""

    we_g, fr_g, density_ratio, heat_flux_ratio = _wojtan_th3337_dryout_inputs(
        gas_weber_number=gas_weber_number,
        gas_froude_number=gas_froude_number,
        vapor_density_kg_m3=vapor_density_kg_m3,
        liquid_density_kg_m3=liquid_density_kg_m3,
        heat_flux_ratio_q_qcrit=heat_flux_ratio_q_qcrit,
    )
    value = 0.61 * math.exp(
        0.57
        - 5.8e-3
        * (we_g ** 0.38)
        * (fr_g ** 0.15)
        * (density_ratio ** -0.09)
        * (heat_flux_ratio ** 0.27)
    )
    return _positive_finite(value, "dryout_completion_quality")


def wojtan_th3337_candidate_dryout_boundaries(
    *,
    gas_weber_number: float,
    gas_froude_number: float,
    vapor_density_kg_m3: float,
    liquid_density_kg_m3: float,
    heat_flux_ratio_q_qcrit: float,
) -> WojtanTh3337CandidateDryoutBoundaryResult:
    """Return candidate TH3337/Wojtan dryout inception/completion qualities."""

    return WojtanTh3337CandidateDryoutBoundaryResult(
        dryout_inception_quality=wojtan_th3337_candidate_dryout_inception_quality(
            gas_weber_number=gas_weber_number,
            gas_froude_number=gas_froude_number,
            vapor_density_kg_m3=vapor_density_kg_m3,
            liquid_density_kg_m3=liquid_density_kg_m3,
            heat_flux_ratio_q_qcrit=heat_flux_ratio_q_qcrit,
        ),
        dryout_completion_quality=wojtan_th3337_candidate_dryout_completion_quality(
            gas_weber_number=gas_weber_number,
            gas_froude_number=gas_froude_number,
            vapor_density_kg_m3=vapor_density_kg_m3,
            liquid_density_kg_m3=liquid_density_kg_m3,
            heat_flux_ratio_q_qcrit=heat_flux_ratio_q_qcrit,
        ),
    )


def wojtan_th2978_candidate_dryout_inception_quality(
    *,
    gas_weber_number: float,
    gas_froude_number: float,
    vapor_density_kg_m3: float,
    liquid_density_kg_m3: float,
    heat_flux_ratio_q_qcrit: float,
) -> float:
    """Candidate TH2978 Eq. (7.47) dryout inception quality xdi; not released."""

    return wojtan_th3337_candidate_dryout_inception_quality(
        gas_weber_number=gas_weber_number,
        gas_froude_number=gas_froude_number,
        vapor_density_kg_m3=vapor_density_kg_m3,
        liquid_density_kg_m3=liquid_density_kg_m3,
        heat_flux_ratio_q_qcrit=heat_flux_ratio_q_qcrit,
    )


def wojtan_th2978_candidate_dryout_completion_quality(
    *,
    gas_weber_number: float,
    gas_froude_number: float,
    vapor_density_kg_m3: float,
    liquid_density_kg_m3: float,
    heat_flux_ratio_q_qcrit: float,
) -> float:
    """Candidate TH2978 Eq. (7.48) dryout completion quality xde; not released."""

    return wojtan_th3337_candidate_dryout_completion_quality(
        gas_weber_number=gas_weber_number,
        gas_froude_number=gas_froude_number,
        vapor_density_kg_m3=vapor_density_kg_m3,
        liquid_density_kg_m3=liquid_density_kg_m3,
        heat_flux_ratio_q_qcrit=heat_flux_ratio_q_qcrit,
    )


def wojtan_th2978_candidate_dryout_limits(
    *,
    gas_weber_number: float,
    gas_froude_number: float,
    vapor_density_kg_m3: float,
    liquid_density_kg_m3: float,
    heat_flux_ratio_q_qcrit: float,
) -> WojtanTh2978CandidateDryoutLimitResult:
    """Return candidate TH2978 Eqs. (7.47)-(7.48) dryout limits."""

    return WojtanTh2978CandidateDryoutLimitResult(
        dryout_inception_quality=wojtan_th2978_candidate_dryout_inception_quality(
            gas_weber_number=gas_weber_number,
            gas_froude_number=gas_froude_number,
            vapor_density_kg_m3=vapor_density_kg_m3,
            liquid_density_kg_m3=liquid_density_kg_m3,
            heat_flux_ratio_q_qcrit=heat_flux_ratio_q_qcrit,
        ),
        dryout_completion_quality=wojtan_th2978_candidate_dryout_completion_quality(
            gas_weber_number=gas_weber_number,
            gas_froude_number=gas_froude_number,
            vapor_density_kg_m3=vapor_density_kg_m3,
            liquid_density_kg_m3=liquid_density_kg_m3,
            heat_flux_ratio_q_qcrit=heat_flux_ratio_q_qcrit,
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
    boiling_heat_transfer_required_audit_checks: tuple[str, ...] | list[str] = ()
    boiling_heat_transfer_audit_id: str = ""
    boiling_heat_transfer_audit_source_status: str = ""
    boiling_heat_transfer_audit_local_full_text: str = ""
    boiling_heat_transfer_audit_sha256: str = ""
    boiling_heat_transfer_formula_audit_document: str = ""
    boiling_heat_transfer_graph_digitization_document: str = ""
    boiling_heat_transfer_graph_review_document: str = ""
    boiling_heat_transfer_si_mapping_document: str = ""
    boiling_heat_transfer_validation_tables_document: str = ""
    boiling_heat_transfer_reference_value_audit_document: str = ""
    boiling_heat_transfer_scope_audit_document: str = ""
    boiling_heat_transfer_hand_calculation_document: str = ""
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
            "boiling_heat_transfer_graph_digitization_document": (
                self.boiling_heat_transfer_graph_digitization_document
            ),
            "boiling_heat_transfer_graph_review_document": (
                self.boiling_heat_transfer_graph_review_document
            ),
            "boiling_heat_transfer_si_mapping_document": self.boiling_heat_transfer_si_mapping_document,
            "boiling_heat_transfer_validation_tables_document": (
                self.boiling_heat_transfer_validation_tables_document
            ),
            "boiling_heat_transfer_reference_value_audit_document": (
                self.boiling_heat_transfer_reference_value_audit_document
            ),
            "boiling_heat_transfer_scope_audit_document": self.boiling_heat_transfer_scope_audit_document,
            "boiling_heat_transfer_hand_calculation_document": (
                self.boiling_heat_transfer_hand_calculation_document
            ),
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


def _positive_finite(value: float, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{name} must be a positive finite value.")
    return numeric


def _open_unit_interval(value: float, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 < numeric < 1.0:
        raise ValueError(f"{name} must be a finite value in the open interval (0, 1).")
    return numeric


def _wojtan_th3337_dryout_inputs(
    *,
    gas_weber_number: float,
    gas_froude_number: float,
    vapor_density_kg_m3: float,
    liquid_density_kg_m3: float,
    heat_flux_ratio_q_qcrit: float,
) -> tuple[float, float, float, float]:
    we_g = _positive_finite(gas_weber_number, "gas_weber_number")
    fr_g = _positive_finite(gas_froude_number, "gas_froude_number")
    rho_g = _positive_finite(vapor_density_kg_m3, "vapor_density_kg_m3")
    rho_l = _positive_finite(liquid_density_kg_m3, "liquid_density_kg_m3")
    heat_flux_ratio = _positive_finite(heat_flux_ratio_q_qcrit, "heat_flux_ratio_q_qcrit")
    return we_g, fr_g, rho_g / rho_l, heat_flux_ratio


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
    "Chen1962CandidateFlowBoilingResult",
    "Chen1962CandidateHeatTransferResult",
    "HeatTransferSourceCandidate",
    "PRESCRIBED_HEAT_INPUT",
    "WALL_COUPLED",
    "WallSoilBoundary",
    "WojtanTh2978CandidateDryoutLimitResult",
    "WojtanTh3337CandidateDryoutBoundaryResult",
    "chen_1962_audit_record",
    "chen_1962_candidate_f_factor",
    "chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si",
    "chen_1962_candidate_heat_transfer_coefficient_si",
    "chen_1962_candidate_inverse_martinelli_parameter",
    "chen_1962_candidate_suppression_factor",
    "chen_1962_candidate_two_phase_reynolds",
    "chen_1962_source_candidate",
    "diagnose_prescribed_heat_input",
    "diagnostics_for_solver_status",
    "failure_class_from_solver_status",
    "hydraulic_perimeter_m",
    "normalize_heat_transfer_model",
    "wall_coupled_heat_input_w_m",
    "wojtan_th3337_candidate_dryout_boundaries",
    "wojtan_th3337_candidate_dryout_completion_quality",
    "wojtan_th3337_candidate_dryout_inception_quality",
    "wojtan_th2978_candidate_dryout_completion_quality",
    "wojtan_th2978_candidate_dryout_inception_quality",
    "wojtan_th2978_candidate_dryout_limits",
]
