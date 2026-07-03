from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from pressure_balance import LoopPressureBalance


def _format_unique_summary(values: tuple[str, ...]) -> str:
    ordered_values = []
    for value in values:
        text = str(value)
        if text and text not in ordered_values:
            ordered_values.append(text)
    return "; ".join(ordered_values)


@dataclass(frozen=True)
class LoopSectionState:
    section_name: str
    section_kind: str
    orientation: str
    length_m: float
    phase_regime: str
    pressure_drop_pa: float
    inlet_liquid_mass_flow_kg_s: float
    inlet_vapor_mass_flow_kg_s: float
    outlet_liquid_mass_flow_kg_s: float
    outlet_vapor_mass_flow_kg_s: float


@dataclass(frozen=True)
class EvaporatorProfile:
    coordinate_0_1: tuple[float, ...]
    axial_position_m: tuple[float, ...]
    phase_regime: tuple[str, ...]
    flow_regime: tuple[str, ...]
    local_temperature_c: tuple[float, ...]
    local_pressure_pa: tuple[float, ...]
    vapor_mass_flow_kg_s: tuple[float, ...]
    liquid_mass_flow_kg_s: tuple[float, ...]
    gas_volume_fraction: tuple[float, ...]
    liquid_volume_fraction: tuple[float, ...]
    gas_superficial_velocity_m_s: tuple[float, ...]
    liquid_superficial_velocity_m_s: tuple[float, ...]
    slip_ratio: tuple[float, ...]
    gas_reynolds: tuple[float, ...]
    liquid_reynolds: tuple[float, ...]
    martinelli_x: tuple[float, ...]
    two_phase_multiplier: tuple[float, ...]
    two_phase_pressure_gradient_pa_per_m: tuple[float, ...]
    flow_regime_source: tuple[str, ...] = ()
    flow_regime_status: tuple[str, ...] = ()
    flow_regime_transition_criteria: tuple[str, ...] = ()
    flow_regime_confidence: tuple[str, ...] = ()

    @property
    def n_points(self) -> int:
        return len(self.coordinate_0_1)


@dataclass(frozen=True)
class RiserProfile:
    height_m: tuple[float, ...]
    flow_regime: tuple[str, ...]
    local_temperature_c: tuple[float, ...]
    local_pressure_pa: tuple[float, ...]
    gas_volume_fraction: tuple[float, ...]
    liquid_volume_fraction: tuple[float, ...]
    mixture_density_kg_m3: tuple[float, ...]
    gas_superficial_velocity_m_s: tuple[float, ...]
    liquid_superficial_velocity_m_s: tuple[float, ...]
    slip_ratio: tuple[float, ...]
    pressure_gradient_pa_per_m: tuple[float, ...]
    cumulative_driving_pressure_pa: tuple[float, ...]
    flow_regime_source: tuple[str, ...] = ()
    flow_regime_status: tuple[str, ...] = ()
    flow_regime_transition_criteria: tuple[str, ...] = ()
    flow_regime_confidence: tuple[str, ...] = ()

    @property
    def n_points(self) -> int:
        return len(self.height_m)


@dataclass(frozen=True)
class SteadyPassResult:
    total_heat_w: float
    preboiling_length_fraction: float
    preboiling_evaporator_length_m: float
    preboiling_path_length_m: float
    boiling_length_m: float
    boiling_onset_position_m: float
    vapor_mass_flow_out_kg_s: float
    liquid_mass_flow_out_kg_s: float
    liquid_mass_flow_in_kg_s: float
    outlet_gas_volume_fraction_closure: float
    outlet_liquid_volume_fraction_closure: float
    gas_velocity_out_m_s: float
    liquid_velocity_out_m_s: float
    liquid_velocity_in_m_s: float
    total_pressure_drop_pa: float
    boiling_section_pressure_drop_pa: float
    inlet_liquid_pressure_drop_pa: float
    outlet_section_pressure_drop_pa: float
    acceleration_pressure_drop_pa: float
    outlet_mixture_density_kg_m3: float
    required_head_m: float
    outlet_mass_quality: float
    liquid_mass_flow_out_lph: float
    liquid_mass_flow_in_lph: float
    vapor_mass_flow_liq_equiv_lph: float
    vapor_mass_flow_gas_lph: float
    outlet_gas_volume_fraction_true: float
    outlet_slip_ratio: float
    driving_pressure_pa: float
    effective_density_difference_kg_m3: float
    outlet_selected_void_fraction_model: str = ""
    outlet_selected_friction_model: str = ""
    evaporator_dominant_flow_regime: str = ""
    riser_dominant_flow_regime: str = ""
    evaporator_flow_regime_summary: str = ""
    riser_flow_regime_summary: str = ""
    friction_model: str = "mathcad_compat"
    pressure_balance: LoopPressureBalance | None = None
    model_mode: str = "worksheet_compatible"
    geometry_source: str = "mathcad_default"
    section_states: tuple[LoopSectionState, ...] = ()
    evaporator_profile: EvaporatorProfile | None = None
    riser_profile: RiserProfile | None = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "model_mode": self.model_mode,
            "friction_model": self.friction_model,
            "geometry_source": self.geometry_source,
            "U_W": self.total_heat_w,
            "yn": self.preboiling_length_fraction,
            "preboiling_evaporator_length_m": self.preboiling_evaporator_length_m,
            "preboiling_path_length_m": self.preboiling_path_length_m,
            "boiling_length_m": self.boiling_length_m,
            "boiling_onset_position_m": self.boiling_onset_position_m,
            "n_control_volumes": self.evaporator_profile.n_points if self.evaporator_profile is not None else 0,
            "n_riser_points": self.riser_profile.n_points if self.riser_profile is not None else 0,
            "n_section_states": len(self.section_states),
            "section_state_names": ",".join(section.section_name for section in self.section_states),
            "GG_out_kg_s": self.vapor_mass_flow_out_kg_s,
            "GL_out_kg_s": self.liquid_mass_flow_out_kg_s,
            "GL_in_kg_s": self.liquid_mass_flow_in_kg_s,
            "phiG_formula": self.outlet_gas_volume_fraction_closure,
            "phiL_formula": self.outlet_liquid_volume_fraction_closure,
            "VG_out_m_s": self.gas_velocity_out_m_s,
            "VL_out_m_s": self.liquid_velocity_out_m_s,
            "VL_in_m_s": self.liquid_velocity_in_m_s,
            "deltaP_Pa": self.total_pressure_drop_pa,
            "sumPsiL_Pa": self.boiling_section_pressure_drop_pa,
            "delta_pX_Pa": self.inlet_liquid_pressure_drop_pa,
            "delta_pL1_Pa": self.outlet_section_pressure_drop_pa,
            "delta_Pu_Pa": self.acceleration_pressure_drop_pa,
            "rhoef_kg_m3": self.outlet_mixture_density_kg_m3,
            "Hy_m": self.required_head_m,
            "chiG1_mass": self.outlet_mass_quality,
            "outlet_mass_quality": self.outlet_mass_quality,
            "GL1_lph": self.liquid_mass_flow_out_lph,
            "GL0_lph": self.liquid_mass_flow_in_lph,
            "GG0_lph": self.vapor_mass_flow_liq_equiv_lph,
            "GG0_liq_equiv_lph": self.vapor_mass_flow_liq_equiv_lph,
            "GG0_gas_lph": self.vapor_mass_flow_gas_lph,
            "phiG1_true": self.outlet_gas_volume_fraction_true,
            "outlet_slip_ratio": self.outlet_slip_ratio,
            "outlet_selected_void_fraction_model": self.outlet_selected_void_fraction_model,
            "outlet_selected_friction_model": self.outlet_selected_friction_model,
            "driving_pressure_pa": self.driving_pressure_pa,
            "effective_density_difference_kg_m3": self.effective_density_difference_kg_m3,
            "evaporator_dominant_flow_regime": self.evaporator_dominant_flow_regime,
            "riser_dominant_flow_regime": self.riser_dominant_flow_regime,
            "evaporator_flow_regime_summary": self.evaporator_flow_regime_summary,
            "riser_flow_regime_summary": self.riser_flow_regime_summary,
            "outlet_gas_volume_fraction_true": self.outlet_gas_volume_fraction_true,
            "outlet_no_slip_gas_volume_fraction": self.outlet_gas_volume_fraction_true,
            "outlet_gas_volume_fraction_closure": self.outlet_gas_volume_fraction_closure,
            "outlet_closure_void_fraction": self.outlet_gas_volume_fraction_closure,
            "outlet_liquid_volume_fraction_closure": self.outlet_liquid_volume_fraction_closure,
        }
        if self.evaporator_profile is not None:
            data.update(
                {
                    "evaporator_flow_regime_source_summary": _format_unique_summary(
                        self.evaporator_profile.flow_regime_source
                    ),
                    "evaporator_flow_regime_status_summary": _format_unique_summary(
                        self.evaporator_profile.flow_regime_status
                    ),
                }
            )
        if self.riser_profile is not None:
            data.update(
                {
                    "riser_flow_regime_source_summary": _format_unique_summary(
                        self.riser_profile.flow_regime_source
                    ),
                    "riser_flow_regime_status_summary": _format_unique_summary(
                        self.riser_profile.flow_regime_status
                    ),
                }
            )
        if self.pressure_balance is not None:
            data.update(
                {
                    "pressure_balance_terms": self.pressure_balance.terms_as_dicts(),
                    "pressure_balance_sections": self.pressure_balance.sections_as_dicts(),
                    "pressure_balance_summary": self.pressure_balance.summary_string(),
                    "pressure_balance_total_friction_pa": self.pressure_balance.total_friction_pa,
                    "pressure_balance_total_hydrostatic_pa": self.pressure_balance.total_hydrostatic_pa,
                    "pressure_balance_total_acceleration_pa": self.pressure_balance.total_acceleration_pa,
                    "pressure_balance_total_local_pa": self.pressure_balance.total_local_pa,
                    "pressure_balance_total_resistance_pa": self.pressure_balance.total_resistance_pa,
                    "pressure_balance_residual_pa": self.pressure_balance.residual_pa,
                }
            )
        return data


@dataclass(frozen=True)
class SteadyLoopResult:
    converged: bool
    H: float
    qtr: float
    Li: float
    tcon: float
    circulation_factor: float | None = None
    auxiliary_temperature_c: float | None = None
    average_temperature_c: float | None = None
    outlet_mixture_temperature_c: float | None = None
    normalized_head_indicator: float | None = None
    normalized_temperature_indicator: float | None = None
    geometric_head_indicator: float | None = None
    pass_result: SteadyPassResult | None = None
    root_bracket: tuple[float, float] | None = None
    n_sign_changes: int = 0
    solver_status: str = "not_run"
    failure_reason: str | None = None
    closure_name: str = ""
    property_model_name: str = ""
    fluid: str = ""
    fluid_cas: str = ""
    refrigerant_name: str = ""
    property_backend: str = ""
    property_source: str = ""
    property_warning: str = ""
    near_critical_warning: str = ""
    model_scientific_status: str = ""
    friction_model: str = "mathcad_compat"
    geometry_source: str = "mathcad_default"
    heat_transfer_model: str = "prescribed_heat_input"
    boiling_heat_transfer_status: str = "not_evaluated"
    boiling_heat_flux_w_m2: float | None = None
    boiling_heat_transfer_limit: str = "not_evaluated_source_required"
    dryout_limit: str = "not_evaluated_source_required"
    hydrodynamic_limit: str = "not_active"
    property_limit: str = "not_active"
    numerical_failure: str = "not_active"
    failure_class: str = "none"
    warnings: tuple[str, ...] = ()
    qcrit_status: str = "not_evaluated"
    qcrit_model: str = "not_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "converged": self.converged,
            "H": self.H,
            "qtr": self.qtr,
            "Li": self.Li,
            "tcon": self.tcon,
            "root_bracket": self.root_bracket,
            "n_sign_changes": self.n_sign_changes,
            "solver_status": self.solver_status,
            "failure_reason": self.failure_reason,
            "closure_name": self.closure_name,
            "property_model_name": self.property_model_name,
            "fluid": self.fluid,
            "fluid_cas": self.fluid_cas,
            "refrigerant_name": self.refrigerant_name,
            "property_backend": self.property_backend,
            "property_source": self.property_source,
            "property_warning": self.property_warning,
            "near_critical_warning": self.near_critical_warning,
            "model_scientific_status": self.model_scientific_status,
            "friction_model": self.friction_model,
            "geometry_source": self.geometry_source,
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
            "qcrit_status": self.qcrit_status,
            "qcrit_model": self.qcrit_model,
        }
        if self.circulation_factor is not None:
            data["fff"] = self.circulation_factor
            data["circulation_factor"] = self.circulation_factor
        if self.auxiliary_temperature_c is not None:
            data["tmm_C"] = self.auxiliary_temperature_c
            data["auxiliary_temperature_c"] = self.auxiliary_temperature_c
        if self.average_temperature_c is not None:
            data["tav_C"] = self.average_temperature_c
            data["average_temperature_c"] = self.average_temperature_c
        if self.outlet_mixture_temperature_c is not None:
            data["tvih_C"] = self.outlet_mixture_temperature_c
            data["outlet_mixture_temperature_c"] = self.outlet_mixture_temperature_c
        if self.normalized_head_indicator is not None:
            data["RVN0"] = self.normalized_head_indicator
            data["normalized_head_indicator"] = self.normalized_head_indicator
        if self.normalized_temperature_indicator is not None:
            data["RVN"] = self.normalized_temperature_indicator
            data["normalized_temperature_indicator"] = self.normalized_temperature_indicator
        if self.geometric_head_indicator is not None:
            data["RV1"] = self.geometric_head_indicator
            data["geometric_head_indicator"] = self.geometric_head_indicator
        if self.pass_result is not None:
            data.update(self.pass_result.to_dict())
        return data
