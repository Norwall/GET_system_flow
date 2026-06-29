from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import numpy as np
from scipy.interpolate import CubicSpline


class PropertyRangeError(ValueError):
    """Raised when a saturation property call leaves the allowed range."""


class BackendUnavailableError(RuntimeError):
    """Raised when an optional property backend cannot be imported or initialized."""


def _fluid_token(value: str) -> str:
    return "".join(ch for ch in value.strip().lower() if ch.isalnum())


_FLUID_ALIASES = {
    "co2": "CO2",
    "r744": "CO2",
    "carbondioxide": "CO2",
    "carbondioxyde": "CO2",
    "nh3": "NH3",
    "r717": "NH3",
    "ammonia": "NH3",
}

_COOLPROP_FLUIDS = {
    "CO2": "CO2",
    "NH3": "Ammonia",
}

_FLUID_NAMES = {
    "CO2": "CarbonDioxide",
    "NH3": "Ammonia",
}

_FLUID_CAS = {
    "CO2": "124-38-9",
    "NH3": "7664-41-7",
}

_COOLPROP_SOURCES = {
    "CO2": "CoolProp HEOS CarbonDioxide; Span-Wagner equation of state",
    "NH3": "CoolProp HEOS Ammonia; Gao-Wu-Bell-Lemmon equation of state",
}


def normalize_fluid_name(fluid: str) -> str:
    """Return the canonical project fluid key for a user-facing alias."""

    token = _fluid_token(fluid)
    try:
        return _FLUID_ALIASES[token]
    except KeyError as exc:
        raise ValueError(f"Unsupported refrigerant fluid: {fluid!r}.") from exc


@dataclass(frozen=True)
class SaturationState:
    fluid: str
    temperature_c: float
    pressure_pa: float
    dp_sat_dT_pa_per_k: float
    h_l_j_kg: float
    h_g_j_kg: float
    latent_heat_j_kg: float
    rho_l_kg_m3: float
    rho_g_kg_m3: float
    v_l_m3_kg: float
    v_g_m3_kg: float
    mu_l_pa_s: float
    mu_g_pa_s: float
    cp_l_j_kgk: float
    cp_g_j_kgk: float
    k_l_w_mk: float
    k_g_w_mk: float
    surface_tension_n_m: float

    @property
    def latent_heat_j_per_kg(self) -> float:
        return self.latent_heat_j_kg

    @property
    def v_l_m3_per_kg(self) -> float:
        return self.v_l_m3_kg

    @property
    def v_g_m3_per_kg(self) -> float:
        return self.v_g_m3_kg

    @property
    def cp_l_j_per_kgk(self) -> float:
        return self.cp_l_j_kgk


@runtime_checkable
class RefrigerantSaturationProperties(Protocol):
    fluid: str
    fluid_cas: str
    refrigerant_name: str
    property_backend: str
    property_source: str
    property_warning: str
    near_critical_warning: str
    allow_property_extrapolation: bool

    def pressure_pa(self, temperature_c: float | np.ndarray) -> Any: ...

    def latent_heat_j_per_kg(self, temperature_c: float | np.ndarray) -> Any: ...

    def temperature_from_pressure_pa(self, pressure_pa: float | np.ndarray) -> Any: ...

    def dp_sat_dT_pa_per_k(self, temperature_c: float | np.ndarray) -> Any: ...

    def liquid_specific_volume_m3_per_kg(self, temperature_c: float | np.ndarray) -> Any: ...

    def vapor_specific_volume_m3_per_kg(self, temperature_c: float | np.ndarray) -> Any: ...

    def liquid_dynamic_viscosity_pa_s(self, temperature_c: float | np.ndarray) -> Any: ...

    def vapor_dynamic_viscosity_pa_s(self, temperature_c: float | np.ndarray) -> Any: ...

    def liquid_heat_capacity_j_per_kgk(self, temperature_c: float | np.ndarray) -> Any: ...

    def state_at_temperature(self, temperature_c: float) -> SaturationState: ...

    def property_warning_at_temperature(self, temperature_c: float) -> str: ...

    def near_critical_warning_at_temperature(self, temperature_c: float) -> str: ...


class MathcadCO2SaturationProperties:
    """CO2 saturation properties copied from the legacy Mathcad-compatible tables."""

    fluid = "CO2"
    fluid_cas = _FLUID_CAS["CO2"]
    refrigerant_name = _FLUID_NAMES["CO2"]
    property_backend = "mathcad_table"
    property_source = "CO2.xmcd saturation tables; documented as Vargaftik-based CO2 reference data"
    property_warning = (
        "Mathcad CO2 table backend has limited tabulated ranges and does not provide "
        "gas cp, thermal conductivity, or surface tension."
    )
    near_critical_warning = ""
    critical_temperature_c = 304.1282 - 273.15

    def __init__(self, allow_property_extrapolation: bool = False) -> None:
        self.allow_property_extrapolation = bool(allow_property_extrapolation)

        t = np.array([-20, -10, 0, 10, 20, 30], dtype=float)
        p = np.array([20.06, 26.99, 35.54, 45.95, 58.46, 73.34], dtype=float) * 1e4 * 9.81
        gamma_l = np.array([1029.9, 980.8, 924.8, 858.0, 770.7, 596.4], dtype=float)
        gamma_g = np.array([51.4, 70.50, 96.30, 133.0, 190.20, 334.40], dtype=float)
        r = np.array([67.79, 62.51, 56.13, 48.09, 37.10, 15.05], dtype=float) * 1e3 * 4.1868
        nu_g = np.array([0.0526, 0.0461, 0.0425, 0.0410, 0.0353, 0.0326], dtype=float) * (1e-2 / 3600)
        nu_l = np.array([0.146, 0.128, 0.118, 0.114, 0.098, 0.090], dtype=float) * 1e-6

        self._temperature_range_c = (float(t.min()), float(t.max()))
        self._pressure_pa = CubicSpline(t, p)
        self._temperature_c_from_pressure_pa = CubicSpline(p, t)
        self._pressure_range_pa = (float(p.min()), float(p.max()))
        self._latent_heat_j_per_kg = CubicSpline(t, r)
        self._mu_g_pa_s = CubicSpline(t, nu_g * gamma_g)
        self._mu_l_pa_s = CubicSpline(t, nu_l * gamma_l)

        t_cp = np.array([-50, -40, -30, -20, -10, 0, 10, 20], dtype=float)
        cp_liquid = np.array([1.84, 1.88, 1.97, 2.05, 2.18, 2.47, 3.14, 5.00], dtype=float) * 1e3
        self._cp_range_c = (float(t_cp.min()), float(t_cp.max()))
        self._cp_l_j_per_kgk = CubicSpline(t_cp, cp_liquid)

        t_dense = np.array(
            [
                216.55,
                220,
                225,
                230,
                235,
                240,
                245,
                250,
                255,
                260,
                265,
                270,
                273.15,
                274,
                275,
                276,
                277,
                278,
                279,
                280,
                281,
                282,
                283,
                284,
                285,
                286,
                287,
                288,
                289,
                290,
                291,
                292,
                293,
                294,
                295,
                296,
                297,
                298,
                299,
                300,
                301,
                302,
                303,
                304.19,
            ],
            dtype=float,
        ) - 273.15
        v_l = np.array(
            [
                0.848,
                0.857,
                0.871,
                0.885,
                0.901,
                0.918,
                0.936,
                0.956,
                0.978,
                1.002,
                1.029,
                1.059,
                1.078,
                1.084,
                1.092,
                1.099,
                1.107,
                1.115,
                1.123,
                1.132,
                1.141,
                1.150,
                1.160,
                1.170,
                1.181,
                1.193,
                1.204,
                1.217,
                1.229,
                1.243,
                1.258,
                1.273,
                1.290,
                1.309,
                1.329,
                1.350,
                1.374,
                1.401,
                1.433,
                1.479,
                1.515,
                1.573,
                1.656,
                2.136,
            ],
            dtype=float,
        ) * 1e-3
        v_g = np.array(
            [
                72.464,
                63.291,
                50.943,
                48.103,
                36.232,
                30.581,
                25.773,
                21.787,
                18.450,
                15.723,
                13.387,
                11.287,
                10.31,
                10.04,
                9.728,
                9.416,
                9.116,
                8.818,
                8.525,
                8.244,
                7.968,
                7.704,
                7.452,
                7.210,
                6.974,
                6.738,
                6.502,
                6.262,
                6.035,
                5.817,
                5.605,
                5.397,
                5.187,
                4.980,
                4.778,
                4.574,
                4.372,
                4.168,
                3.964,
                3.733,
                3.504,
                3.259,
                2.978,
                2.136,
            ],
            dtype=float,
        ) * 1e-3

        self._specific_volume_range_c = (float(t_dense.min()), float(t_dense.max()))
        self._v_l_m3_per_kg = CubicSpline(t_dense, v_l)
        self._v_g_m3_per_kg = CubicSpline(t_dense, v_g)

    def pressure_pa(self, temperature_c: float | np.ndarray) -> Any:
        self._check_temperature(temperature_c, self._temperature_range_c, "Mathcad CO2 pressure table")
        return self._pressure_pa(temperature_c)

    def latent_heat_j_per_kg(self, temperature_c: float | np.ndarray) -> Any:
        self._check_temperature(temperature_c, self._temperature_range_c, "Mathcad CO2 latent heat table")
        return self._latent_heat_j_per_kg(temperature_c)

    def temperature_from_pressure_pa(self, pressure_pa: float | np.ndarray) -> Any:
        self._check_value(pressure_pa, self._pressure_range_pa, "Mathcad CO2 saturation pressure table", "Pa")
        return self._temperature_c_from_pressure_pa(pressure_pa)

    def dp_sat_dT_pa_per_k(self, temperature_c: float | np.ndarray) -> Any:
        self._check_temperature(temperature_c, self._temperature_range_c, "Mathcad CO2 pressure derivative table")
        return self._pressure_pa(temperature_c, 1)

    def liquid_specific_volume_m3_per_kg(self, temperature_c: float | np.ndarray) -> Any:
        self._check_temperature(temperature_c, self._specific_volume_range_c, "Mathcad CO2 liquid volume table")
        return self._v_l_m3_per_kg(temperature_c)

    def vapor_specific_volume_m3_per_kg(self, temperature_c: float | np.ndarray) -> Any:
        self._check_temperature(temperature_c, self._specific_volume_range_c, "Mathcad CO2 vapor volume table")
        return self._v_g_m3_per_kg(temperature_c)

    def liquid_dynamic_viscosity_pa_s(self, temperature_c: float | np.ndarray) -> Any:
        self._check_temperature(temperature_c, self._temperature_range_c, "Mathcad CO2 liquid viscosity table")
        return self._mu_l_pa_s(temperature_c)

    def vapor_dynamic_viscosity_pa_s(self, temperature_c: float | np.ndarray) -> Any:
        self._check_temperature(temperature_c, self._temperature_range_c, "Mathcad CO2 vapor viscosity table")
        return self._mu_g_pa_s(temperature_c)

    def liquid_heat_capacity_j_per_kgk(self, temperature_c: float | np.ndarray) -> Any:
        self._check_temperature(temperature_c, self._cp_range_c, "Mathcad CO2 liquid heat capacity table")
        return self._cp_l_j_per_kgk(temperature_c)

    def state_at_temperature(self, temperature_c: float) -> SaturationState:
        v_l = float(self.liquid_specific_volume_m3_per_kg(temperature_c))
        v_g = float(self.vapor_specific_volume_m3_per_kg(temperature_c))
        latent_heat = float(self.latent_heat_j_per_kg(temperature_c))
        return SaturationState(
            fluid=self.fluid,
            temperature_c=float(temperature_c),
            pressure_pa=float(self.pressure_pa(temperature_c)),
            dp_sat_dT_pa_per_k=float(self.dp_sat_dT_pa_per_k(temperature_c)),
            h_l_j_kg=0.0,
            h_g_j_kg=latent_heat,
            latent_heat_j_kg=latent_heat,
            rho_l_kg_m3=float(1.0 / v_l),
            rho_g_kg_m3=float(1.0 / v_g),
            v_l_m3_kg=v_l,
            v_g_m3_kg=v_g,
            mu_l_pa_s=float(self.liquid_dynamic_viscosity_pa_s(temperature_c)),
            mu_g_pa_s=float(self.vapor_dynamic_viscosity_pa_s(temperature_c)),
            cp_l_j_kgk=float(self.liquid_heat_capacity_j_per_kgk(temperature_c)),
            cp_g_j_kgk=float("nan"),
            k_l_w_mk=float("nan"),
            k_g_w_mk=float("nan"),
            surface_tension_n_m=float("nan"),
        )

    def property_warning_at_temperature(self, temperature_c: float) -> str:
        _ = temperature_c
        if self.allow_property_extrapolation:
            return f"{self.property_warning} Extrapolation is explicitly enabled."
        return self.property_warning

    def near_critical_warning_at_temperature(self, temperature_c: float) -> str:
        delta_k = self.critical_temperature_c - float(temperature_c)
        if 0.0 <= delta_k <= 2.0:
            return f"Temperature is {delta_k:.3g} K below the CO2 critical temperature."
        return ""

    def _check_temperature(self, temperature_c: float | np.ndarray, allowed_range_c: tuple[float, float], table_name: str) -> None:
        self._check_value(temperature_c, allowed_range_c, table_name, "deg C")

    def _check_value(self, value: float | np.ndarray, allowed_range: tuple[float, float], source: str, unit: str) -> None:
        if self.allow_property_extrapolation:
            return
        values = np.asarray(value, dtype=float)
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            return
        lo, hi = allowed_range
        if np.any((finite < lo) | (finite > hi)):
            actual_min = float(np.min(finite))
            actual_max = float(np.max(finite))
            raise PropertyRangeError(
                f"{source} request [{actual_min:g}, {actual_max:g}] {unit} is outside "
                f"allowed range [{lo:g}, {hi:g}] {unit}. Set allow_property_extrapolation=True "
                "only for explicit compatibility studies."
            )


class CoolPropSaturationProperties:
    def __init__(self, fluid: str, allow_property_extrapolation: bool = False) -> None:
        self.fluid = normalize_fluid_name(fluid)
        self.fluid_cas = _FLUID_CAS[self.fluid]
        self.refrigerant_name = _FLUID_NAMES[self.fluid]
        self.property_backend = "coolprop"
        self.property_source = _COOLPROP_SOURCES[self.fluid]
        self.property_warning = ""
        self.near_critical_warning = ""
        self.allow_property_extrapolation = bool(allow_property_extrapolation)
        self._coolprop_fluid = _COOLPROP_FLUIDS[self.fluid]
        try:
            from CoolProp.CoolProp import PropsSI
        except ImportError as exc:
            raise BackendUnavailableError(
                "CoolProp is required for CoolPropSaturationProperties. Install project dependencies."
            ) from exc
        self._props_si = PropsSI
        self._triple_temperature_c = float(self._props_si("Ttriple", self._coolprop_fluid) - 273.15)
        self._critical_temperature_c = float(self._props_si("Tcrit", self._coolprop_fluid) - 273.15)
        self._triple_pressure_pa = float(self._props_si("ptriple", self._coolprop_fluid))
        self._critical_pressure_pa = float(self._props_si("pcrit", self._coolprop_fluid))
        self.triple_temperature_c = self._triple_temperature_c
        self.critical_temperature_c = self._critical_temperature_c
        self.triple_pressure_pa = self._triple_pressure_pa
        self.critical_pressure_pa = self._critical_pressure_pa

    def pressure_pa(self, temperature_c: float | np.ndarray) -> Any:
        return self._props_temperature_quality("P", temperature_c, 0.0)

    def latent_heat_j_per_kg(self, temperature_c: float | np.ndarray) -> Any:
        return self._props_temperature_quality("H", temperature_c, 1.0) - self._props_temperature_quality("H", temperature_c, 0.0)

    def temperature_from_pressure_pa(self, pressure_pa: float | np.ndarray) -> Any:
        values, scalar = self._as_array(pressure_pa)
        result = np.array([self._temperature_from_pressure_scalar(float(p)) for p in values], dtype=float)
        for t_c in result:
            self._check_temperature(float(t_c))
        return float(result[0]) if scalar else result.reshape(np.asarray(pressure_pa, dtype=float).shape)

    def dp_sat_dT_pa_per_k(self, temperature_c: float | np.ndarray) -> Any:
        values, scalar = self._as_array(temperature_c)
        result = np.array([self._dp_sat_dT_scalar(float(t_c)) for t_c in values], dtype=float)
        return float(result[0]) if scalar else result.reshape(np.asarray(temperature_c, dtype=float).shape)

    def liquid_specific_volume_m3_per_kg(self, temperature_c: float | np.ndarray) -> Any:
        return 1.0 / self._props_temperature_quality("D", temperature_c, 0.0)

    def vapor_specific_volume_m3_per_kg(self, temperature_c: float | np.ndarray) -> Any:
        return 1.0 / self._props_temperature_quality("D", temperature_c, 1.0)

    def liquid_dynamic_viscosity_pa_s(self, temperature_c: float | np.ndarray) -> Any:
        return self._props_temperature_quality("V", temperature_c, 0.0)

    def vapor_dynamic_viscosity_pa_s(self, temperature_c: float | np.ndarray) -> Any:
        return self._props_temperature_quality("V", temperature_c, 1.0)

    def liquid_heat_capacity_j_per_kgk(self, temperature_c: float | np.ndarray) -> Any:
        return self._props_temperature_quality("C", temperature_c, 0.0)

    def vapor_heat_capacity_j_per_kgk(self, temperature_c: float | np.ndarray) -> Any:
        return self._props_temperature_quality("C", temperature_c, 1.0)

    def liquid_thermal_conductivity_w_mk(self, temperature_c: float | np.ndarray) -> Any:
        return self._props_temperature_quality("L", temperature_c, 0.0)

    def vapor_thermal_conductivity_w_mk(self, temperature_c: float | np.ndarray) -> Any:
        return self._props_temperature_quality("L", temperature_c, 1.0)

    def surface_tension_n_m(self, temperature_c: float | np.ndarray) -> Any:
        return self._props_temperature_quality("I", temperature_c, 0.0)

    def state_at_temperature(self, temperature_c: float) -> SaturationState:
        t_c = float(temperature_c)
        h_l = float(self._props_temperature_quality("H", t_c, 0.0))
        h_g = float(self._props_temperature_quality("H", t_c, 1.0))
        rho_l = float(self._props_temperature_quality("D", t_c, 0.0))
        rho_g = float(self._props_temperature_quality("D", t_c, 1.0))
        return SaturationState(
            fluid=self.fluid,
            temperature_c=t_c,
            pressure_pa=float(self.pressure_pa(t_c)),
            dp_sat_dT_pa_per_k=float(self.dp_sat_dT_pa_per_k(t_c)),
            h_l_j_kg=h_l,
            h_g_j_kg=h_g,
            latent_heat_j_kg=h_g - h_l,
            rho_l_kg_m3=rho_l,
            rho_g_kg_m3=rho_g,
            v_l_m3_kg=1.0 / rho_l,
            v_g_m3_kg=1.0 / rho_g,
            mu_l_pa_s=float(self.liquid_dynamic_viscosity_pa_s(t_c)),
            mu_g_pa_s=float(self.vapor_dynamic_viscosity_pa_s(t_c)),
            cp_l_j_kgk=float(self.liquid_heat_capacity_j_per_kgk(t_c)),
            cp_g_j_kgk=float(self.vapor_heat_capacity_j_per_kgk(t_c)),
            k_l_w_mk=float(self.liquid_thermal_conductivity_w_mk(t_c)),
            k_g_w_mk=float(self.vapor_thermal_conductivity_w_mk(t_c)),
            surface_tension_n_m=float(self.surface_tension_n_m(t_c)),
        )

    def property_warning_at_temperature(self, temperature_c: float) -> str:
        _ = temperature_c
        if self.allow_property_extrapolation:
            return "CoolProp saturation range extrapolation is explicitly enabled."
        return self.property_warning

    def near_critical_warning_at_temperature(self, temperature_c: float) -> str:
        delta_k = self._critical_temperature_c - float(temperature_c)
        if 0.0 <= delta_k <= 2.0:
            return f"Temperature is {delta_k:.3g} K below the {self.fluid} critical temperature."
        return ""

    def _props_temperature_quality(self, output: str, temperature_c: float | np.ndarray, quality: float) -> Any:
        values, scalar = self._as_array(temperature_c)
        result = np.array(
            [
                self._props_si(output, "T", self._checked_temperature_k(float(t_c)), "Q", quality, self._coolprop_fluid)
                for t_c in values
            ],
            dtype=float,
        )
        return float(result[0]) if scalar else result.reshape(np.asarray(temperature_c, dtype=float).shape)

    def _dp_sat_dT_scalar(self, temperature_c: float) -> float:
        temperature_k = self._checked_temperature_k(temperature_c)
        try:
            return float(self._props_si("d(P)/d(T)|sigma", "T", temperature_k, "Q", 0.0, self._coolprop_fluid))
        except ValueError:
            dt = 1.0e-3
            lower_c = max(temperature_c - dt, self._triple_temperature_c + 1.0e-6)
            upper_c = min(temperature_c + dt, self._critical_temperature_c - 1.0e-6)
            if upper_c <= lower_c:
                raise
            p_low = float(self.pressure_pa(lower_c))
            p_high = float(self.pressure_pa(upper_c))
            return (p_high - p_low) / (upper_c - lower_c)

    def _temperature_from_pressure_scalar(self, pressure_pa: float) -> float:
        if not self.allow_property_extrapolation:
            if pressure_pa < self._triple_pressure_pa or pressure_pa >= self._critical_pressure_pa:
                raise PropertyRangeError(
                    f"{self.fluid} CoolProp saturation pressure {pressure_pa:g} Pa is outside "
                    f"allowed range [{self._triple_pressure_pa:g}, {self._critical_pressure_pa:g}) Pa."
                )
        try:
            return float(self._props_si("T", "P", pressure_pa, "Q", 0.0, self._coolprop_fluid) - 273.15)
        except ValueError as exc:
            raise PropertyRangeError(
                f"{self.fluid} CoolProp saturation pressure {pressure_pa:g} Pa is outside the saturation range."
            ) from exc

    def _checked_temperature_k(self, temperature_c: float) -> float:
        self._check_temperature(temperature_c)
        return float(temperature_c) + 273.15

    def _check_temperature(self, temperature_c: float) -> None:
        if self.allow_property_extrapolation:
            return
        t_c = float(temperature_c)
        if t_c < self._triple_temperature_c or t_c >= self._critical_temperature_c:
            raise PropertyRangeError(
                f"{self.fluid} CoolProp saturation temperature {t_c:g} deg C is outside "
                f"allowed range [{self._triple_temperature_c:g}, {self._critical_temperature_c:g}) deg C."
            )

    @staticmethod
    def _as_array(value: float | np.ndarray) -> tuple[np.ndarray, bool]:
        array = np.asarray(value, dtype=float)
        scalar = array.ndim == 0
        return np.atleast_1d(array).ravel(), scalar


class RefpropSaturationProperties(CoolPropSaturationProperties):
    def __init__(self, fluid: str, allow_property_extrapolation: bool = False) -> None:
        super().__init__(fluid=fluid, allow_property_extrapolation=allow_property_extrapolation)
        self.property_backend = "refprop"
        self.property_source = f"NIST REFPROP via CoolProp REFPROP backend for {self.fluid}"
        self._coolprop_fluid = f"REFPROP::{_COOLPROP_FLUIDS[self.fluid]}"
        try:
            _ = self._props_si("Tcrit", self._coolprop_fluid)
        except Exception as exc:
            raise BackendUnavailableError(
                "REFPROP backend is not available through CoolProp in this environment."
            ) from exc
        self._triple_temperature_c = float(self._props_si("Ttriple", self._coolprop_fluid) - 273.15)
        self._critical_temperature_c = float(self._props_si("Tcrit", self._coolprop_fluid) - 273.15)
        self._triple_pressure_pa = float(self._props_si("ptriple", self._coolprop_fluid))
        self._critical_pressure_pa = float(self._props_si("pcrit", self._coolprop_fluid))
        self.triple_temperature_c = self._triple_temperature_c
        self.critical_temperature_c = self._critical_temperature_c
        self.triple_pressure_pa = self._triple_pressure_pa
        self.critical_pressure_pa = self._critical_pressure_pa


def create_saturation_properties(
    fluid: str = "CO2",
    property_backend: str = "mathcad_table",
    allow_property_extrapolation: bool = False,
) -> RefrigerantSaturationProperties:
    canonical_fluid = normalize_fluid_name(fluid)
    backend = property_backend.strip().lower()
    if backend in {"mathcad", "mathcad_table", "worksheet_compatible"}:
        if canonical_fluid != "CO2":
            raise ValueError("Mathcad table backend is only available for CO2.")
        return MathcadCO2SaturationProperties(allow_property_extrapolation=allow_property_extrapolation)
    if backend in {"coolprop", "heos"}:
        return CoolPropSaturationProperties(fluid=canonical_fluid, allow_property_extrapolation=allow_property_extrapolation)
    if backend in {"refprop", "nist_refprop"}:
        return RefpropSaturationProperties(fluid=canonical_fluid, allow_property_extrapolation=allow_property_extrapolation)
    raise ValueError(f"Unsupported property backend: {property_backend!r}.")
