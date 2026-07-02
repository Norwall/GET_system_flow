from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

import numpy as np
from scipy.optimize import root_scalar

from co2_geometry import LoopGeometry
from co2_results import EvaporatorProfile, LoopSectionState, RiserProfile, SteadyLoopResult, SteadyPassResult
from pressure_balance import LoopPressureBalance, SectionPressureBalance, hydrostatic_pressure_pa
from refrigerant_properties import PropertyRangeError, RefrigerantSaturationProperties
from two_phase_regimes import (
    FlowRegimeClassification,
    classify_horizontal_evaporator_regime_result,
    classify_vertical_riser_regime_result,
    dominant_regime,
    format_regime_summary,
    single_liquid_heating_classification,
    summarize_regime_fractions,
)
from two_phase_closures import (
    chisholm_constant,
    closure_model_scientific_status,
    closure_state_from_model,
    friction_factor_from_model,
    martinelli_parameter,
    normalize_closure_model,
    normalize_friction_model,
    two_phase_multiplier_liquid_reference,
)


def _regime_metadata_arrays(
    n_items: int,
    classification: FlowRegimeClassification,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.full(n_items, classification.source, dtype=object),
        np.full(n_items, classification.status, dtype=object),
        np.full(n_items, classification.transition_criteria, dtype=object),
        np.full(n_items, classification.confidence, dtype=object),
    )


def _write_regime_metadata(
    source_values: np.ndarray,
    status_values: np.ndarray,
    transition_values: np.ndarray,
    confidence_values: np.ndarray,
    index: int,
    classification: FlowRegimeClassification,
) -> None:
    source_values[index] = classification.source
    status_values[index] = classification.status
    transition_values[index] = classification.transition_criteria
    confidence_values[index] = classification.confidence


@dataclass(frozen=True)
class SteadyLoopInputs:
    H: float
    qtr: float
    Li: float
    tcon: float
    mode: str = "worksheet_compatible"
    closure_model: str = "worksheet_compatible"
    friction_model: str = "mathcad_compat"
    geometry: LoopGeometry | None = None


@dataclass(frozen=True)
class RootSearchResult:
    circulation_factor: float | None
    root_bracket: tuple[float, float] | None
    n_sign_changes: int
    solver_status: str
    failure_reason: str | None


class SteadyLoopSolver:
    """Steady-state решатель рабочего режима для контура естественной циркуляции."""

    def __init__(
        self,
        geometry: LoopGeometry,
        properties: RefrigerantSaturationProperties,
        closure_name: str = "darcy_friction_factor+martinelli+chisholm+worksheet_void_fraction",
    ) -> None:
        self.geometry = geometry
        self.properties = properties
        self.closure_name = closure_name
        self._last_property_error: str | None = None

    @property
    def property_model_name(self) -> str:
        return type(self.properties).__name__

    def property_result_fields(self, inputs: SteadyLoopInputs) -> dict[str, str]:
        property_warning_at_temperature = getattr(self.properties, "property_warning_at_temperature", None)
        near_critical_warning_at_temperature = getattr(self.properties, "near_critical_warning_at_temperature", None)
        property_warning = (
            property_warning_at_temperature(inputs.tcon)
            if callable(property_warning_at_temperature)
            else getattr(self.properties, "property_warning", "")
        )
        near_critical_warning = (
            near_critical_warning_at_temperature(inputs.tcon)
            if callable(near_critical_warning_at_temperature)
            else getattr(self.properties, "near_critical_warning", "")
        )
        return {
            "fluid": getattr(self.properties, "fluid", ""),
            "property_backend": getattr(self.properties, "property_backend", ""),
            "property_source": getattr(self.properties, "property_source", ""),
            "property_warning": property_warning,
            "near_critical_warning": near_critical_warning,
        }

    def effective_closure_model(self, inputs: SteadyLoopInputs) -> str:
        return normalize_closure_model(inputs.closure_model)

    def model_scientific_status(self, inputs: SteadyLoopInputs) -> str:
        return closure_model_scientific_status(inputs.closure_model)

    def closure_label(self, inputs: SteadyLoopInputs) -> str:
        effective_closure_model = self.effective_closure_model(inputs)
        if effective_closure_model == "experimental_regime_aware":
            alias_suffix = "(alias:regime_aware)" if inputs.closure_model == "regime_aware" else ""
            return (
                f"experimental_regime_aware{alias_suffix}"
                "+regime_selected_void_fraction+regime_selected_friction"
            )
        return f"{effective_closure_model}+darcy_friction_factor+martinelli+chisholm"

    def effective_friction_model(self, inputs: SteadyLoopInputs) -> str:
        return normalize_friction_model(inputs.friction_model)

    def geometry_source(self, inputs: SteadyLoopInputs) -> str:
        return inputs.geometry.geometry_source if inputs.geometry is not None else self.geometry.geometry_source

    def friction_factor(self, reynolds_number, relative_roughness: float, inputs: SteadyLoopInputs):
        return friction_factor_from_model(
            reynolds_number=reynolds_number,
            relative_roughness=relative_roughness,
            model=self.effective_friction_model(inputs),
        )

    def _section_geometry_fields(self, section) -> dict[str, float | str]:
        return {
            "hydraulic_diameter_m": float(section.hydraulic_diameter_m),
            "roughness_m": float(section.roughness_m),
            "relative_roughness": float(section.relative_roughness),
            "area_m2": float(section.area_m2),
            "heat_mode": str(section.heat_mode),
        }

    def _build_pressure_balance(
        self,
        *,
        downcomer_section,
        riser_section,
        preboiling_evaporator_section,
        boiling_evaporator_section,
        condenser_section,
        downcomer_friction_pa: float,
        riser_friction_pa: float,
        preboiling_evaporator_friction_pa: float,
        boiling_evaporator_friction_pa: float,
        condenser_friction_pa: float,
        acceleration_pressure_drop_pa: float,
        downcomer_hydrostatic_pa: float,
        riser_hydrostatic_pa: float,
        driving_pressure_pa: float,
    ) -> LoopPressureBalance:
        return LoopPressureBalance(
            sections=(
                SectionPressureBalance(
                    section_name=downcomer_section.name,
                    section_kind=downcomer_section.section_kind,
                    orientation=downcomer_section.orientation,
                    length_m=downcomer_section.length_m,
                    dz_m=downcomer_section.dz_m if downcomer_section.dz_m != 0.0 else -abs(riser_section.length_m),
                    **self._section_geometry_fields(downcomer_section),
                    delta_p_hydrostatic_pa=float(downcomer_hydrostatic_pa),
                    delta_p_friction_pa=float(downcomer_friction_pa),
                ),
                SectionPressureBalance(
                    section_name=riser_section.name,
                    section_kind=riser_section.section_kind,
                    orientation=riser_section.orientation,
                    length_m=riser_section.length_m,
                    dz_m=float(riser_section.dz_m),
                    **self._section_geometry_fields(riser_section),
                    delta_p_hydrostatic_pa=float(riser_hydrostatic_pa),
                    delta_p_friction_pa=float(riser_friction_pa),
                ),
                SectionPressureBalance(
                    section_name=preboiling_evaporator_section.name,
                    section_kind=preboiling_evaporator_section.section_kind,
                    orientation=preboiling_evaporator_section.orientation,
                    length_m=preboiling_evaporator_section.length_m,
                    dz_m=0.0,
                    **self._section_geometry_fields(preboiling_evaporator_section),
                    delta_p_friction_pa=float(preboiling_evaporator_friction_pa),
                ),
                SectionPressureBalance(
                    section_name=boiling_evaporator_section.name,
                    section_kind=boiling_evaporator_section.section_kind,
                    orientation=boiling_evaporator_section.orientation,
                    length_m=boiling_evaporator_section.length_m,
                    dz_m=0.0,
                    **self._section_geometry_fields(boiling_evaporator_section),
                    delta_p_friction_pa=float(boiling_evaporator_friction_pa),
                    delta_p_acceleration_pa=float(acceleration_pressure_drop_pa),
                ),
                SectionPressureBalance(
                    section_name=condenser_section.name,
                    section_kind=condenser_section.section_kind,
                    orientation=condenser_section.orientation,
                    length_m=condenser_section.length_m,
                    dz_m=0.0,
                    **self._section_geometry_fields(condenser_section),
                    delta_p_friction_pa=float(condenser_friction_pa),
                ),
            ),
            driving_pressure_pa=float(driving_pressure_pa),
        )

    def one_pass(
        self,
        inputs: SteadyLoopInputs,
        circulation_factor: float,
        ngrid: int = 500,
    ) -> Optional[SteadyPassResult]:
        if inputs.geometry is not None and inputs.geometry is not self.geometry:
            inputs.geometry.validate_current_solver_sections()
            solver = SteadyLoopSolver(
                geometry=inputs.geometry,
                properties=self.properties,
                closure_name=self.closure_name,
            )
            return solver.one_pass(
                inputs=replace(inputs, geometry=None),
                circulation_factor=circulation_factor,
                ngrid=ngrid,
            )

        state = self.properties.state_at_temperature(inputs.tcon)
        total_heat_w = inputs.qtr * inputs.Li

        preboiling_length_fraction = (
            ((9.81 * inputs.H) * (state.v_l_m3_per_kg ** -1))
            * (1.0 + circulation_factor)
            * state.cp_l_j_per_kgk
        ) / (state.dp_sat_dT_pa_per_k * state.latent_heat_j_per_kg)
        if (not np.isfinite(preboiling_length_fraction)) or preboiling_length_fraction >= 1.0 or circulation_factor < 0.0:
            return None

        if inputs.mode == "distributed_steady":
            return self._one_pass_distributed(
                inputs=inputs,
                circulation_factor=circulation_factor,
                ngrid=ngrid,
                reference_state=state,
                total_heat_w=total_heat_w,
                preboiling_length_fraction=float(preboiling_length_fraction),
            )

        preboiling_evaporator_length_m = preboiling_length_fraction * inputs.Li
        preboiling_path_length_m = (
            inputs.H + self.geometry.inlet_section_length_m
        ) + preboiling_evaporator_length_m
        boiling_length_m = inputs.Li - preboiling_evaporator_length_m

        vapor_mass_flow_out_kg_s = total_heat_w / state.latent_heat_j_per_kg
        total_mass_flow_kg_s = vapor_mass_flow_out_kg_s * (1.0 + circulation_factor)
        liquid_mass_flow_in_kg_s = total_mass_flow_kg_s
        liquid_mass_flow_out_kg_s = total_mass_flow_kg_s - vapor_mass_flow_out_kg_s

        boiling_coordinate = np.linspace(float(preboiling_length_fraction) + 1e-8, 1.0, ngrid)
        vapor_mass_flow_profile_kg_s = (
            total_heat_w * (boiling_coordinate - preboiling_length_fraction)
        ) / (state.latent_heat_j_per_kg * (1.0 - preboiling_length_fraction))
        liquid_mass_flow_profile_kg_s = total_mass_flow_kg_s - vapor_mass_flow_profile_kg_s

        gas_reynolds = (vapor_mass_flow_profile_kg_s * self.geometry.hydraulic_diameter_m) / (
            state.mu_g_pa_s * self.geometry.flow_area_m2
        )
        liquid_reynolds = (liquid_mass_flow_profile_kg_s * self.geometry.hydraulic_diameter_m) / (
            state.mu_l_pa_s * self.geometry.flow_area_m2
        )
        gas_mass_flux = vapor_mass_flow_profile_kg_s / self.geometry.flow_area_m2
        liquid_mass_flux = liquid_mass_flow_profile_kg_s / self.geometry.flow_area_m2

        gas_friction_factor = self.friction_factor(gas_reynolds, self.geometry.relative_roughness, inputs)
        liquid_friction_factor = self.friction_factor(liquid_reynolds, self.geometry.relative_roughness, inputs)
        martinelli_x_profile = martinelli_parameter(
            liquid_mass_flow_kg_s=liquid_mass_flow_profile_kg_s,
            vapor_mass_flow_kg_s=vapor_mass_flow_profile_kg_s,
            liquid_friction_factor=liquid_friction_factor,
            gas_friction_factor=gas_friction_factor,
            liquid_specific_volume_m3_per_kg=state.v_l_m3_per_kg,
            vapor_specific_volume_m3_per_kg=state.v_g_m3_per_kg,
        )
        chisholm_c_profile = chisholm_constant(
            gas_reynolds=gas_reynolds,
            liquid_reynolds=liquid_reynolds,
        )
        two_phase_multiplier = two_phase_multiplier_liquid_reference(
            martinelli_x=martinelli_x_profile,
            chisholm_c=chisholm_c_profile,
        )
        boiling_closure_states = [
            closure_state_from_model(
                model=inputs.closure_model,
                vapor_mass_flow_kg_s=float(vapor_mass_flow_value),
                liquid_mass_flow_kg_s=float(liquid_mass_flow_value),
                gas_mass_flux_kg_m2_s=float(gas_mass_flux_value),
                liquid_mass_flux_kg_m2_s=float(liquid_mass_flux_value_m2),
                vapor_specific_volume_m3_per_kg=state.v_g_m3_per_kg,
                liquid_specific_volume_m3_per_kg=state.v_l_m3_per_kg,
                phi2l=float(two_phase_multiplier_value),
                orientation="horizontal",
                hydraulic_diameter_m=self.geometry.hydraulic_diameter_m,
                relative_roughness=self.geometry.relative_roughness,
                vapor_dynamic_viscosity_pa_s=state.mu_g_pa_s,
                liquid_dynamic_viscosity_pa_s=state.mu_l_pa_s,
                friction_model=self.effective_friction_model(inputs),
            )
            for vapor_mass_flow_value, liquid_mass_flow_value, gas_mass_flux_value, liquid_mass_flux_value_m2, two_phase_multiplier_value in zip(
                vapor_mass_flow_profile_kg_s,
                liquid_mass_flow_profile_kg_s,
                gas_mass_flux,
                liquid_mass_flux,
                two_phase_multiplier,
            )
        ]
        effective_two_phase_multiplier_profile = np.asarray(
            [
                closure_state.effective_two_phase_multiplier
                if closure_state.effective_two_phase_multiplier is not None
                else two_phase_multiplier_value
                for closure_state, two_phase_multiplier_value in zip(boiling_closure_states, two_phase_multiplier)
            ],
            dtype=float,
        )
        liquid_only_pressure_gradient = (
            liquid_friction_factor * state.v_l_m3_per_kg * liquid_mass_flux**2
        ) / (4.0 * self.geometry.inner_radius_m)
        two_phase_pressure_gradient_pa_per_m = np.asarray(
            [
                closure_state.friction_pressure_gradient_pa_per_m
                if closure_state.friction_pressure_gradient_pa_per_m is not None
                else effective_multiplier_value * liquid_only_gradient_value
                for closure_state, effective_multiplier_value, liquid_only_gradient_value in zip(
                    boiling_closure_states,
                    effective_two_phase_multiplier_profile,
                    liquid_only_pressure_gradient,
                )
            ],
            dtype=float,
        )
        two_phase_pressure_gradient = two_phase_pressure_gradient_pa_per_m * inputs.Li
        boiling_section_pressure_drop_pa = float(np.trapezoid(two_phase_pressure_gradient, boiling_coordinate))

        gas_reynolds_out = (vapor_mass_flow_out_kg_s * self.geometry.hydraulic_diameter_m) / (
            state.mu_g_pa_s * self.geometry.flow_area_m2
        )
        liquid_reynolds_out = (liquid_mass_flow_out_kg_s * self.geometry.hydraulic_diameter_m) / (
            state.mu_l_pa_s * self.geometry.flow_area_m2
        )
        gas_mass_flux_out = vapor_mass_flow_out_kg_s / self.geometry.flow_area_m2
        liquid_mass_flux_out = liquid_mass_flow_out_kg_s / self.geometry.flow_area_m2
        liquid_mass_flux_in = liquid_mass_flow_in_kg_s / self.geometry.flow_area_m2

        outlet_gas_friction_factor = self.friction_factor(gas_reynolds_out, self.geometry.relative_roughness, inputs)
        outlet_liquid_friction_factor = self.friction_factor(liquid_reynolds_out, self.geometry.relative_roughness, inputs)
        martinelli_x_out = martinelli_parameter(
            liquid_mass_flow_kg_s=liquid_mass_flow_out_kg_s,
            vapor_mass_flow_kg_s=vapor_mass_flow_out_kg_s,
            liquid_friction_factor=outlet_liquid_friction_factor,
            gas_friction_factor=outlet_gas_friction_factor,
            liquid_specific_volume_m3_per_kg=state.v_l_m3_per_kg,
            vapor_specific_volume_m3_per_kg=state.v_g_m3_per_kg,
        )
        chisholm_c_out = float(
            chisholm_constant(
                gas_reynolds=gas_reynolds_out,
                liquid_reynolds=liquid_reynolds_out,
            )
        )
        outlet_two_phase_multiplier = float(
            two_phase_multiplier_liquid_reference(
                martinelli_x=martinelli_x_out,
                chisholm_c=chisholm_c_out,
            )
        )
        outlet_closure_state = closure_state_from_model(
            model=inputs.closure_model,
            vapor_mass_flow_kg_s=vapor_mass_flow_out_kg_s,
            liquid_mass_flow_kg_s=liquid_mass_flow_out_kg_s,
            gas_mass_flux_kg_m2_s=gas_mass_flux_out,
            liquid_mass_flux_kg_m2_s=liquid_mass_flux_out,
            vapor_specific_volume_m3_per_kg=state.v_g_m3_per_kg,
            liquid_specific_volume_m3_per_kg=state.v_l_m3_per_kg,
            phi2l=outlet_two_phase_multiplier,
            orientation="horizontal",
            hydraulic_diameter_m=self.geometry.hydraulic_diameter_m,
            relative_roughness=self.geometry.relative_roughness,
            vapor_dynamic_viscosity_pa_s=state.mu_g_pa_s,
            liquid_dynamic_viscosity_pa_s=state.mu_l_pa_s,
            friction_model=self.effective_friction_model(inputs),
        )
        liquid_volume_fraction_out = outlet_closure_state.liquid_volume_fraction
        gas_volume_fraction_out = outlet_closure_state.gas_volume_fraction

        gas_velocity_out_m_s = outlet_closure_state.gas_velocity_m_s
        liquid_velocity_out_m_s = outlet_closure_state.liquid_velocity_m_s
        liquid_velocity_in_m_s = liquid_mass_flux_in * state.v_l_m3_per_kg
        acceleration_pressure_drop_pa = (
            ((state.v_l_m3_per_kg ** -1) * (liquid_velocity_out_m_s**2) * liquid_volume_fraction_out)
            + ((state.v_g_m3_per_kg ** -1) * (gas_velocity_out_m_s**2) * gas_volume_fraction_out)
            - ((state.v_l_m3_per_kg ** -1) * (liquid_velocity_in_m_s**2))
        )

        liquid_reynolds_in = (liquid_mass_flow_in_kg_s * self.geometry.hydraulic_diameter_m) / (
            state.mu_l_pa_s * self.geometry.flow_area_m2
        )
        inlet_liquid_pressure_drop_pa = (
            (self.friction_factor(liquid_reynolds_in, self.geometry.relative_roughness, inputs) * preboiling_path_length_m)
            * state.v_l_m3_per_kg
            * (liquid_mass_flux_in**2)
        ) / (self.geometry.inner_radius_m * 4.0)
        outlet_liquid_only_pressure_gradient = (
            outlet_liquid_friction_factor * state.v_l_m3_per_kg * (liquid_mass_flux_out**2)
        ) / (4.0 * self.geometry.inner_radius_m)
        outlet_effective_two_phase_multiplier = (
            outlet_closure_state.effective_two_phase_multiplier
            if outlet_closure_state.effective_two_phase_multiplier is not None
            else outlet_two_phase_multiplier
        )
        outlet_friction_pressure_gradient_pa_per_m = (
            outlet_closure_state.friction_pressure_gradient_pa_per_m
            if outlet_closure_state.friction_pressure_gradient_pa_per_m is not None
            else outlet_effective_two_phase_multiplier * outlet_liquid_only_pressure_gradient
        )
        outlet_section_pressure_drop_pa = (
            outlet_friction_pressure_gradient_pa_per_m
            * self.geometry.outlet_section_length_m
        )

        outlet_mixture_density_kg_m3 = outlet_closure_state.mixture_density_kg_m3
        effective_density_difference_kg_m3 = (state.v_l_m3_per_kg ** -1) - outlet_mixture_density_kg_m3
        driving_pressure_pa = 9.81 * inputs.H * effective_density_difference_kg_m3
        total_pressure_drop_pa = (
            boiling_section_pressure_drop_pa
            + inlet_liquid_pressure_drop_pa
            + outlet_section_pressure_drop_pa
            + acceleration_pressure_drop_pa
        )
        required_head_m = total_pressure_drop_pa / (
            9.81 * effective_density_difference_kg_m3
        )

        outlet_mass_quality = 1.0 / (1.0 + circulation_factor)
        liquid_mass_flow_out_lph = liquid_mass_flow_out_kg_s * state.v_l_m3_per_kg * 1000.0 * 3600.0
        liquid_mass_flow_in_lph = liquid_mass_flow_in_kg_s * state.v_l_m3_per_kg * 1000.0 * 3600.0
        vapor_mass_flow_liq_equiv_lph = vapor_mass_flow_out_kg_s * state.v_l_m3_per_kg * 1000.0 * 3600.0
        vapor_mass_flow_gas_lph = vapor_mass_flow_out_kg_s * state.v_g_m3_per_kg * 1000.0 * 3600.0
        outlet_gas_volume_fraction_true = (vapor_mass_flow_out_kg_s * state.v_g_m3_per_kg) / (
            (vapor_mass_flow_out_kg_s * state.v_g_m3_per_kg)
            + (liquid_mass_flow_out_kg_s * state.v_l_m3_per_kg)
        )
        inlet_liquid_pressure_gradient_pa_per_m = (
            inlet_liquid_pressure_drop_pa / preboiling_path_length_m if preboiling_path_length_m > 0.0 else 0.0
        )

        evaporator_coordinate = np.linspace(0.0, 1.0, ngrid)
        evaporator_axial_position_m = evaporator_coordinate * inputs.Li
        boiling_mask = evaporator_coordinate >= preboiling_length_fraction
        preboiling_mask = ~boiling_mask
        phase_regime = np.where(preboiling_mask, "single_liquid_heating", "boiling_two_phase")

        vapor_mass_flow_profile_full_kg_s = np.where(
            boiling_mask,
            (total_heat_w * (evaporator_coordinate - preboiling_length_fraction))
            / (state.latent_heat_j_per_kg * (1.0 - preboiling_length_fraction)),
            0.0,
        )
        liquid_mass_flow_profile_full_kg_s = total_mass_flow_kg_s - vapor_mass_flow_profile_full_kg_s

        gas_reynolds_full = np.full(ngrid, np.nan, dtype=float)
        liquid_reynolds_full = np.full(ngrid, liquid_reynolds_in, dtype=float)
        martinelli_x_full = np.full(ngrid, np.nan, dtype=float)
        two_phase_multiplier_full = np.ones(ngrid, dtype=float)
        pressure_gradient_full_pa_per_m = np.full(ngrid, inlet_liquid_pressure_gradient_pa_per_m, dtype=float)
        gas_volume_fraction_full = np.zeros(ngrid, dtype=float)
        liquid_volume_fraction_full = np.ones(ngrid, dtype=float)
        gas_superficial_velocity_full_m_s = np.zeros(ngrid, dtype=float)
        liquid_superficial_velocity_full_m_s = np.full(
            ngrid,
            liquid_mass_flux_in * state.v_l_m3_per_kg,
            dtype=float,
        )
        slip_ratio_full = np.zeros(ngrid, dtype=float)

        if np.any(boiling_mask):
            boiling_gas_volume_fraction = np.asarray(
                [closure_state.gas_volume_fraction for closure_state in boiling_closure_states],
                dtype=float,
            )
            boiling_liquid_volume_fraction = np.asarray(
                [closure_state.liquid_volume_fraction for closure_state in boiling_closure_states],
                dtype=float,
            )
            boiling_slip_ratio = np.asarray(
                [closure_state.slip_ratio for closure_state in boiling_closure_states],
                dtype=float,
            )
            boiling_gas_superficial_velocity_m_s = gas_mass_flux * state.v_g_m3_per_kg
            boiling_liquid_superficial_velocity_m_s = liquid_mass_flux * state.v_l_m3_per_kg
            gas_reynolds_full[boiling_mask] = np.interp(evaporator_coordinate[boiling_mask], boiling_coordinate, gas_reynolds)
            liquid_reynolds_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                liquid_reynolds,
            )
            martinelli_x_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                martinelli_x_profile,
            )
            two_phase_multiplier_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                effective_two_phase_multiplier_profile,
            )
            pressure_gradient_full_pa_per_m[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                two_phase_pressure_gradient_pa_per_m,
            )
            gas_volume_fraction_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                boiling_gas_volume_fraction,
            )
            liquid_volume_fraction_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                boiling_liquid_volume_fraction,
            )
            gas_superficial_velocity_full_m_s[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                boiling_gas_superficial_velocity_m_s,
            )
            liquid_superficial_velocity_full_m_s[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                boiling_liquid_superficial_velocity_m_s,
            )
            slip_ratio_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                boiling_slip_ratio,
            )

        if inputs.mode == "distributed_steady":
            subcool_delta_t_c = (
                preboiling_length_fraction * state.latent_heat_j_per_kg / ((1.0 + circulation_factor) * state.cp_l_j_per_kgk)
            )
            inlet_liquid_temperature_c = inputs.tcon - subcool_delta_t_c
            local_temperature_profile_c = np.full(ngrid, inputs.tcon, dtype=float)
            local_pressure_profile_pa = np.full(ngrid, state.pressure_pa, dtype=float)

            if np.any(preboiling_mask) and preboiling_evaporator_length_m > 0.0:
                preboiling_progress = evaporator_axial_position_m[preboiling_mask] / preboiling_evaporator_length_m
                local_temperature_profile_c[preboiling_mask] = (
                    inlet_liquid_temperature_c + preboiling_progress * subcool_delta_t_c
                )
                local_pressure_profile_pa[preboiling_mask] = state.pressure_pa + (
                    inlet_liquid_pressure_gradient_pa_per_m
                    * (preboiling_evaporator_length_m - evaporator_axial_position_m[preboiling_mask])
                )
                liquid_mu_pre = self.properties.liquid_dynamic_viscosity_pa_s(local_temperature_profile_c[preboiling_mask])
                liquid_reynolds_full[preboiling_mask] = (
                    liquid_mass_flow_in_kg_s * self.geometry.hydraulic_diameter_m
                ) / (liquid_mu_pre * self.geometry.flow_area_m2)

            boiling_axial_position_m = boiling_coordinate * inputs.Li
            cumulative_boil_pressure_drop_pa = np.zeros_like(boiling_axial_position_m, dtype=float)
            if len(boiling_axial_position_m) > 1:
                dp_steps = 0.5 * (two_phase_pressure_gradient_pa_per_m[1:] + two_phase_pressure_gradient_pa_per_m[:-1]) * np.diff(
                    boiling_axial_position_m
                )
                cumulative_boil_pressure_drop_pa[1:] = np.cumsum(dp_steps)
            boiling_pressure_profile_pa = state.pressure_pa - cumulative_boil_pressure_drop_pa
            boiling_temperature_profile_c = self.properties.temperature_from_pressure_pa(boiling_pressure_profile_pa)
            local_pressure_profile_pa[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                boiling_pressure_profile_pa,
            )
            local_temperature_profile_c[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                boiling_coordinate,
                boiling_temperature_profile_c,
            )
        else:
            local_temperature_profile_c = np.full(ngrid, inputs.tcon, dtype=float)
            local_pressure_profile_pa = np.full(ngrid, state.pressure_pa, dtype=float)

        single_liquid_regime = single_liquid_heating_classification()
        flow_regime_full = np.full(ngrid, single_liquid_regime.name, dtype=object)
        (
            flow_regime_source_full,
            flow_regime_status_full,
            flow_regime_transition_criteria_full,
            flow_regime_confidence_full,
        ) = _regime_metadata_arrays(ngrid, single_liquid_regime)
        if np.any(boiling_mask):
            if self.effective_closure_model(inputs) == "experimental_regime_aware":
                boiling_regime_profile = [closure_state.diagnostic_regime or "boiling_two_phase" for closure_state in boiling_closure_states]
                boiling_regime_source_profile = [
                    closure_state.diagnostic_regime_source or "experimental_regime_aware heuristic thresholds; no primary source"
                    for closure_state in boiling_closure_states
                ]
                boiling_regime_status_profile = [
                    closure_state.diagnostic_regime_status or "experimental"
                    for closure_state in boiling_closure_states
                ]
                boiling_regime_transition_profile = [
                    closure_state.diagnostic_regime_transition_criteria or "legacy experimental fallback"
                    for closure_state in boiling_closure_states
                ]
                boiling_regime_confidence_profile = [
                    closure_state.diagnostic_regime_confidence or "heuristic"
                    for closure_state in boiling_closure_states
                ]
                boiling_indices = np.searchsorted(boiling_coordinate, evaporator_coordinate[boiling_mask], side="left")
                boiling_indices = np.clip(boiling_indices, 0, len(boiling_regime_profile) - 1)
                flow_regime_full[boiling_mask] = np.asarray(
                    [boiling_regime_profile[int(index)] for index in boiling_indices],
                    dtype=object,
                )
                flow_regime_source_full[boiling_mask] = np.asarray(
                    [boiling_regime_source_profile[int(index)] for index in boiling_indices],
                    dtype=object,
                )
                flow_regime_status_full[boiling_mask] = np.asarray(
                    [boiling_regime_status_profile[int(index)] for index in boiling_indices],
                    dtype=object,
                )
                flow_regime_transition_criteria_full[boiling_mask] = np.asarray(
                    [boiling_regime_transition_profile[int(index)] for index in boiling_indices],
                    dtype=object,
                )
                flow_regime_confidence_full[boiling_mask] = np.asarray(
                    [boiling_regime_confidence_profile[int(index)] for index in boiling_indices],
                    dtype=object,
                )
            else:
                for point_index in np.where(boiling_mask)[0]:
                    regime_classification = classify_horizontal_evaporator_regime_result(
                        mass_quality=float(vapor_mass_flow_profile_full_kg_s[point_index] / max(total_mass_flow_kg_s, 1e-12)),
                        gas_volume_fraction=float(gas_volume_fraction_full[point_index]),
                        gas_superficial_velocity_m_s=float(gas_superficial_velocity_full_m_s[point_index]),
                        liquid_superficial_velocity_m_s=float(liquid_superficial_velocity_full_m_s[point_index]),
                        slip_ratio=float(slip_ratio_full[point_index]),
                    )
                    flow_regime_full[point_index] = regime_classification.name
                    _write_regime_metadata(
                        source_values=flow_regime_source_full,
                        status_values=flow_regime_status_full,
                        transition_values=flow_regime_transition_criteria_full,
                        confidence_values=flow_regime_confidence_full,
                        index=int(point_index),
                        classification=regime_classification,
                    )

        evaporator_segment_lengths_m = np.full(ngrid, inputs.Li / max(ngrid, 1), dtype=float)
        evaporator_regime_fractions = summarize_regime_fractions(
            regimes=[str(value) for value in flow_regime_full.tolist()],
            segment_lengths_m=evaporator_segment_lengths_m.tolist(),
        )
        evaporator_dominant_flow_regime = dominant_regime(evaporator_regime_fractions)
        evaporator_flow_regime_summary = format_regime_summary(evaporator_regime_fractions)

        evaporator_profile = EvaporatorProfile(
            coordinate_0_1=tuple(np.asarray(evaporator_coordinate, dtype=float).tolist()),
            axial_position_m=tuple(np.asarray(evaporator_axial_position_m, dtype=float).tolist()),
            phase_regime=tuple(str(value) for value in phase_regime.tolist()),
            flow_regime=tuple(str(value) for value in flow_regime_full.tolist()),
            local_temperature_c=tuple(np.asarray(local_temperature_profile_c, dtype=float).tolist()),
            local_pressure_pa=tuple(np.asarray(local_pressure_profile_pa, dtype=float).tolist()),
            vapor_mass_flow_kg_s=tuple(np.asarray(vapor_mass_flow_profile_full_kg_s, dtype=float).tolist()),
            liquid_mass_flow_kg_s=tuple(np.asarray(liquid_mass_flow_profile_full_kg_s, dtype=float).tolist()),
            gas_volume_fraction=tuple(np.asarray(gas_volume_fraction_full, dtype=float).tolist()),
            liquid_volume_fraction=tuple(np.asarray(liquid_volume_fraction_full, dtype=float).tolist()),
            gas_superficial_velocity_m_s=tuple(np.asarray(gas_superficial_velocity_full_m_s, dtype=float).tolist()),
            liquid_superficial_velocity_m_s=tuple(np.asarray(liquid_superficial_velocity_full_m_s, dtype=float).tolist()),
            slip_ratio=tuple(np.asarray(slip_ratio_full, dtype=float).tolist()),
            gas_reynolds=tuple(np.asarray(gas_reynolds_full, dtype=float).tolist()),
            liquid_reynolds=tuple(np.asarray(liquid_reynolds_full, dtype=float).tolist()),
            martinelli_x=tuple(np.asarray(martinelli_x_full, dtype=float).tolist()),
            two_phase_multiplier=tuple(np.asarray(two_phase_multiplier_full, dtype=float).tolist()),
            two_phase_pressure_gradient_pa_per_m=tuple(np.asarray(pressure_gradient_full_pa_per_m, dtype=float).tolist()),
            flow_regime_source=tuple(str(value) for value in flow_regime_source_full.tolist()),
            flow_regime_status=tuple(str(value) for value in flow_regime_status_full.tolist()),
            flow_regime_transition_criteria=tuple(str(value) for value in flow_regime_transition_criteria_full.tolist()),
            flow_regime_confidence=tuple(str(value) for value in flow_regime_confidence_full.tolist()),
        )

        riser_section = self.geometry.riser_section(height_m=inputs.H)
        downcomer_section = self.geometry.downcomer_section()
        preboiling_evaporator_section = self.geometry.evaporator_section(
            length_m=preboiling_evaporator_length_m,
            name="evaporator_preboiling",
        )
        boiling_evaporator_section = self.geometry.evaporator_section(
            length_m=boiling_length_m,
            name="evaporator_boiling",
        )
        condenser_section = self.geometry.condenser_section()
        riser_dominant_flow_regime = "single_liquid"
        riser_section_pressure_drop_pa = inlet_liquid_pressure_gradient_pa_per_m * riser_section.length_m
        downcomer_friction_pa = inlet_liquid_pressure_gradient_pa_per_m * downcomer_section.length_m
        preboiling_evaporator_friction_pa = (
            inlet_liquid_pressure_gradient_pa_per_m * preboiling_evaporator_section.length_m
        )
        downcomer_dz_m = downcomer_section.dz_m if downcomer_section.dz_m != 0.0 else -abs(riser_section.length_m)
        downcomer_hydrostatic_pa = hydrostatic_pressure_pa(state.v_l_m3_per_kg ** -1, downcomer_dz_m)
        riser_hydrostatic_pa = hydrostatic_pressure_pa(outlet_mixture_density_kg_m3, riser_section.dz_m)
        pressure_balance = self._build_pressure_balance(
            downcomer_section=downcomer_section,
            riser_section=riser_section,
            preboiling_evaporator_section=preboiling_evaporator_section,
            boiling_evaporator_section=boiling_evaporator_section,
            condenser_section=condenser_section,
            downcomer_friction_pa=downcomer_friction_pa,
            riser_friction_pa=riser_section_pressure_drop_pa,
            preboiling_evaporator_friction_pa=preboiling_evaporator_friction_pa,
            boiling_evaporator_friction_pa=boiling_section_pressure_drop_pa,
            condenser_friction_pa=outlet_section_pressure_drop_pa,
            acceleration_pressure_drop_pa=acceleration_pressure_drop_pa,
            downcomer_hydrostatic_pa=downcomer_hydrostatic_pa,
            riser_hydrostatic_pa=riser_hydrostatic_pa,
            driving_pressure_pa=driving_pressure_pa,
        )
        section_states = (
            LoopSectionState(
                section_name=downcomer_section.name,
                section_kind=downcomer_section.section_kind,
                orientation=downcomer_section.orientation,
                length_m=downcomer_section.length_m,
                phase_regime="single_liquid",
                pressure_drop_pa=float(downcomer_friction_pa),
                inlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_in_kg_s),
                inlet_vapor_mass_flow_kg_s=0.0,
                outlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_in_kg_s),
                outlet_vapor_mass_flow_kg_s=0.0,
            ),
            LoopSectionState(
                section_name=riser_section.name,
                section_kind=riser_section.section_kind,
                orientation=riser_section.orientation,
                length_m=riser_section.length_m,
                phase_regime=riser_dominant_flow_regime or "two_phase_riser",
                pressure_drop_pa=float(riser_section_pressure_drop_pa),
                inlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_out_kg_s),
                inlet_vapor_mass_flow_kg_s=float(vapor_mass_flow_out_kg_s),
                outlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_out_kg_s),
                outlet_vapor_mass_flow_kg_s=float(vapor_mass_flow_out_kg_s),
            ),
            LoopSectionState(
                section_name=preboiling_evaporator_section.name,
                section_kind=preboiling_evaporator_section.section_kind,
                orientation=preboiling_evaporator_section.orientation,
                length_m=preboiling_evaporator_section.length_m,
                phase_regime="single_liquid_heating",
                pressure_drop_pa=float(preboiling_evaporator_friction_pa),
                inlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_in_kg_s),
                inlet_vapor_mass_flow_kg_s=0.0,
                outlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_in_kg_s),
                outlet_vapor_mass_flow_kg_s=0.0,
            ),
            LoopSectionState(
                section_name=boiling_evaporator_section.name,
                section_kind=boiling_evaporator_section.section_kind,
                orientation=boiling_evaporator_section.orientation,
                length_m=boiling_evaporator_section.length_m,
                phase_regime="boiling_two_phase",
                pressure_drop_pa=float(boiling_section_pressure_drop_pa),
                inlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_in_kg_s),
                inlet_vapor_mass_flow_kg_s=0.0,
                outlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_out_kg_s),
                outlet_vapor_mass_flow_kg_s=float(vapor_mass_flow_out_kg_s),
            ),
            LoopSectionState(
                section_name=condenser_section.name,
                section_kind=condenser_section.section_kind,
                orientation=condenser_section.orientation,
                length_m=condenser_section.length_m,
                phase_regime="condensing_two_phase",
                pressure_drop_pa=float(outlet_section_pressure_drop_pa),
                inlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_out_kg_s),
                inlet_vapor_mass_flow_kg_s=float(vapor_mass_flow_out_kg_s),
                outlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_out_kg_s),
                outlet_vapor_mass_flow_kg_s=float(vapor_mass_flow_out_kg_s),
            ),
        )

        return SteadyPassResult(
            total_heat_w=float(total_heat_w),
            preboiling_length_fraction=float(preboiling_length_fraction),
            preboiling_evaporator_length_m=float(preboiling_evaporator_length_m),
            preboiling_path_length_m=float(preboiling_path_length_m),
            boiling_length_m=float(boiling_length_m),
            boiling_onset_position_m=float(preboiling_evaporator_length_m),
            vapor_mass_flow_out_kg_s=float(vapor_mass_flow_out_kg_s),
            liquid_mass_flow_out_kg_s=float(liquid_mass_flow_out_kg_s),
            liquid_mass_flow_in_kg_s=float(liquid_mass_flow_in_kg_s),
            outlet_gas_volume_fraction_closure=float(gas_volume_fraction_out),
            outlet_liquid_volume_fraction_closure=float(liquid_volume_fraction_out),
            gas_velocity_out_m_s=float(gas_velocity_out_m_s),
            liquid_velocity_out_m_s=float(liquid_velocity_out_m_s),
            liquid_velocity_in_m_s=float(liquid_velocity_in_m_s),
            total_pressure_drop_pa=float(total_pressure_drop_pa),
            boiling_section_pressure_drop_pa=float(boiling_section_pressure_drop_pa),
            inlet_liquid_pressure_drop_pa=float(inlet_liquid_pressure_drop_pa),
            outlet_section_pressure_drop_pa=float(outlet_section_pressure_drop_pa),
            acceleration_pressure_drop_pa=float(acceleration_pressure_drop_pa),
            outlet_mixture_density_kg_m3=float(outlet_mixture_density_kg_m3),
            required_head_m=float(required_head_m),
            outlet_mass_quality=float(outlet_mass_quality),
            liquid_mass_flow_out_lph=float(liquid_mass_flow_out_lph),
            liquid_mass_flow_in_lph=float(liquid_mass_flow_in_lph),
            vapor_mass_flow_liq_equiv_lph=float(vapor_mass_flow_liq_equiv_lph),
            vapor_mass_flow_gas_lph=float(vapor_mass_flow_gas_lph),
            outlet_gas_volume_fraction_true=float(outlet_gas_volume_fraction_true),
            outlet_slip_ratio=float(outlet_closure_state.slip_ratio),
            outlet_selected_void_fraction_model=outlet_closure_state.selected_void_fraction_model,
            outlet_selected_friction_model=outlet_closure_state.selected_friction_model,
            driving_pressure_pa=float(driving_pressure_pa),
            effective_density_difference_kg_m3=float(effective_density_difference_kg_m3),
            evaporator_dominant_flow_regime=evaporator_dominant_flow_regime,
            riser_dominant_flow_regime="",
            evaporator_flow_regime_summary=evaporator_flow_regime_summary,
            riser_flow_regime_summary="",
            friction_model=self.effective_friction_model(inputs),
            pressure_balance=pressure_balance,
            model_mode=inputs.mode,
            geometry_source=self.geometry.geometry_source,
            section_states=section_states,
            evaporator_profile=evaporator_profile,
            riser_profile=None,
        )

    def _one_pass_distributed(
        self,
        inputs: SteadyLoopInputs,
        circulation_factor: float,
        ngrid: int,
        reference_state,
        total_heat_w: float,
        preboiling_length_fraction: float,
    ) -> Optional[SteadyPassResult]:
        preboiling_evaporator_length_m = preboiling_length_fraction * inputs.Li
        preboiling_path_length_m = self.geometry.inlet_section_length_m + preboiling_evaporator_length_m
        boiling_length_m = inputs.Li - preboiling_evaporator_length_m
        if boiling_length_m <= 0.0:
            return None

        subcool_delta_t_c = (
            preboiling_length_fraction
            * reference_state.latent_heat_j_per_kg
            / ((1.0 + circulation_factor) * reference_state.cp_l_j_per_kgk)
        )
        inlet_liquid_temperature_c = inputs.tcon - subcool_delta_t_c
        preboiling_reference_temperature_c = 0.5 * (inlet_liquid_temperature_c + inputs.tcon)
        preboiling_state = self.properties.state_at_temperature(preboiling_reference_temperature_c)

        vapor_mass_flow_out_guess_kg_s = total_heat_w / reference_state.latent_heat_j_per_kg
        n_boil = max(ngrid, 25)
        cell_edges_m = np.linspace(preboiling_evaporator_length_m, inputs.Li, n_boil + 1, dtype=float)
        cell_widths_m = np.diff(cell_edges_m)
        cell_centers_m = 0.5 * (cell_edges_m[:-1] + cell_edges_m[1:])
        cell_center_coordinate = cell_centers_m / inputs.Li
        onset_pressure_pa = reference_state.pressure_pa

        final_vapor_mass_flow_profile_kg_s = None
        final_liquid_mass_flow_profile_kg_s = None
        final_gas_reynolds = None
        final_liquid_reynolds = None
        final_martinelli_x = None
        final_two_phase_multiplier = None
        final_two_phase_pressure_gradient_pa_per_m = None
        final_liquid_volume_fraction = None
        final_gas_volume_fraction = None
        final_mixture_density_kg_m3 = None
        final_gas_superficial_velocity_m_s = None
        final_liquid_superficial_velocity_m_s = None
        final_slip_ratio = None
        final_diagnostic_regime = None
        final_diagnostic_regime_source = None
        final_diagnostic_regime_status = None
        final_diagnostic_regime_transition_criteria = None
        final_diagnostic_regime_confidence = None
        final_pressure_profile_pa = None
        final_temperature_profile_c = None
        final_vapor_mass_flow_out_kg_s = None
        final_outlet_state = None

        for _ in range(8):
            total_mass_flow_kg_s = vapor_mass_flow_out_guess_kg_s * (1.0 + circulation_factor)
            vapor_mass_flow_in_kg_s = 0.0
            local_pressure_pa = onset_pressure_pa

            vapor_mass_flow_profile = np.zeros(n_boil, dtype=float)
            liquid_mass_flow_profile = np.zeros(n_boil, dtype=float)
            gas_reynolds_profile = np.zeros(n_boil, dtype=float)
            liquid_reynolds_profile = np.zeros(n_boil, dtype=float)
            martinelli_x_profile = np.zeros(n_boil, dtype=float)
            two_phase_multiplier_profile = np.zeros(n_boil, dtype=float)
            two_phase_pressure_gradient_profile = np.zeros(n_boil, dtype=float)
            liquid_volume_fraction_profile = np.zeros(n_boil, dtype=float)
            gas_volume_fraction_profile = np.zeros(n_boil, dtype=float)
            mixture_density_profile = np.zeros(n_boil, dtype=float)
            gas_superficial_velocity_profile_m_s = np.zeros(n_boil, dtype=float)
            liquid_superficial_velocity_profile_m_s = np.zeros(n_boil, dtype=float)
            slip_ratio_profile = np.zeros(n_boil, dtype=float)
            diagnostic_regime_profile = np.full(n_boil, "", dtype=object)
            diagnostic_regime_source_profile = np.full(n_boil, "", dtype=object)
            diagnostic_regime_status_profile = np.full(n_boil, "", dtype=object)
            diagnostic_regime_transition_profile = np.full(n_boil, "", dtype=object)
            diagnostic_regime_confidence_profile = np.full(n_boil, "", dtype=object)
            pressure_profile_pa = np.zeros(n_boil, dtype=float)
            temperature_profile_c = np.zeros(n_boil, dtype=float)

            for idx, cell_width_m in enumerate(cell_widths_m):
                local_temperature_c = float(self.properties.temperature_from_pressure_pa(local_pressure_pa))
                local_state = self.properties.state_at_temperature(local_temperature_c)
                cell_evaporation_kg_s = inputs.qtr * cell_width_m / local_state.latent_heat_j_per_kg
                vapor_mass_flow_center_kg_s = vapor_mass_flow_in_kg_s + 0.5 * cell_evaporation_kg_s
                liquid_mass_flow_center_kg_s = total_mass_flow_kg_s - vapor_mass_flow_center_kg_s
                if liquid_mass_flow_center_kg_s <= 0.0:
                    return None

                gas_reynolds = (vapor_mass_flow_center_kg_s * self.geometry.hydraulic_diameter_m) / (
                    local_state.mu_g_pa_s * self.geometry.flow_area_m2
                )
                liquid_reynolds = (liquid_mass_flow_center_kg_s * self.geometry.hydraulic_diameter_m) / (
                    local_state.mu_l_pa_s * self.geometry.flow_area_m2
                )
                gas_friction_factor = self.friction_factor(gas_reynolds, self.geometry.relative_roughness, inputs)
                liquid_friction_factor = self.friction_factor(liquid_reynolds, self.geometry.relative_roughness, inputs)
                martinelli_x = float(
                    martinelli_parameter(
                        liquid_mass_flow_kg_s=liquid_mass_flow_center_kg_s,
                        vapor_mass_flow_kg_s=vapor_mass_flow_center_kg_s,
                        liquid_friction_factor=liquid_friction_factor,
                        gas_friction_factor=gas_friction_factor,
                        liquid_specific_volume_m3_per_kg=local_state.v_l_m3_per_kg,
                        vapor_specific_volume_m3_per_kg=local_state.v_g_m3_per_kg,
                    )
                )
                chisholm_c = float(
                    chisholm_constant(
                        gas_reynolds=gas_reynolds,
                        liquid_reynolds=liquid_reynolds,
                    )
                )
                two_phase_multiplier = float(
                    two_phase_multiplier_liquid_reference(
                        martinelli_x=martinelli_x,
                        chisholm_c=chisholm_c,
                    )
                )
                gas_mass_flux = vapor_mass_flow_center_kg_s / self.geometry.flow_area_m2
                liquid_mass_flux = liquid_mass_flow_center_kg_s / self.geometry.flow_area_m2
                liquid_only_pressure_gradient_pa_per_m = (
                    liquid_friction_factor * local_state.v_l_m3_per_kg * liquid_mass_flux**2
                ) / (4.0 * self.geometry.inner_radius_m)
                cell_closure_state = closure_state_from_model(
                    model=inputs.closure_model,
                    vapor_mass_flow_kg_s=vapor_mass_flow_center_kg_s,
                    liquid_mass_flow_kg_s=liquid_mass_flow_center_kg_s,
                    gas_mass_flux_kg_m2_s=gas_mass_flux,
                    liquid_mass_flux_kg_m2_s=liquid_mass_flux,
                    vapor_specific_volume_m3_per_kg=local_state.v_g_m3_per_kg,
                    liquid_specific_volume_m3_per_kg=local_state.v_l_m3_per_kg,
                    phi2l=two_phase_multiplier,
                    orientation="horizontal",
                    hydraulic_diameter_m=self.geometry.hydraulic_diameter_m,
                    relative_roughness=self.geometry.relative_roughness,
                    vapor_dynamic_viscosity_pa_s=local_state.mu_g_pa_s,
                    liquid_dynamic_viscosity_pa_s=local_state.mu_l_pa_s,
                    friction_model=self.effective_friction_model(inputs),
                )
                effective_two_phase_multiplier = (
                    cell_closure_state.effective_two_phase_multiplier
                    if cell_closure_state.effective_two_phase_multiplier is not None
                    else two_phase_multiplier
                )
                two_phase_pressure_gradient_pa_per_m = (
                    cell_closure_state.friction_pressure_gradient_pa_per_m
                    if cell_closure_state.friction_pressure_gradient_pa_per_m is not None
                    else effective_two_phase_multiplier * liquid_only_pressure_gradient_pa_per_m
                )
                mixture_density_kg_m3 = cell_closure_state.mixture_density_kg_m3
                gas_superficial_velocity_m_s = gas_mass_flux * local_state.v_g_m3_per_kg
                liquid_superficial_velocity_m_s = liquid_mass_flux * local_state.v_l_m3_per_kg

                pressure_profile_pa[idx] = local_pressure_pa
                temperature_profile_c[idx] = local_temperature_c
                vapor_mass_flow_profile[idx] = vapor_mass_flow_center_kg_s
                liquid_mass_flow_profile[idx] = liquid_mass_flow_center_kg_s
                gas_reynolds_profile[idx] = gas_reynolds
                liquid_reynolds_profile[idx] = liquid_reynolds
                martinelli_x_profile[idx] = martinelli_x
                two_phase_multiplier_profile[idx] = effective_two_phase_multiplier
                two_phase_pressure_gradient_profile[idx] = two_phase_pressure_gradient_pa_per_m
                liquid_volume_fraction_profile[idx] = cell_closure_state.liquid_volume_fraction
                gas_volume_fraction_profile[idx] = cell_closure_state.gas_volume_fraction
                mixture_density_profile[idx] = mixture_density_kg_m3
                gas_superficial_velocity_profile_m_s[idx] = gas_superficial_velocity_m_s
                liquid_superficial_velocity_profile_m_s[idx] = liquid_superficial_velocity_m_s
                slip_ratio_profile[idx] = cell_closure_state.slip_ratio
                diagnostic_regime_profile[idx] = cell_closure_state.diagnostic_regime
                diagnostic_regime_source_profile[idx] = cell_closure_state.diagnostic_regime_source
                diagnostic_regime_status_profile[idx] = cell_closure_state.diagnostic_regime_status
                diagnostic_regime_transition_profile[idx] = cell_closure_state.diagnostic_regime_transition_criteria
                diagnostic_regime_confidence_profile[idx] = cell_closure_state.diagnostic_regime_confidence

                local_pressure_pa -= two_phase_pressure_gradient_pa_per_m * cell_width_m
                vapor_mass_flow_in_kg_s += cell_evaporation_kg_s

            updated_vapor_mass_flow_out_kg_s = float(vapor_mass_flow_in_kg_s)
            final_vapor_mass_flow_profile_kg_s = vapor_mass_flow_profile
            final_liquid_mass_flow_profile_kg_s = liquid_mass_flow_profile
            final_gas_reynolds = gas_reynolds_profile
            final_liquid_reynolds = liquid_reynolds_profile
            final_martinelli_x = martinelli_x_profile
            final_two_phase_multiplier = two_phase_multiplier_profile
            final_two_phase_pressure_gradient_pa_per_m = two_phase_pressure_gradient_profile
            final_liquid_volume_fraction = liquid_volume_fraction_profile
            final_gas_volume_fraction = gas_volume_fraction_profile
            final_mixture_density_kg_m3 = mixture_density_profile
            final_gas_superficial_velocity_m_s = gas_superficial_velocity_profile_m_s
            final_liquid_superficial_velocity_m_s = liquid_superficial_velocity_profile_m_s
            final_slip_ratio = slip_ratio_profile
            final_diagnostic_regime = diagnostic_regime_profile
            final_diagnostic_regime_source = diagnostic_regime_source_profile
            final_diagnostic_regime_status = diagnostic_regime_status_profile
            final_diagnostic_regime_transition_criteria = diagnostic_regime_transition_profile
            final_diagnostic_regime_confidence = diagnostic_regime_confidence_profile
            final_pressure_profile_pa = pressure_profile_pa
            final_temperature_profile_c = temperature_profile_c
            final_vapor_mass_flow_out_kg_s = updated_vapor_mass_flow_out_kg_s
            final_outlet_state = self.properties.state_at_temperature(
                float(self.properties.temperature_from_pressure_pa(local_pressure_pa))
            )

            if abs(updated_vapor_mass_flow_out_kg_s - vapor_mass_flow_out_guess_kg_s) <= max(
                1e-10,
                1e-6 * max(updated_vapor_mass_flow_out_kg_s, 1e-10),
            ):
                break
            vapor_mass_flow_out_guess_kg_s = 0.5 * (
                vapor_mass_flow_out_guess_kg_s + updated_vapor_mass_flow_out_kg_s
            )

        if (
            final_vapor_mass_flow_profile_kg_s is None
            or final_liquid_mass_flow_profile_kg_s is None
            or final_gas_reynolds is None
            or final_liquid_reynolds is None
            or final_martinelli_x is None
            or final_two_phase_multiplier is None
            or final_two_phase_pressure_gradient_pa_per_m is None
            or final_liquid_volume_fraction is None
            or final_gas_volume_fraction is None
            or final_mixture_density_kg_m3 is None
            or final_gas_superficial_velocity_m_s is None
            or final_liquid_superficial_velocity_m_s is None
            or final_slip_ratio is None
            or final_diagnostic_regime is None
            or final_diagnostic_regime_source is None
            or final_diagnostic_regime_status is None
            or final_diagnostic_regime_transition_criteria is None
            or final_diagnostic_regime_confidence is None
            or final_pressure_profile_pa is None
            or final_temperature_profile_c is None
            or final_vapor_mass_flow_out_kg_s is None
            or final_outlet_state is None
        ):
            return None

        vapor_mass_flow_out_kg_s = final_vapor_mass_flow_out_kg_s
        total_mass_flow_kg_s = vapor_mass_flow_out_kg_s * (1.0 + circulation_factor)
        liquid_mass_flow_in_kg_s = total_mass_flow_kg_s
        liquid_mass_flow_out_kg_s = total_mass_flow_kg_s - vapor_mass_flow_out_kg_s
        liquid_mass_flux_in = liquid_mass_flow_in_kg_s / self.geometry.flow_area_m2

        liquid_reynolds_in = (liquid_mass_flow_in_kg_s * self.geometry.hydraulic_diameter_m) / (
            preboiling_state.mu_l_pa_s * self.geometry.flow_area_m2
        )
        inlet_liquid_pressure_drop_pa = (
            (self.friction_factor(liquid_reynolds_in, self.geometry.relative_roughness, inputs) * preboiling_path_length_m)
            * preboiling_state.v_l_m3_per_kg
            * (liquid_mass_flux_in**2)
        ) / (self.geometry.inner_radius_m * 4.0)
        inlet_liquid_pressure_gradient_pa_per_m = (
            inlet_liquid_pressure_drop_pa / preboiling_path_length_m if preboiling_path_length_m > 0.0 else 0.0
        )

        boiling_section_pressure_drop_pa = float(onset_pressure_pa - final_outlet_state.pressure_pa)

        gas_reynolds_out = (vapor_mass_flow_out_kg_s * self.geometry.hydraulic_diameter_m) / (
            final_outlet_state.mu_g_pa_s * self.geometry.flow_area_m2
        )
        liquid_reynolds_out = (liquid_mass_flow_out_kg_s * self.geometry.hydraulic_diameter_m) / (
            final_outlet_state.mu_l_pa_s * self.geometry.flow_area_m2
        )
        gas_mass_flux_out = vapor_mass_flow_out_kg_s / self.geometry.flow_area_m2
        liquid_mass_flux_out = liquid_mass_flow_out_kg_s / self.geometry.flow_area_m2
        outlet_gas_friction_factor = self.friction_factor(gas_reynolds_out, self.geometry.relative_roughness, inputs)
        outlet_liquid_friction_factor = self.friction_factor(liquid_reynolds_out, self.geometry.relative_roughness, inputs)
        martinelli_x_out = float(
            martinelli_parameter(
                liquid_mass_flow_kg_s=liquid_mass_flow_out_kg_s,
                vapor_mass_flow_kg_s=vapor_mass_flow_out_kg_s,
                liquid_friction_factor=outlet_liquid_friction_factor,
                gas_friction_factor=outlet_gas_friction_factor,
                liquid_specific_volume_m3_per_kg=final_outlet_state.v_l_m3_per_kg,
                vapor_specific_volume_m3_per_kg=final_outlet_state.v_g_m3_per_kg,
            )
        )
        chisholm_c_out = float(
            chisholm_constant(
                gas_reynolds=gas_reynolds_out,
                liquid_reynolds=liquid_reynolds_out,
            )
        )
        outlet_two_phase_multiplier = float(
            two_phase_multiplier_liquid_reference(
                martinelli_x=martinelli_x_out,
                chisholm_c=chisholm_c_out,
            )
        )
        outlet_closure_state = closure_state_from_model(
            model=inputs.closure_model,
            vapor_mass_flow_kg_s=vapor_mass_flow_out_kg_s,
            liquid_mass_flow_kg_s=liquid_mass_flow_out_kg_s,
            gas_mass_flux_kg_m2_s=gas_mass_flux_out,
            liquid_mass_flux_kg_m2_s=liquid_mass_flux_out,
            vapor_specific_volume_m3_per_kg=final_outlet_state.v_g_m3_per_kg,
            liquid_specific_volume_m3_per_kg=final_outlet_state.v_l_m3_per_kg,
            phi2l=outlet_two_phase_multiplier,
            orientation="horizontal",
            hydraulic_diameter_m=self.geometry.hydraulic_diameter_m,
            relative_roughness=self.geometry.relative_roughness,
            vapor_dynamic_viscosity_pa_s=final_outlet_state.mu_g_pa_s,
            liquid_dynamic_viscosity_pa_s=final_outlet_state.mu_l_pa_s,
            friction_model=self.effective_friction_model(inputs),
        )
        liquid_volume_fraction_out = outlet_closure_state.liquid_volume_fraction
        gas_volume_fraction_out = outlet_closure_state.gas_volume_fraction
        gas_velocity_out_m_s = outlet_closure_state.gas_velocity_m_s
        liquid_velocity_out_m_s = outlet_closure_state.liquid_velocity_m_s
        liquid_velocity_in_m_s = liquid_mass_flux_in * preboiling_state.v_l_m3_per_kg
        acceleration_pressure_drop_pa = (
            ((final_outlet_state.v_l_m3_per_kg ** -1) * (liquid_velocity_out_m_s**2) * liquid_volume_fraction_out)
            + ((final_outlet_state.v_g_m3_per_kg ** -1) * (gas_velocity_out_m_s**2) * gas_volume_fraction_out)
            - ((preboiling_state.v_l_m3_per_kg ** -1) * (liquid_velocity_in_m_s**2))
        )
        outlet_liquid_only_pressure_gradient = (
            outlet_liquid_friction_factor * final_outlet_state.v_l_m3_per_kg * (liquid_mass_flux_out**2)
        ) / (4.0 * self.geometry.inner_radius_m)
        outlet_effective_two_phase_multiplier = (
            outlet_closure_state.effective_two_phase_multiplier
            if outlet_closure_state.effective_two_phase_multiplier is not None
            else outlet_two_phase_multiplier
        )
        outlet_friction_pressure_gradient_pa_per_m = (
            outlet_closure_state.friction_pressure_gradient_pa_per_m
            if outlet_closure_state.friction_pressure_gradient_pa_per_m is not None
            else outlet_effective_two_phase_multiplier * outlet_liquid_only_pressure_gradient
        )
        outlet_section_pressure_drop_pa = (
            outlet_friction_pressure_gradient_pa_per_m
            * self.geometry.outlet_section_length_m
        )

        outlet_mixture_density_kg_m3 = outlet_closure_state.mixture_density_kg_m3
        reference_liquid_density_kg_m3 = reference_state.v_l_m3_per_kg ** -1
        n_riser = max(40, min(ngrid, 120))
        riser_edge_heights_top_m = np.linspace(0.0, inputs.H, n_riser + 1, dtype=float)
        riser_cell_heights_m = np.diff(riser_edge_heights_top_m)
        riser_center_heights_top_m = 0.5 * (riser_edge_heights_top_m[:-1] + riser_edge_heights_top_m[1:])
        riser_pressure_top_pa = reference_state.pressure_pa
        riser_local_pressure_pa = riser_pressure_top_pa

        riser_pressure_profile_top_pa = np.zeros(n_riser, dtype=float)
        riser_temperature_profile_top_c = np.zeros(n_riser, dtype=float)
        riser_gas_volume_fraction_top = np.zeros(n_riser, dtype=float)
        riser_liquid_volume_fraction_top = np.zeros(n_riser, dtype=float)
        riser_mixture_density_top = np.zeros(n_riser, dtype=float)
        riser_slip_ratio_top = np.zeros(n_riser, dtype=float)
        riser_gas_superficial_velocity_top_m_s = np.zeros(n_riser, dtype=float)
        riser_liquid_superficial_velocity_top_m_s = np.zeros(n_riser, dtype=float)
        riser_diagnostic_regime_top = np.full(n_riser, "", dtype=object)
        riser_diagnostic_regime_source_top = np.full(n_riser, "", dtype=object)
        riser_diagnostic_regime_status_top = np.full(n_riser, "", dtype=object)
        riser_diagnostic_regime_transition_top = np.full(n_riser, "", dtype=object)
        riser_diagnostic_regime_confidence_top = np.full(n_riser, "", dtype=object)
        riser_pressure_gradient_top_pa_per_m = np.zeros(n_riser, dtype=float)
        riser_friction_gradient_top_pa_per_m = np.zeros(n_riser, dtype=float)
        riser_hydrostatic_gradient_top_pa_per_m = np.zeros(n_riser, dtype=float)

        for idx, cell_height_m in enumerate(riser_cell_heights_m):
            riser_temperature_c = float(self.properties.temperature_from_pressure_pa(riser_local_pressure_pa))
            riser_state = self.properties.state_at_temperature(riser_temperature_c)
            riser_gas_reynolds = (vapor_mass_flow_out_kg_s * self.geometry.hydraulic_diameter_m) / (
                riser_state.mu_g_pa_s * self.geometry.flow_area_m2
            )
            riser_liquid_reynolds = (liquid_mass_flow_out_kg_s * self.geometry.hydraulic_diameter_m) / (
                riser_state.mu_l_pa_s * self.geometry.flow_area_m2
            )
            riser_gas_friction_factor = self.friction_factor(riser_gas_reynolds, self.geometry.relative_roughness, inputs)
            riser_liquid_friction_factor = self.friction_factor(riser_liquid_reynolds, self.geometry.relative_roughness, inputs)
            riser_martinelli_x = float(
                martinelli_parameter(
                    liquid_mass_flow_kg_s=liquid_mass_flow_out_kg_s,
                    vapor_mass_flow_kg_s=vapor_mass_flow_out_kg_s,
                    liquid_friction_factor=riser_liquid_friction_factor,
                    gas_friction_factor=riser_gas_friction_factor,
                    liquid_specific_volume_m3_per_kg=riser_state.v_l_m3_per_kg,
                    vapor_specific_volume_m3_per_kg=riser_state.v_g_m3_per_kg,
                )
            )
            riser_chisholm_c = float(
                chisholm_constant(
                    gas_reynolds=riser_gas_reynolds,
                    liquid_reynolds=riser_liquid_reynolds,
                )
            )
            riser_phi2l = float(
                two_phase_multiplier_liquid_reference(
                    martinelli_x=riser_martinelli_x,
                    chisholm_c=riser_chisholm_c,
                )
            )
            riser_closure_state = closure_state_from_model(
                model=inputs.closure_model,
                vapor_mass_flow_kg_s=vapor_mass_flow_out_kg_s,
                liquid_mass_flow_kg_s=liquid_mass_flow_out_kg_s,
                gas_mass_flux_kg_m2_s=gas_mass_flux_out,
                liquid_mass_flux_kg_m2_s=liquid_mass_flux_out,
                vapor_specific_volume_m3_per_kg=riser_state.v_g_m3_per_kg,
                liquid_specific_volume_m3_per_kg=riser_state.v_l_m3_per_kg,
                phi2l=riser_phi2l,
                orientation="vertical_up",
                hydraulic_diameter_m=self.geometry.hydraulic_diameter_m,
                relative_roughness=self.geometry.relative_roughness,
                vapor_dynamic_viscosity_pa_s=riser_state.mu_g_pa_s,
                liquid_dynamic_viscosity_pa_s=riser_state.mu_l_pa_s,
                friction_model=self.effective_friction_model(inputs),
            )
            riser_liquid_only_gradient_pa_per_m = (
                riser_liquid_friction_factor * riser_state.v_l_m3_per_kg * (liquid_mass_flux_out**2)
            ) / (4.0 * self.geometry.inner_radius_m)
            riser_effective_two_phase_multiplier = (
                riser_closure_state.effective_two_phase_multiplier
                if riser_closure_state.effective_two_phase_multiplier is not None
                else riser_phi2l
            )
            riser_friction_gradient_pa_per_m = (
                riser_closure_state.friction_pressure_gradient_pa_per_m
                if riser_closure_state.friction_pressure_gradient_pa_per_m is not None
                else riser_effective_two_phase_multiplier * riser_liquid_only_gradient_pa_per_m
            )
            riser_total_gradient_pa_per_m = riser_friction_gradient_pa_per_m + (
                riser_closure_state.mixture_density_kg_m3 * 9.81
            )

            riser_pressure_profile_top_pa[idx] = riser_local_pressure_pa
            riser_temperature_profile_top_c[idx] = riser_temperature_c
            riser_gas_volume_fraction_top[idx] = riser_closure_state.gas_volume_fraction
            riser_liquid_volume_fraction_top[idx] = riser_closure_state.liquid_volume_fraction
            riser_mixture_density_top[idx] = riser_closure_state.mixture_density_kg_m3
            riser_slip_ratio_top[idx] = riser_closure_state.slip_ratio
            riser_gas_superficial_velocity_top_m_s[idx] = gas_mass_flux_out * riser_state.v_g_m3_per_kg
            riser_liquid_superficial_velocity_top_m_s[idx] = liquid_mass_flux_out * riser_state.v_l_m3_per_kg
            riser_diagnostic_regime_top[idx] = riser_closure_state.diagnostic_regime
            riser_diagnostic_regime_source_top[idx] = riser_closure_state.diagnostic_regime_source
            riser_diagnostic_regime_status_top[idx] = riser_closure_state.diagnostic_regime_status
            riser_diagnostic_regime_transition_top[idx] = riser_closure_state.diagnostic_regime_transition_criteria
            riser_diagnostic_regime_confidence_top[idx] = riser_closure_state.diagnostic_regime_confidence
            riser_pressure_gradient_top_pa_per_m[idx] = riser_total_gradient_pa_per_m
            riser_friction_gradient_top_pa_per_m[idx] = riser_friction_gradient_pa_per_m
            riser_hydrostatic_gradient_top_pa_per_m[idx] = riser_closure_state.mixture_density_kg_m3 * 9.81

            riser_local_pressure_pa += riser_total_gradient_pa_per_m * cell_height_m

        riser_section_pressure_drop_pa = float(np.sum(riser_friction_gradient_top_pa_per_m * riser_cell_heights_m))
        riser_hydrostatic_pressure_drop_pa = float(
            np.sum(riser_hydrostatic_gradient_top_pa_per_m * riser_cell_heights_m)
        )
        density_difference_top = reference_liquid_density_kg_m3 - riser_mixture_density_top
        driving_pressure_pa = float(np.sum(9.81 * density_difference_top * riser_cell_heights_m))
        effective_density_difference_kg_m3 = (
            driving_pressure_pa / (9.81 * inputs.H) if inputs.H > 0.0 else reference_liquid_density_kg_m3 - outlet_mixture_density_kg_m3
        )
        total_pressure_drop_pa = (
            boiling_section_pressure_drop_pa
            + inlet_liquid_pressure_drop_pa
            + riser_section_pressure_drop_pa
            + outlet_section_pressure_drop_pa
            + acceleration_pressure_drop_pa
        )
        required_head_m = total_pressure_drop_pa / (
            9.81 * effective_density_difference_kg_m3
        )

        outlet_mass_quality = vapor_mass_flow_out_kg_s / total_mass_flow_kg_s
        liquid_mass_flow_out_lph = liquid_mass_flow_out_kg_s * final_outlet_state.v_l_m3_per_kg * 1000.0 * 3600.0
        liquid_mass_flow_in_lph = liquid_mass_flow_in_kg_s * preboiling_state.v_l_m3_per_kg * 1000.0 * 3600.0
        vapor_mass_flow_liq_equiv_lph = vapor_mass_flow_out_kg_s * final_outlet_state.v_l_m3_per_kg * 1000.0 * 3600.0
        vapor_mass_flow_gas_lph = vapor_mass_flow_out_kg_s * final_outlet_state.v_g_m3_per_kg * 1000.0 * 3600.0
        outlet_gas_volume_fraction_true = (vapor_mass_flow_out_kg_s * final_outlet_state.v_g_m3_per_kg) / (
            (vapor_mass_flow_out_kg_s * final_outlet_state.v_g_m3_per_kg)
            + (liquid_mass_flow_out_kg_s * final_outlet_state.v_l_m3_per_kg)
        )
        riser_height_bottom_to_top_m = inputs.H - riser_center_heights_top_m[::-1]
        riser_temperature_bottom_to_top_c = riser_temperature_profile_top_c[::-1]
        riser_pressure_bottom_to_top_pa = riser_pressure_profile_top_pa[::-1]
        riser_gas_volume_fraction_bottom_to_top = riser_gas_volume_fraction_top[::-1]
        riser_liquid_volume_fraction_bottom_to_top = riser_liquid_volume_fraction_top[::-1]
        riser_mixture_density_bottom_to_top = riser_mixture_density_top[::-1]
        riser_slip_ratio_bottom_to_top = riser_slip_ratio_top[::-1]
        riser_gas_superficial_velocity_bottom_to_top_m_s = riser_gas_superficial_velocity_top_m_s[::-1]
        riser_liquid_superficial_velocity_bottom_to_top_m_s = riser_liquid_superficial_velocity_top_m_s[::-1]
        riser_pressure_gradient_bottom_to_top_pa_per_m = riser_pressure_gradient_top_pa_per_m[::-1]
        riser_density_difference_bottom_to_top = density_difference_top[::-1]
        riser_cell_heights_bottom_to_top_m = riser_cell_heights_m[::-1]
        if self.effective_closure_model(inputs) == "experimental_regime_aware":
            riser_flow_regime_bottom_to_top = tuple(
                str(value) if str(value) else "two_phase_riser"
                for value in riser_diagnostic_regime_top[::-1]
            )
            riser_flow_regime_source_bottom_to_top = tuple(
                str(value) if str(value) else "experimental_regime_aware heuristic thresholds; no primary source"
                for value in riser_diagnostic_regime_source_top[::-1]
            )
            riser_flow_regime_status_bottom_to_top = tuple(
                str(value) if str(value) else "experimental"
                for value in riser_diagnostic_regime_status_top[::-1]
            )
            riser_flow_regime_transition_bottom_to_top = tuple(
                str(value) if str(value) else "legacy experimental fallback"
                for value in riser_diagnostic_regime_transition_top[::-1]
            )
            riser_flow_regime_confidence_bottom_to_top = tuple(
                str(value) if str(value) else "heuristic"
                for value in riser_diagnostic_regime_confidence_top[::-1]
            )
        else:
            riser_classifications = tuple(
                classify_vertical_riser_regime_result(
                    gas_volume_fraction=float(gas_volume_fraction),
                    gas_superficial_velocity_m_s=float(gas_superficial_velocity_m_s),
                )
                for gas_volume_fraction, gas_superficial_velocity_m_s in zip(
                    riser_gas_volume_fraction_bottom_to_top,
                    riser_gas_superficial_velocity_bottom_to_top_m_s,
                )
            )
            riser_flow_regime_bottom_to_top = tuple(classification.name for classification in riser_classifications)
            riser_flow_regime_source_bottom_to_top = tuple(classification.source for classification in riser_classifications)
            riser_flow_regime_status_bottom_to_top = tuple(classification.status for classification in riser_classifications)
            riser_flow_regime_transition_bottom_to_top = tuple(
                classification.transition_criteria for classification in riser_classifications
            )
            riser_flow_regime_confidence_bottom_to_top = tuple(
                classification.confidence for classification in riser_classifications
            )
        riser_regime_fractions = summarize_regime_fractions(
            regimes=list(riser_flow_regime_bottom_to_top),
            segment_lengths_m=riser_cell_heights_bottom_to_top_m.tolist(),
        )
        riser_dominant_flow_regime = dominant_regime(riser_regime_fractions)
        riser_flow_regime_summary = format_regime_summary(riser_regime_fractions)
        riser_cumulative_driving_pressure_pa = np.cumsum(
            9.81 * riser_density_difference_bottom_to_top * riser_cell_heights_bottom_to_top_m
        )
        riser_profile = RiserProfile(
            height_m=tuple(np.asarray(riser_height_bottom_to_top_m, dtype=float).tolist()),
            flow_regime=riser_flow_regime_bottom_to_top,
            local_temperature_c=tuple(np.asarray(riser_temperature_bottom_to_top_c, dtype=float).tolist()),
            local_pressure_pa=tuple(np.asarray(riser_pressure_bottom_to_top_pa, dtype=float).tolist()),
            gas_volume_fraction=tuple(np.asarray(riser_gas_volume_fraction_bottom_to_top, dtype=float).tolist()),
            liquid_volume_fraction=tuple(np.asarray(riser_liquid_volume_fraction_bottom_to_top, dtype=float).tolist()),
            mixture_density_kg_m3=tuple(np.asarray(riser_mixture_density_bottom_to_top, dtype=float).tolist()),
            gas_superficial_velocity_m_s=tuple(np.asarray(riser_gas_superficial_velocity_bottom_to_top_m_s, dtype=float).tolist()),
            liquid_superficial_velocity_m_s=tuple(np.asarray(riser_liquid_superficial_velocity_bottom_to_top_m_s, dtype=float).tolist()),
            slip_ratio=tuple(np.asarray(riser_slip_ratio_bottom_to_top, dtype=float).tolist()),
            pressure_gradient_pa_per_m=tuple(np.asarray(riser_pressure_gradient_bottom_to_top_pa_per_m, dtype=float).tolist()),
            cumulative_driving_pressure_pa=tuple(np.asarray(riser_cumulative_driving_pressure_pa, dtype=float).tolist()),
            flow_regime_source=riser_flow_regime_source_bottom_to_top,
            flow_regime_status=riser_flow_regime_status_bottom_to_top,
            flow_regime_transition_criteria=riser_flow_regime_transition_bottom_to_top,
            flow_regime_confidence=riser_flow_regime_confidence_bottom_to_top,
        )

        evaporator_coordinate = np.linspace(0.0, 1.0, ngrid)
        evaporator_axial_position_m = evaporator_coordinate * inputs.Li
        boiling_mask = evaporator_coordinate >= preboiling_length_fraction
        preboiling_mask = ~boiling_mask
        phase_regime = np.where(preboiling_mask, "single_liquid_heating", "boiling_two_phase")

        vapor_mass_flow_profile_full_kg_s = np.zeros(ngrid, dtype=float)
        liquid_mass_flow_profile_full_kg_s = np.full(ngrid, liquid_mass_flow_in_kg_s, dtype=float)
        gas_reynolds_full = np.full(ngrid, np.nan, dtype=float)
        liquid_reynolds_full = np.full(ngrid, liquid_reynolds_in, dtype=float)
        martinelli_x_full = np.full(ngrid, np.nan, dtype=float)
        two_phase_multiplier_full = np.ones(ngrid, dtype=float)
        pressure_gradient_full_pa_per_m = np.full(ngrid, inlet_liquid_pressure_gradient_pa_per_m, dtype=float)
        gas_volume_fraction_full = np.zeros(ngrid, dtype=float)
        liquid_volume_fraction_full = np.ones(ngrid, dtype=float)
        gas_superficial_velocity_full_m_s = np.zeros(ngrid, dtype=float)
        liquid_superficial_velocity_full_m_s = np.full(
            ngrid,
            liquid_mass_flux_in * preboiling_state.v_l_m3_per_kg,
            dtype=float,
        )
        slip_ratio_full = np.zeros(ngrid, dtype=float)
        local_temperature_profile_c = np.full(ngrid, inputs.tcon, dtype=float)
        local_pressure_profile_pa = np.full(ngrid, onset_pressure_pa, dtype=float)

        if np.any(preboiling_mask) and preboiling_evaporator_length_m > 0.0:
            preboiling_progress = evaporator_axial_position_m[preboiling_mask] / preboiling_evaporator_length_m
            local_temperature_profile_c[preboiling_mask] = (
                inlet_liquid_temperature_c + preboiling_progress * subcool_delta_t_c
            )
            local_pressure_profile_pa[preboiling_mask] = onset_pressure_pa + (
                inlet_liquid_pressure_gradient_pa_per_m
                * (preboiling_evaporator_length_m - evaporator_axial_position_m[preboiling_mask])
            )
            liquid_mu_pre = self.properties.liquid_dynamic_viscosity_pa_s(local_temperature_profile_c[preboiling_mask])
            liquid_reynolds_full[preboiling_mask] = (
                liquid_mass_flow_in_kg_s * self.geometry.hydraulic_diameter_m
            ) / (liquid_mu_pre * self.geometry.flow_area_m2)

        if np.any(boiling_mask):
            vapor_mass_flow_profile_full_kg_s[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_vapor_mass_flow_profile_kg_s,
                left=0.0,
                right=float(final_vapor_mass_flow_profile_kg_s[-1]),
            )
            liquid_mass_flow_profile_full_kg_s[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_liquid_mass_flow_profile_kg_s,
                left=float(liquid_mass_flow_in_kg_s),
                right=float(final_liquid_mass_flow_profile_kg_s[-1]),
            )
            gas_reynolds_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_gas_reynolds,
            )
            liquid_reynolds_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_liquid_reynolds,
            )
            martinelli_x_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_martinelli_x,
            )
            two_phase_multiplier_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_two_phase_multiplier,
            )
            gas_volume_fraction_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_gas_volume_fraction,
            )
            liquid_volume_fraction_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_liquid_volume_fraction,
            )
            gas_superficial_velocity_full_m_s[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_gas_superficial_velocity_m_s,
            )
            liquid_superficial_velocity_full_m_s[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_liquid_superficial_velocity_m_s,
            )
            slip_ratio_full[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_slip_ratio,
            )
            pressure_gradient_full_pa_per_m[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_two_phase_pressure_gradient_pa_per_m,
            )
            local_temperature_profile_c[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_temperature_profile_c,
            )
            local_pressure_profile_pa[boiling_mask] = np.interp(
                evaporator_coordinate[boiling_mask],
                cell_center_coordinate,
                final_pressure_profile_pa,
            )

        single_liquid_regime = single_liquid_heating_classification()
        flow_regime_full = np.full(ngrid, single_liquid_regime.name, dtype=object)
        (
            flow_regime_source_full,
            flow_regime_status_full,
            flow_regime_transition_criteria_full,
            flow_regime_confidence_full,
        ) = _regime_metadata_arrays(ngrid, single_liquid_regime)
        if np.any(boiling_mask):
            if self.effective_closure_model(inputs) == "experimental_regime_aware":
                boiling_regime_profile = [str(value) if str(value) else "boiling_two_phase" for value in final_diagnostic_regime.tolist()]
                boiling_regime_source_profile = [
                    str(value) if str(value) else "experimental_regime_aware heuristic thresholds; no primary source"
                    for value in final_diagnostic_regime_source.tolist()
                ]
                boiling_regime_status_profile = [
                    str(value) if str(value) else "experimental"
                    for value in final_diagnostic_regime_status.tolist()
                ]
                boiling_regime_transition_profile = [
                    str(value) if str(value) else "legacy experimental fallback"
                    for value in final_diagnostic_regime_transition_criteria.tolist()
                ]
                boiling_regime_confidence_profile = [
                    str(value) if str(value) else "heuristic"
                    for value in final_diagnostic_regime_confidence.tolist()
                ]
                boiling_indices = np.searchsorted(cell_center_coordinate, evaporator_coordinate[boiling_mask], side="left")
                boiling_indices = np.clip(boiling_indices, 0, len(boiling_regime_profile) - 1)
                flow_regime_full[boiling_mask] = np.asarray(
                    [boiling_regime_profile[int(index)] for index in boiling_indices],
                    dtype=object,
                )
                flow_regime_source_full[boiling_mask] = np.asarray(
                    [boiling_regime_source_profile[int(index)] for index in boiling_indices],
                    dtype=object,
                )
                flow_regime_status_full[boiling_mask] = np.asarray(
                    [boiling_regime_status_profile[int(index)] for index in boiling_indices],
                    dtype=object,
                )
                flow_regime_transition_criteria_full[boiling_mask] = np.asarray(
                    [boiling_regime_transition_profile[int(index)] for index in boiling_indices],
                    dtype=object,
                )
                flow_regime_confidence_full[boiling_mask] = np.asarray(
                    [boiling_regime_confidence_profile[int(index)] for index in boiling_indices],
                    dtype=object,
                )
            else:
                for point_index in np.where(boiling_mask)[0]:
                    regime_classification = classify_horizontal_evaporator_regime_result(
                        mass_quality=float(vapor_mass_flow_profile_full_kg_s[point_index] / max(total_mass_flow_kg_s, 1e-12)),
                        gas_volume_fraction=float(gas_volume_fraction_full[point_index]),
                        gas_superficial_velocity_m_s=float(gas_superficial_velocity_full_m_s[point_index]),
                        liquid_superficial_velocity_m_s=float(liquid_superficial_velocity_full_m_s[point_index]),
                        slip_ratio=float(slip_ratio_full[point_index]),
                    )
                    flow_regime_full[point_index] = regime_classification.name
                    _write_regime_metadata(
                        source_values=flow_regime_source_full,
                        status_values=flow_regime_status_full,
                        transition_values=flow_regime_transition_criteria_full,
                        confidence_values=flow_regime_confidence_full,
                        index=int(point_index),
                        classification=regime_classification,
                    )

        evaporator_segment_lengths_m = np.full(ngrid, inputs.Li / max(ngrid, 1), dtype=float)
        evaporator_regime_fractions = summarize_regime_fractions(
            regimes=[str(value) for value in flow_regime_full.tolist()],
            segment_lengths_m=evaporator_segment_lengths_m.tolist(),
        )
        evaporator_dominant_flow_regime = dominant_regime(evaporator_regime_fractions)
        evaporator_flow_regime_summary = format_regime_summary(evaporator_regime_fractions)

        evaporator_profile = EvaporatorProfile(
            coordinate_0_1=tuple(np.asarray(evaporator_coordinate, dtype=float).tolist()),
            axial_position_m=tuple(np.asarray(evaporator_axial_position_m, dtype=float).tolist()),
            phase_regime=tuple(str(value) for value in phase_regime.tolist()),
            flow_regime=tuple(str(value) for value in flow_regime_full.tolist()),
            local_temperature_c=tuple(np.asarray(local_temperature_profile_c, dtype=float).tolist()),
            local_pressure_pa=tuple(np.asarray(local_pressure_profile_pa, dtype=float).tolist()),
            vapor_mass_flow_kg_s=tuple(np.asarray(vapor_mass_flow_profile_full_kg_s, dtype=float).tolist()),
            liquid_mass_flow_kg_s=tuple(np.asarray(liquid_mass_flow_profile_full_kg_s, dtype=float).tolist()),
            gas_volume_fraction=tuple(np.asarray(gas_volume_fraction_full, dtype=float).tolist()),
            liquid_volume_fraction=tuple(np.asarray(liquid_volume_fraction_full, dtype=float).tolist()),
            gas_superficial_velocity_m_s=tuple(np.asarray(gas_superficial_velocity_full_m_s, dtype=float).tolist()),
            liquid_superficial_velocity_m_s=tuple(np.asarray(liquid_superficial_velocity_full_m_s, dtype=float).tolist()),
            slip_ratio=tuple(np.asarray(slip_ratio_full, dtype=float).tolist()),
            gas_reynolds=tuple(np.asarray(gas_reynolds_full, dtype=float).tolist()),
            liquid_reynolds=tuple(np.asarray(liquid_reynolds_full, dtype=float).tolist()),
            martinelli_x=tuple(np.asarray(martinelli_x_full, dtype=float).tolist()),
            two_phase_multiplier=tuple(np.asarray(two_phase_multiplier_full, dtype=float).tolist()),
            two_phase_pressure_gradient_pa_per_m=tuple(np.asarray(pressure_gradient_full_pa_per_m, dtype=float).tolist()),
            flow_regime_source=tuple(str(value) for value in flow_regime_source_full.tolist()),
            flow_regime_status=tuple(str(value) for value in flow_regime_status_full.tolist()),
            flow_regime_transition_criteria=tuple(str(value) for value in flow_regime_transition_criteria_full.tolist()),
            flow_regime_confidence=tuple(str(value) for value in flow_regime_confidence_full.tolist()),
        )

        riser_section = self.geometry.riser_section(height_m=inputs.H)
        downcomer_section = self.geometry.downcomer_section()
        preboiling_evaporator_section = self.geometry.evaporator_section(
            length_m=preboiling_evaporator_length_m,
            name="evaporator_preboiling",
        )
        boiling_evaporator_section = self.geometry.evaporator_section(
            length_m=boiling_length_m,
            name="evaporator_boiling",
        )
        condenser_section = self.geometry.condenser_section()
        downcomer_friction_pa = inlet_liquid_pressure_gradient_pa_per_m * downcomer_section.length_m
        preboiling_evaporator_friction_pa = (
            inlet_liquid_pressure_gradient_pa_per_m * preboiling_evaporator_section.length_m
        )
        downcomer_dz_m = downcomer_section.dz_m if downcomer_section.dz_m != 0.0 else -abs(riser_section.length_m)
        downcomer_hydrostatic_pa = hydrostatic_pressure_pa(reference_liquid_density_kg_m3, downcomer_dz_m)
        pressure_balance = self._build_pressure_balance(
            downcomer_section=downcomer_section,
            riser_section=riser_section,
            preboiling_evaporator_section=preboiling_evaporator_section,
            boiling_evaporator_section=boiling_evaporator_section,
            condenser_section=condenser_section,
            downcomer_friction_pa=downcomer_friction_pa,
            riser_friction_pa=riser_section_pressure_drop_pa,
            preboiling_evaporator_friction_pa=preboiling_evaporator_friction_pa,
            boiling_evaporator_friction_pa=boiling_section_pressure_drop_pa,
            condenser_friction_pa=outlet_section_pressure_drop_pa,
            acceleration_pressure_drop_pa=acceleration_pressure_drop_pa,
            downcomer_hydrostatic_pa=downcomer_hydrostatic_pa,
            riser_hydrostatic_pa=riser_hydrostatic_pressure_drop_pa,
            driving_pressure_pa=driving_pressure_pa,
        )
        section_states = (
            LoopSectionState(
                section_name=downcomer_section.name,
                section_kind=downcomer_section.section_kind,
                orientation=downcomer_section.orientation,
                length_m=downcomer_section.length_m,
                phase_regime="single_liquid",
                pressure_drop_pa=float(downcomer_friction_pa),
                inlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_in_kg_s),
                inlet_vapor_mass_flow_kg_s=0.0,
                outlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_in_kg_s),
                outlet_vapor_mass_flow_kg_s=0.0,
            ),
            LoopSectionState(
                section_name=riser_section.name,
                section_kind=riser_section.section_kind,
                orientation=riser_section.orientation,
                length_m=riser_section.length_m,
                phase_regime=riser_dominant_flow_regime or "two_phase_riser",
                pressure_drop_pa=float(riser_section_pressure_drop_pa),
                inlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_out_kg_s),
                inlet_vapor_mass_flow_kg_s=float(vapor_mass_flow_out_kg_s),
                outlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_out_kg_s),
                outlet_vapor_mass_flow_kg_s=float(vapor_mass_flow_out_kg_s),
            ),
            LoopSectionState(
                section_name=preboiling_evaporator_section.name,
                section_kind=preboiling_evaporator_section.section_kind,
                orientation=preboiling_evaporator_section.orientation,
                length_m=preboiling_evaporator_section.length_m,
                phase_regime="single_liquid_heating",
                pressure_drop_pa=float(preboiling_evaporator_friction_pa),
                inlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_in_kg_s),
                inlet_vapor_mass_flow_kg_s=0.0,
                outlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_in_kg_s),
                outlet_vapor_mass_flow_kg_s=0.0,
            ),
            LoopSectionState(
                section_name=boiling_evaporator_section.name,
                section_kind=boiling_evaporator_section.section_kind,
                orientation=boiling_evaporator_section.orientation,
                length_m=boiling_evaporator_section.length_m,
                phase_regime=evaporator_dominant_flow_regime or "boiling_two_phase",
                pressure_drop_pa=float(boiling_section_pressure_drop_pa),
                inlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_in_kg_s),
                inlet_vapor_mass_flow_kg_s=0.0,
                outlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_out_kg_s),
                outlet_vapor_mass_flow_kg_s=float(vapor_mass_flow_out_kg_s),
            ),
            LoopSectionState(
                section_name=condenser_section.name,
                section_kind=condenser_section.section_kind,
                orientation=condenser_section.orientation,
                length_m=condenser_section.length_m,
                phase_regime="condensing_two_phase",
                pressure_drop_pa=float(outlet_section_pressure_drop_pa),
                inlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_out_kg_s),
                inlet_vapor_mass_flow_kg_s=float(vapor_mass_flow_out_kg_s),
                outlet_liquid_mass_flow_kg_s=float(liquid_mass_flow_out_kg_s),
                outlet_vapor_mass_flow_kg_s=float(vapor_mass_flow_out_kg_s),
            ),
        )

        return SteadyPassResult(
            total_heat_w=float(total_heat_w),
            preboiling_length_fraction=float(preboiling_length_fraction),
            preboiling_evaporator_length_m=float(preboiling_evaporator_length_m),
            preboiling_path_length_m=float(preboiling_path_length_m),
            boiling_length_m=float(boiling_length_m),
            boiling_onset_position_m=float(preboiling_evaporator_length_m),
            vapor_mass_flow_out_kg_s=float(vapor_mass_flow_out_kg_s),
            liquid_mass_flow_out_kg_s=float(liquid_mass_flow_out_kg_s),
            liquid_mass_flow_in_kg_s=float(liquid_mass_flow_in_kg_s),
            outlet_gas_volume_fraction_closure=float(gas_volume_fraction_out),
            outlet_liquid_volume_fraction_closure=float(liquid_volume_fraction_out),
            gas_velocity_out_m_s=float(gas_velocity_out_m_s),
            liquid_velocity_out_m_s=float(liquid_velocity_out_m_s),
            liquid_velocity_in_m_s=float(liquid_velocity_in_m_s),
            total_pressure_drop_pa=float(total_pressure_drop_pa),
            boiling_section_pressure_drop_pa=float(boiling_section_pressure_drop_pa),
            inlet_liquid_pressure_drop_pa=float(inlet_liquid_pressure_drop_pa),
            outlet_section_pressure_drop_pa=float(outlet_section_pressure_drop_pa),
            acceleration_pressure_drop_pa=float(acceleration_pressure_drop_pa),
            outlet_mixture_density_kg_m3=float(outlet_mixture_density_kg_m3),
            required_head_m=float(required_head_m),
            outlet_mass_quality=float(outlet_mass_quality),
            liquid_mass_flow_out_lph=float(liquid_mass_flow_out_lph),
            liquid_mass_flow_in_lph=float(liquid_mass_flow_in_lph),
            vapor_mass_flow_liq_equiv_lph=float(vapor_mass_flow_liq_equiv_lph),
            vapor_mass_flow_gas_lph=float(vapor_mass_flow_gas_lph),
            outlet_gas_volume_fraction_true=float(outlet_gas_volume_fraction_true),
            outlet_slip_ratio=float(outlet_closure_state.slip_ratio),
            outlet_selected_void_fraction_model=outlet_closure_state.selected_void_fraction_model,
            outlet_selected_friction_model=outlet_closure_state.selected_friction_model,
            driving_pressure_pa=float(driving_pressure_pa),
            effective_density_difference_kg_m3=float(effective_density_difference_kg_m3),
            evaporator_dominant_flow_regime=evaporator_dominant_flow_regime,
            riser_dominant_flow_regime=riser_dominant_flow_regime,
            evaporator_flow_regime_summary=evaporator_flow_regime_summary,
            riser_flow_regime_summary=riser_flow_regime_summary,
            friction_model=self.effective_friction_model(inputs),
            pressure_balance=pressure_balance,
            model_mode="distributed_steady",
            geometry_source=self.geometry.geometry_source,
            section_states=section_states,
            evaporator_profile=evaporator_profile,
            riser_profile=riser_profile,
        )

    def head_residual(self, inputs: SteadyLoopInputs, circulation_factor: float) -> float:
        residual_ngrid = 80 if inputs.mode == "distributed_steady" else 250
        try:
            pass_result = self.one_pass(inputs=inputs, circulation_factor=circulation_factor, ngrid=residual_ngrid)
        except PropertyRangeError as exc:
            self._last_property_error = str(exc)
            return np.nan
        if pass_result is None or not np.isfinite(pass_result.required_head_m):
            return np.nan
        return pass_result.required_head_m - inputs.H

    def find_circulation_factor(
        self,
        inputs: SteadyLoopInputs,
        fmin: float = 1e-6,
        fmax: float = 200.0,
        nsamp: int = 220,
    ) -> RootSearchResult:
        self._last_property_error = None
        if inputs.mode == "distributed_steady":
            nsamp = min(nsamp, 80)
        circulation_factor_grid = np.logspace(np.log10(fmin), np.log10(fmax), nsamp)
        head_residuals = np.array(
            [self.head_residual(inputs=inputs, circulation_factor=f) for f in circulation_factor_grid],
            dtype=float,
        )
        finite_mask = np.isfinite(head_residuals)
        sign_change_indices = np.where(
            finite_mask[:-1] & finite_mask[1:] & (head_residuals[:-1] * head_residuals[1:] < 0.0)
        )[0]
        n_sign_changes = int(len(sign_change_indices))
        if n_sign_changes == 0:
            if self._last_property_error is not None and not np.any(finite_mask):
                return RootSearchResult(
                    circulation_factor=None,
                    root_bracket=None,
                    n_sign_changes=0,
                    solver_status="property_out_of_range",
                    failure_reason=self._last_property_error,
                )
            return RootSearchResult(
                circulation_factor=None,
                root_bracket=None,
                n_sign_changes=0,
                solver_status="no_root_bracket",
                failure_reason="Не найден отрезок со сменой знака для невязки Hy(f) - H.",
            )

        bracket_index = int(sign_change_indices[0])
        root_bracket = (
            float(circulation_factor_grid[bracket_index]),
            float(circulation_factor_grid[bracket_index + 1]),
        )
        try:
            sol = root_scalar(
                lambda f: self.head_residual(inputs=inputs, circulation_factor=f),
                bracket=list(root_bracket),
                method="brentq",
                xtol=1e-10,
                rtol=1e-10,
            )
        except PropertyRangeError as exc:
            return RootSearchResult(
                circulation_factor=None,
                root_bracket=root_bracket,
                n_sign_changes=n_sign_changes,
                solver_status="property_out_of_range",
                failure_reason=str(exc),
            )
        except ValueError as exc:
            if self._last_property_error is not None:
                return RootSearchResult(
                    circulation_factor=None,
                    root_bracket=root_bracket,
                    n_sign_changes=n_sign_changes,
                    solver_status="property_out_of_range",
                    failure_reason=self._last_property_error,
                )
            return RootSearchResult(
                circulation_factor=None,
                root_bracket=root_bracket,
                n_sign_changes=n_sign_changes,
                solver_status="root_solver_failed",
                failure_reason=str(exc),
            )

        if not sol.converged:
            return RootSearchResult(
                circulation_factor=None,
                root_bracket=root_bracket,
                n_sign_changes=n_sign_changes,
                solver_status="root_solver_not_converged",
                failure_reason="Решатель Brent не сошелся для параметра циркуляции.",
            )

        return RootSearchResult(
            circulation_factor=float(sol.root),
            root_bracket=root_bracket,
            n_sign_changes=n_sign_changes,
            solver_status="converged",
            failure_reason=None,
        )

    def solve_auxiliary_temperature(
        self,
        inputs: SteadyLoopInputs,
        circulation_factor: float,
    ) -> tuple[Optional[float], Optional[str]]:
        auxiliary_ngrid = 160 if inputs.mode == "distributed_steady" else 500
        try:
            pass_result = self.one_pass(inputs=inputs, circulation_factor=circulation_factor, ngrid=auxiliary_ngrid)
        except PropertyRangeError as exc:
            return None, str(exc)
        if pass_result is None:
            return None, "Не удалось вычислить внутренний проход для уравнения tmm."

        inlet_liquid_pressure_drop_pa = pass_result.inlet_liquid_pressure_drop_pa

        def temperature_residual(candidate_temperature_c: float) -> float:
            try:
                state = self.properties.state_at_temperature(0.5 * (candidate_temperature_c + inputs.tcon))
            except PropertyRangeError as exc:
                self._last_property_error = str(exc)
                return np.nan
            return (
                (inputs.tcon - candidate_temperature_c)
                - (inlet_liquid_pressure_drop_pa / state.dp_sat_dT_pa_per_k)
                + ((9.81 * inputs.H) / (state.v_l_m3_per_kg * state.dp_sat_dT_pa_per_k))
            )

        temperature_grid_c = np.linspace(inputs.tcon - 50.0, inputs.tcon + 10.0, 800)
        residual_values = np.array([temperature_residual(t) for t in temperature_grid_c], dtype=float)
        sign_change_indices = np.where(
            np.isfinite(residual_values[:-1])
            & np.isfinite(residual_values[1:])
            & (residual_values[:-1] * residual_values[1:] < 0.0)
        )[0]
        if len(sign_change_indices) == 0:
            return None, "Не найден отрезок со сменой знака для уравнения tmm."

        bracket_index = int(sign_change_indices[0])
        try:
            sol = root_scalar(
                temperature_residual,
                bracket=[temperature_grid_c[bracket_index], temperature_grid_c[bracket_index + 1]],
                method="brentq",
                xtol=1e-12,
                rtol=1e-12,
            )
        except (PropertyRangeError, ValueError) as exc:
            return None, str(exc)

        if not sol.converged:
            return None, "Решатель Brent не сошелся для вспомогательной температуры."
        return float(sol.root), None

    def solve(self, inputs: SteadyLoopInputs) -> SteadyLoopResult:
        geometry_source = self.geometry_source(inputs)
        if inputs.geometry is not None:
            try:
                inputs.geometry.validate_current_solver_sections()
            except ValueError as exc:
                return SteadyLoopResult(
                    converged=False,
                    H=inputs.H,
                    qtr=inputs.qtr,
                    Li=inputs.Li,
                    tcon=inputs.tcon,
                    solver_status="validation_error",
                    failure_reason=str(exc),
                    closure_name=self.closure_label(inputs),
                    property_model_name=self.property_model_name,
                    **self.property_result_fields(inputs),
                    model_scientific_status=self.model_scientific_status(inputs),
                    friction_model=self.effective_friction_model(inputs),
                    geometry_source=geometry_source,
                )
        if inputs.H < 0.0:
            return SteadyLoopResult(
                converged=False,
                H=inputs.H,
                qtr=inputs.qtr,
                Li=inputs.Li,
                tcon=inputs.tcon,
                solver_status="validation_error",
                failure_reason="H must be non-negative.",
                closure_name=self.closure_label(inputs),
                property_model_name=self.property_model_name,
                **self.property_result_fields(inputs),
                model_scientific_status=self.model_scientific_status(inputs),
                friction_model=self.effective_friction_model(inputs),
                geometry_source=geometry_source,
            )
        if inputs.H == 0.0:
            return SteadyLoopResult(
                converged=False,
                H=inputs.H,
                qtr=inputs.qtr,
                Li=inputs.Li,
                tcon=inputs.tcon,
                solver_status="no_driving_head",
                failure_reason="H=0 gives no hydrostatic driving head for natural circulation.",
                closure_name=self.closure_label(inputs),
                property_model_name=self.property_model_name,
                **self.property_result_fields(inputs),
                model_scientific_status=self.model_scientific_status(inputs),
                friction_model=self.effective_friction_model(inputs),
                geometry_source=geometry_source,
            )
        try:
            self.properties.state_at_temperature(inputs.tcon)
        except PropertyRangeError as exc:
            return SteadyLoopResult(
                converged=False,
                H=inputs.H,
                qtr=inputs.qtr,
                Li=inputs.Li,
                tcon=inputs.tcon,
                solver_status="property_out_of_range",
                failure_reason=str(exc),
                closure_name=self.closure_label(inputs),
                property_model_name=self.property_model_name,
                **self.property_result_fields(inputs),
                model_scientific_status=self.model_scientific_status(inputs),
                friction_model=self.effective_friction_model(inputs),
                geometry_source=geometry_source,
            )

        root_search = self.find_circulation_factor(inputs=inputs)
        if root_search.circulation_factor is None:
            return SteadyLoopResult(
                converged=False,
                H=inputs.H,
                qtr=inputs.qtr,
                Li=inputs.Li,
                tcon=inputs.tcon,
                root_bracket=root_search.root_bracket,
                n_sign_changes=root_search.n_sign_changes,
                solver_status=root_search.solver_status,
                failure_reason=root_search.failure_reason,
                closure_name=self.closure_label(inputs),
                property_model_name=self.property_model_name,
                **self.property_result_fields(inputs),
                model_scientific_status=self.model_scientific_status(inputs),
                friction_model=self.effective_friction_model(inputs),
                geometry_source=geometry_source,
            )

        final_ngrid = 400 if inputs.mode == "distributed_steady" else 1200
        try:
            pass_result = self.one_pass(inputs=inputs, circulation_factor=root_search.circulation_factor, ngrid=final_ngrid)
        except PropertyRangeError as exc:
            return SteadyLoopResult(
                converged=False,
                H=inputs.H,
                qtr=inputs.qtr,
                Li=inputs.Li,
                tcon=inputs.tcon,
                circulation_factor=root_search.circulation_factor,
                root_bracket=root_search.root_bracket,
                n_sign_changes=root_search.n_sign_changes,
                solver_status="property_out_of_range",
                failure_reason=str(exc),
                closure_name=self.closure_label(inputs),
                property_model_name=self.property_model_name,
                **self.property_result_fields(inputs),
                model_scientific_status=self.model_scientific_status(inputs),
                friction_model=self.effective_friction_model(inputs),
                geometry_source=geometry_source,
            )
        if pass_result is None:
            return SteadyLoopResult(
                converged=False,
                H=inputs.H,
                qtr=inputs.qtr,
                Li=inputs.Li,
                tcon=inputs.tcon,
                circulation_factor=root_search.circulation_factor,
                root_bracket=root_search.root_bracket,
                n_sign_changes=root_search.n_sign_changes,
                solver_status="internal_pass_failed",
                failure_reason="После поиска корня не удалось восстановить стационарный проход.",
                closure_name=self.closure_label(inputs),
                property_model_name=self.property_model_name,
                **self.property_result_fields(inputs),
                model_scientific_status=self.model_scientific_status(inputs),
                friction_model=self.effective_friction_model(inputs),
                geometry_source=geometry_source,
            )

        auxiliary_temperature_c, temperature_failure_reason = self.solve_auxiliary_temperature(
            inputs=inputs,
            circulation_factor=root_search.circulation_factor,
        )
        if auxiliary_temperature_c is None:
            return SteadyLoopResult(
                converged=False,
                H=inputs.H,
                qtr=inputs.qtr,
                Li=inputs.Li,
                tcon=inputs.tcon,
                circulation_factor=root_search.circulation_factor,
                pass_result=pass_result,
                root_bracket=root_search.root_bracket,
                n_sign_changes=root_search.n_sign_changes,
                solver_status="aux_temperature_failed",
                failure_reason=temperature_failure_reason,
                closure_name=self.closure_label(inputs),
                property_model_name=self.property_model_name,
                **self.property_result_fields(inputs),
                model_scientific_status=self.model_scientific_status(inputs),
                friction_model=self.effective_friction_model(inputs),
                geometry_source=geometry_source,
            )

        state = self.properties.state_at_temperature(inputs.tcon)
        outlet_mixture_temperature_c = inputs.tcon + (
            9.81 * ((inputs.H * pass_result.outlet_mixture_density_kg_m3) / state.dp_sat_dT_pa_per_k)
        )
        average_temperature_c = (
            0.5 * (inputs.tcon + auxiliary_temperature_c) * pass_result.preboiling_length_fraction
            + 0.5 * (outlet_mixture_temperature_c + auxiliary_temperature_c)
            * (1.0 - pass_result.preboiling_length_fraction)
        )
        total_heat_w = inputs.qtr * inputs.Li
        normalized_head_indicator = (
            (0.5 * (((9.81 * pass_result.required_head_m) * (state.v_l_m3_per_kg ** -1))))
        ) / (total_heat_w * state.dp_sat_dT_pa_per_k)
        normalized_temperature_indicator = (average_temperature_c - inputs.tcon) / total_heat_w
        geometric_head_indicator = (
            ((0.5 * 9.81) * inputs.H) / ((state.dp_sat_dT_pa_per_k * state.v_l_m3_per_kg) * total_heat_w)
        )

        return SteadyLoopResult(
            converged=True,
            H=inputs.H,
            qtr=inputs.qtr,
            Li=inputs.Li,
            tcon=inputs.tcon,
            circulation_factor=root_search.circulation_factor,
            auxiliary_temperature_c=float(auxiliary_temperature_c),
            average_temperature_c=float(average_temperature_c),
            outlet_mixture_temperature_c=float(outlet_mixture_temperature_c),
            normalized_head_indicator=float(normalized_head_indicator),
            normalized_temperature_indicator=float(normalized_temperature_indicator),
            geometric_head_indicator=float(geometric_head_indicator),
            pass_result=pass_result,
            root_bracket=root_search.root_bracket,
            n_sign_changes=root_search.n_sign_changes,
            solver_status="converged",
            failure_reason=None,
            closure_name=self.closure_label(inputs),
            property_model_name=self.property_model_name,
            **self.property_result_fields(inputs),
            model_scientific_status=self.model_scientific_status(inputs),
            friction_model=self.effective_friction_model(inputs),
            geometry_source=geometry_source,
        )
