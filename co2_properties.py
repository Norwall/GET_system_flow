from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.interpolate import CubicSpline


@dataclass(frozen=True)
class SaturationState:
    temperature_c: float
    pressure_pa: float
    dp_sat_dT_pa_per_k: float
    latent_heat_j_per_kg: float
    rho_l_kg_m3: float
    rho_g_kg_m3: float
    v_l_m3_per_kg: float
    v_g_m3_per_kg: float
    mu_l_pa_s: float
    mu_g_pa_s: float
    cp_l_j_per_kgk: float


class CO2SaturationProperties:
    def __init__(self) -> None:
        t = np.array([-20, -10, 0, 10, 20, 30], dtype=float)
        p = np.array([20.06, 26.99, 35.54, 45.95, 58.46, 73.34], dtype=float) * 1e4 * 9.81
        gamma_l = np.array([1029.9, 980.8, 924.8, 858.0, 770.7, 596.4], dtype=float)
        gamma_g = np.array([51.4, 70.50, 96.30, 133.0, 190.20, 334.40], dtype=float)
        r = np.array([67.79, 62.51, 56.13, 48.09, 37.10, 15.05], dtype=float) * 1e3 * 4.1868
        nu_g = np.array([0.0526, 0.0461, 0.0425, 0.0410, 0.0353, 0.0326], dtype=float) * (1e-2 / 3600)
        nu_l = np.array([0.146, 0.128, 0.118, 0.114, 0.098, 0.090], dtype=float) * 1e-6

        self._pressure_pa = CubicSpline(t, p)
        self._temperature_c_from_pressure_pa = CubicSpline(p, t)
        self._latent_heat_j_per_kg = CubicSpline(t, r)
        self._mu_g_pa_s = CubicSpline(t, nu_g * gamma_g)
        self._mu_l_pa_s = CubicSpline(t, nu_l * gamma_l)

        t_cp = np.array([-50, -40, -30, -20, -10, 0, 10, 20], dtype=float)
        cp_liquid = np.array([1.84, 1.88, 1.97, 2.05, 2.18, 2.47, 3.14, 5.00], dtype=float) * 1e3
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

        self._v_l_m3_per_kg = CubicSpline(t_dense, v_l)
        self._v_g_m3_per_kg = CubicSpline(t_dense, v_g)

    def pressure_pa(self, temperature_c: float | np.ndarray) -> Any:
        return self._pressure_pa(temperature_c)

    def latent_heat_j_per_kg(self, temperature_c: float | np.ndarray) -> Any:
        return self._latent_heat_j_per_kg(temperature_c)

    def temperature_from_pressure_pa(self, pressure_pa: float | np.ndarray) -> Any:
        return self._temperature_c_from_pressure_pa(pressure_pa)

    def dp_sat_dT_pa_per_k(self, temperature_c: float | np.ndarray) -> Any:
        return self._pressure_pa(temperature_c, 1)

    def liquid_specific_volume_m3_per_kg(self, temperature_c: float | np.ndarray) -> Any:
        return self._v_l_m3_per_kg(temperature_c)

    def vapor_specific_volume_m3_per_kg(self, temperature_c: float | np.ndarray) -> Any:
        return self._v_g_m3_per_kg(temperature_c)

    def liquid_dynamic_viscosity_pa_s(self, temperature_c: float | np.ndarray) -> Any:
        return self._mu_l_pa_s(temperature_c)

    def vapor_dynamic_viscosity_pa_s(self, temperature_c: float | np.ndarray) -> Any:
        return self._mu_g_pa_s(temperature_c)

    def liquid_heat_capacity_j_per_kgk(self, temperature_c: float | np.ndarray) -> Any:
        return self._cp_l_j_per_kgk(temperature_c)

    def state_at_temperature(self, temperature_c: float) -> SaturationState:
        v_l = float(self.liquid_specific_volume_m3_per_kg(temperature_c))
        v_g = float(self.vapor_specific_volume_m3_per_kg(temperature_c))
        return SaturationState(
            temperature_c=float(temperature_c),
            pressure_pa=float(self.pressure_pa(temperature_c)),
            dp_sat_dT_pa_per_k=float(self.dp_sat_dT_pa_per_k(temperature_c)),
            latent_heat_j_per_kg=float(self.latent_heat_j_per_kg(temperature_c)),
            rho_l_kg_m3=float(1.0 / v_l),
            rho_g_kg_m3=float(1.0 / v_g),
            v_l_m3_per_kg=v_l,
            v_g_m3_per_kg=v_g,
            mu_l_pa_s=float(self.liquid_dynamic_viscosity_pa_s(temperature_c)),
            mu_g_pa_s=float(self.vapor_dynamic_viscosity_pa_s(temperature_c)),
            cp_l_j_per_kgk=float(self.liquid_heat_capacity_j_per_kgk(temperature_c)),
        )
