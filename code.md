from __future__ import annotations

"""Стационарная модель естественной циркуляции CO2, перенесенная из Mathcad.

Код ищет самосогласованный рабочий режим двухфазного контура:
- в испарителе подводится тепло и образуется пар;
- парожидкостная смесь становится легче жидкого столба;
- из-за разности плотностей возникает циркуляционный напор;
- этот напор расходуется на трение и ускорительные потери.

Главная неизвестная величина здесь — параметр циркуляции ``f``. Решатель ищет
такое значение ``f``, при котором требуемый напор ``Hy`` совпадает с заданным
геометрическим напором ``H``.
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import root_scalar
from scipy.special import erf


@dataclass(frozen=True)
class Scenario:
    """Контейнер для одного расчетного режима.

    Параметры
    ---------
    H:
        Доступный геометрический циркуляционный напор, м.
    qtr:
        Линейная тепловая нагрузка на испаритель, Вт/м.
    Li:
        Длина испарителя, м.
    tcon:
        Температура конденсации, град C.
    """

    name: str
    H: float
    qtr: float
    Li: float
    tcon: float


class CO2MathcadModel:
    """
    Python-порт внутреннего Mathcad-расчета CO2 для системы GET.

    Что реализовано:
    - стационарная одномерная модель внутреннего контура для горизонтального
      испарителя;
    - интерполяция термофизических свойств так, как это сделано в рабочем листе;
    - решение нелинейного баланса рабочего режима по параметру циркуляции ``f``.

    Важное ограничение:
    нижние и верхние критические тепловые нагрузки в диссертации получаются
    внешним алгоритмом сканирования, а для верхнего критического режима также
    через специальный предел ``f = 0``. Этот файл в основном реализует решатель
    стационарного рабочего режима, поэтому точное воспроизведение всех строк
    критических таблиц из приложений этим портом не гарантируется. В актуальном
    проекте отдельный слой такого расчёта вынесен в ``critical_loads.py``; этот
    файл остаётся историческим standalone-портом.
    """

    def __init__(self) -> None:
        # Базовая геометрия, перенесенная из рабочего листа.
        # inner_radius_m — внутренний радиус трубы, поэтому площадь прохода
        # равна pi * r^2, а гидравлический диаметр, используемый ниже, равен 2r.
        self.inner_radius_m = 1.325e-2
        self.reference_diameter_1_m = 36.5e-3
        self.reference_diameter_2_m = 67e-3
        self.outlet_section_length_m = 6.5
        self.inlet_section_length_m = 10.5
        # Относительная шероховатость eps / D для корреляции коэффициента трения.
        self.relative_roughness = (1e-4) / (2 * self.inner_radius_m)
        # Старые имена оставлены как алиасы, чтобы не ломать совместимость с
        # существующими сценариями, проверками и внешними вызовами.
        self.aa = self.inner_radius_m
        self.d1 = self.reference_diameter_1_m
        self.d2 = self.reference_diameter_2_m
        self.Lot = self.outlet_section_length_m
        self.Lpod = self.inlet_section_length_m
        self.Delta = self.relative_roughness

        # Таблица свойств на линии насыщения, используемая исходным рабочим листом в
        # основном рабочем диапазоне.
        t = np.array([-20, -10, 0, 10, 20, 30], dtype=float)
        p = np.array([20.06, 26.99, 35.54, 45.95, 58.46, 73.34], dtype=float) * 1e4 * 9.81
        gamma_l = np.array([1029.9, 980.8, 924.8, 858.0, 770.7, 596.4], dtype=float)
        gamma_g = np.array([51.4, 70.50, 96.30, 133.0, 190.20, 334.40], dtype=float)
        r = np.array([67.79, 62.51, 56.13, 48.09, 37.10, 15.05], dtype=float) * 1e3 * 4.1868
        nu_g = np.array([0.0526, 0.0461, 0.0425, 0.0410, 0.0353, 0.0326], dtype=float) * (1e-2 / 3600)
        nu_l = np.array([0.146, 0.128, 0.118, 0.114, 0.098, 0.090], dtype=float) * 1e-6

        self._px = CubicSpline(t, p)
        self._rx = CubicSpline(t, r)
        # Динамическая вязкость mu = nu * rho.
        self._mu_g = CubicSpline(t, nu_g * gamma_g)
        self._mu_l = CubicSpline(t, nu_l * gamma_l)

        # Теплоемкость жидкости для участка догрева до начала кипения.
        t1 = np.array([-50, -40, -30, -20, -10, 0, 10, 20], dtype=float)
        cp1 = np.array([1.84, 1.88, 1.97, 2.05, 2.18, 2.47, 3.14, 5.00], dtype=float) * 1e3
        self._cp_l = CubicSpline(t1, cp1)

        # Более плотная таблица около критической области для давления,
        # теплоты парообразования и удельных объемов фаз.
        # В текущем расчете ниже в основном используются vx и vgx.
        t3 = np.array(
            [216.55, 220, 225, 230, 235, 240, 245, 250, 255, 260, 265, 270, 273.15,
             274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287,
             288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301,
             302, 303, 304.19],
            dtype=float,
        ) - 273.15
        r3 = np.array(
            [347.3, 342.7, 336.7, 330.0, 322.5, 314.2, 304.2, 293.7, 282.3, 270.5,
             257.4, 242.5, 232.5, 229.8, 227.0, 225.9, 220.6, 217.3, 214.0, 210.6,
             207.1, 203.5, 199.8, 196.0, 192.1, 188.1, 183.9, 179.5, 175.0, 170.4,
             165.6, 160.5, 155.2, 149.6, 143.7, 137.3, 130.5, 123.4, 115.8, 107.1,
             97.2, 84.9, 69.0, 0.0],
            dtype=float,
        ) * 1e3
        p3 = np.array(
            [5.18, 6.0, 7.34, 8.91, 10.75, 12.82, 15.18, 17.87, 20.85, 24.21, 27.87,
             32.03, 34.839, 35.633, 36.576, 37.543, 38.521, 39.520, 40.547, 41.588,
             42.654, 43.732, 44.831, 45.956, 47.096, 48.261, 49.450, 50.666, 51.895,
             53.148, 54.432, 55.732, 57.066, 58.421, 59.802, 61.205, 62.639, 64.098,
             65.598, 67.115, 68.661, 70.246, 71.858, 73.815],
            dtype=float,
        ) * 1e5
        v1 = np.array(
            [0.848, 0.857, 0.871, 0.885, 0.901, 0.918, 0.936, 0.956, 0.978, 1.002,
             1.029, 1.059, 1.078, 1.084, 1.092, 1.099, 1.107, 1.115, 1.123, 1.132,
             1.141, 1.150, 1.160, 1.170, 1.181, 1.193, 1.204, 1.217, 1.229, 1.243,
             1.258, 1.273, 1.290, 1.309, 1.329, 1.350, 1.374, 1.401, 1.433, 1.479,
             1.515, 1.573, 1.656, 2.136],
            dtype=float,
        ) * 1e-3
        v2 = np.array(
            [72.464, 63.291, 50.943, 48.103, 36.232, 30.581, 25.773, 21.787, 18.450,
             15.723, 13.387, 11.287, 10.31, 10.04, 9.728, 9.416, 9.116, 8.818, 8.525,
             8.244, 7.968, 7.704, 7.452, 7.210, 6.974, 6.738, 6.502, 6.262, 6.035,
             5.817, 5.605, 5.397, 5.187, 4.980, 4.778, 4.574, 4.372, 4.168, 3.964,
             3.733, 3.504, 3.259, 2.978, 2.136],
            dtype=float,
        ) * 1e-3

        self._px3 = CubicSpline(t3, p3)
        self._rx3 = CubicSpline(t3, r3)
        self._vx = CubicSpline(t3, v1)
        self._vgx = CubicSpline(t3, v2)

    def px(self, t: float | np.ndarray) -> Any:
        """Давление насыщения p_sat(T), Па."""
        return self._px(t)

    def rx(self, t: float | np.ndarray) -> Any:
        """Теплота парообразования r(T), Дж/кг."""
        return self._rx(t)

    def aaa(self, t: float | np.ndarray) -> Any:
        """Производная dp_sat/dT на линии насыщения, Па/К."""
        return self.dp_sat_dT(t)

    def dp_sat_dT(self, t: float | np.ndarray) -> Any:
        """Более понятное имя для производной dp_sat/dT на линии насыщения."""
        return self._px(t, 1)

    def vx(self, t: float | np.ndarray) -> Any:
        """Удельный объем жидкости, м^3/кг. Плотность жидкости равна 1 / vx."""
        return self._vx(t)

    def vgx(self, t: float | np.ndarray) -> Any:
        """Удельный объем пара, м^3/кг. Плотность пара равна 1 / vgx."""
        return self._vgx(t)

    def cp_l(self, t: float | np.ndarray) -> Any:
        """Теплоемкость жидкости, Дж/(кг*К)."""
        return self._cp_l(t)

    def mu_g(self, t: float | np.ndarray) -> Any:
        """Динамическая вязкость пара, Па*с."""
        return self._mu_g(t)

    def mu_l(self, t: float | np.ndarray) -> Any:
        """Динамическая вязкость жидкости, Па*с."""
        return self._mu_l(t)

    def lambda_tot(self, re: float | np.ndarray) -> Any:
        """Сглаженный коэффициент трения Дарси для разных режимов течения."""
        reynolds_number = np.asarray(re, dtype=float)
        friction_laminar = 64.0 / reynolds_number
        friction_blasius = 0.3164 / np.power(reynolds_number, 0.25)
        friction_rough = (1.8 * np.log(8.3 / self.relative_roughness)) ** (-2)
        # p1 плавно переводит расчет из ламинарного режима в турбулентный,
        # p2 — из гладкой трубы в шероховатую. Переход через erf нужен, чтобы
        # избежать нефизических скачков коэффициента трения.
        turbulent_blend = 0.5 + 0.5 * erf((reynolds_number - 2850.0) / (600.0 * np.sqrt(2.0)))
        roughness_blend = erf((reynolds_number * self.relative_roughness) / (275.0 * np.sqrt(2.0)))
        return (
            friction_laminar * (1.0 - turbulent_blend)
            + friction_blasius * turbulent_blend * (1.0 - roughness_blend)
            + friction_rough * turbulent_blend * roughness_blend
        )

    def one_pass(
        self,
        H: float,
        qtr: float,
        Li: float,
        tcon: float,
        f: float,
        ngrid: int = 500,
    ) -> Optional[Dict[str, float]]:
        """Выполняет один полный гидравлический и тепловой проход при заданном ``f``.

        Метод сам по себе не ищет рабочий режим, а принимает ``f`` как известный
        и возвращает:
        - массовые расходы пара и жидкости;
        - вклады в двухфазные потери давления;
        - плотность смеси и требуемый напор ``Hy``.
        """

        # Полная тепловая мощность, подведенная к испарителю.
        total_heat_w = qtr * Li
        # Доля длины испарителя, которая уходит только на догрев жидкости до
        # состояния кипения. Оставшаяся часть 1 - yn является двухфазной зоной.
        #
        # Структура формулы такая:
        # - g * H * rho_l задает характерный гидростатический перепад давления;
        # - деление на dp/dT переводит его в эквивалентный перепад температуры
        #   насыщения;
        # - cp_l переводит этот перепад температуры в чувствительное тепло на кг;
        # - деление на r нормирует его на теплоту парообразования;
        # - множитель (1 + f) учитывает весь циркулирующий расход, а не только
        #   испаряющуюся часть.
        preboiling_length_fraction = (
            ((9.81 * H) * (self.vx(tcon) ** -1)) * (1.0 + f) * self.cp_l(tcon)
        ) / (self.dp_sat_dT(tcon) * self.rx(tcon))
        if (not np.isfinite(preboiling_length_fraction)) or preboiling_length_fraction >= 1.0 or f < 0.0:
            return None

        # Баланс масс на выходе из испарителя:
        # vapor_mass_flow_out_kg_s — образовавшийся расход пара,
        # total_mass_flow_kg_s — полный циркуляционный расход,
        # liquid_mass_flow_in_kg_s — полностью жидкостный расход на входе,
        # liquid_mass_flow_out_kg_s — остаток жидкости после испарения части
        # потока.
        vapor_mass_flow_out_kg_s = total_heat_w / self.rx(tcon)
        total_mass_flow_kg_s = vapor_mass_flow_out_kg_s * (1.0 + f)
        liquid_mass_flow_in_kg_s = total_mass_flow_kg_s
        liquid_mass_flow_out_kg_s = total_mass_flow_kg_s - vapor_mass_flow_out_kg_s

        # Разбиваем двухфазную часть испарителя на 1D-сетку.
        # При равномерном теплоподводе парообразование вдоль кипящего участка
        # растет линейно.
        boiling_coordinate = np.linspace(float(preboiling_length_fraction) + 1e-8, 1.0, ngrid)
        vapor_mass_flow_profile_kg_s = (
            total_heat_w * (boiling_coordinate - preboiling_length_fraction)
        ) / (self.rx(tcon) * (1.0 - preboiling_length_fraction))
        liquid_mass_flow_profile_kg_s = total_mass_flow_kg_s - vapor_mass_flow_profile_kg_s

        # Числа Рейнольдса фаз и массовые потоки через сечение.
        gas_reynolds = (vapor_mass_flow_profile_kg_s * 2.0) / ((self.mu_g(tcon) * np.pi) * self.inner_radius_m)
        liquid_reynolds = (liquid_mass_flow_profile_kg_s * 2.0) / ((self.mu_l(tcon) * np.pi) * self.inner_radius_m)
        gas_mass_flux = vapor_mass_flow_profile_kg_s / (np.pi * self.inner_radius_m**2)
        liquid_mass_flux = liquid_mass_flow_profile_kg_s / (np.pi * self.inner_radius_m**2)

        gas_friction_factor = self.lambda_tot(gas_reynolds)
        liquid_friction_factor = self.lambda_tot(liquid_reynolds)
        # Параметр типа Локхарта-Мартинелли, который переводит жидкостные потери
        # в двухфазные.
        martinelli_parameter = (liquid_mass_flow_profile_kg_s / vapor_mass_flow_profile_kg_s) * np.sqrt(
            (liquid_friction_factor * self.vx(tcon)) / (gas_friction_factor * self.vgx(tcon))
        )
        # Константа Chisholm для разных комбинаций ламинарного и турбулентного
        # режимов по фазам.
        chisholm_constant = np.where(
            (gas_reynolds > 2320.0) & (liquid_reynolds > 2320.0),
            20.0,
            np.where(
                (gas_reynolds > 2320.0) & (liquid_reynolds <= 2320.0),
                12.0,
                np.where((gas_reynolds <= 2320.0) & (liquid_reynolds > 2320.0), 10.0, 5.0),
            ),
        )
        # Двухфазный множитель относительно эталонного жидкостного перепада.
        two_phase_multiplier = 1.0 + chisholm_constant / martinelli_parameter + 1.0 / martinelli_parameter**2
        # Градиент потерь для условного liquid-only течения и его двухфазная
        # поправка.
        liquid_only_pressure_gradient = (
            liquid_friction_factor * self.vx(tcon) * liquid_mass_flux**2
        ) / (4.0 * self.inner_radius_m)
        two_phase_pressure_gradient = (two_phase_multiplier * total_heat_w) * (liquid_only_pressure_gradient / qtr)
        # Интегральные распределенные потери давления на кипящем участке.
        boiling_section_pressure_drop_pa = float(np.trapezoid(two_phase_pressure_gradient, boiling_coordinate))

        # Свойства в выходном сечении нужны для расчета последующего участка и
        # для оценки объемных долей фаз на выходе.
        gas_reynolds_out = (vapor_mass_flow_out_kg_s * 2.0) / ((self.mu_g(tcon) * np.pi) * self.inner_radius_m)
        liquid_reynolds_out = (liquid_mass_flow_out_kg_s * 2.0) / ((self.mu_l(tcon) * np.pi) * self.inner_radius_m)
        gas_mass_flux_out = vapor_mass_flow_out_kg_s / (np.pi * self.inner_radius_m**2)
        liquid_mass_flux_out = liquid_mass_flow_out_kg_s / (np.pi * self.inner_radius_m**2)
        liquid_mass_flux_in = liquid_mass_flow_in_kg_s / (np.pi * self.inner_radius_m**2)

        martinelli_parameter_out = (liquid_mass_flow_out_kg_s / vapor_mass_flow_out_kg_s) * np.sqrt(
            (self.lambda_tot(liquid_reynolds_out) * self.vx(tcon))
            / (self.lambda_tot(gas_reynolds_out) * self.vgx(tcon))
        )
        chisholm_constant_out = (
            20.0 if (gas_reynolds_out > 2320.0 and liquid_reynolds_out > 2320.0)
            else 12.0 if (gas_reynolds_out > 2320.0 and liquid_reynolds_out <= 2320.0)
            else 10.0 if (gas_reynolds_out <= 2320.0 and liquid_reynolds_out > 2320.0)
            else 5.0
        )
        outlet_two_phase_multiplier = (
            1.0 + chisholm_constant_out / martinelli_parameter_out + 1.0 / martinelli_parameter_out**2
        )
        # Замыкающее соотношение из рабочего листа для оценки объемных долей фаз.
        liquid_volume_fraction_out = 1.0 / (outlet_two_phase_multiplier ** (1.0 / 3.0))
        gas_volume_fraction_out = 1.0 - liquid_volume_fraction_out

        # Истинные скорости фаз внутри занимаемых ими частей сечения.
        gas_velocity_out_m_s = (gas_mass_flux_out / gas_volume_fraction_out) * self.vgx(tcon)
        liquid_velocity_out_m_s = (liquid_mass_flux_out / liquid_volume_fraction_out) * self.vx(tcon)
        liquid_velocity_in_m_s = liquid_mass_flux_in * self.vx(tcon)
        # Ускорительные потери давления при переходе от однофазного жидкого
        # потока на входе к раздельному двухфазному потоку на выходе.
        acceleration_pressure_drop_pa = (
            ((self.vx(tcon) ** -1) * (liquid_velocity_out_m_s**2) * liquid_volume_fraction_out)
            + ((self.vgx(tcon) ** -1) * (gas_velocity_out_m_s**2) * gas_volume_fraction_out)
            - ((self.vx(tcon) ** -1) * (liquid_velocity_in_m_s**2))
        )

        # Однофазный жидкостный участок до начала кипения: вертикальная ветвь,
        # подводящий участок и часть испарителя, где идет только догрев.
        preboiling_path_length_m = (H + self.inlet_section_length_m) + (preboiling_length_fraction * Li)
        liquid_reynolds_in = (liquid_mass_flow_in_kg_s * 2.0) / ((self.mu_l(tcon) * np.pi) * self.inner_radius_m)
        inlet_liquid_pressure_drop_pa = (
            (self.lambda_tot(liquid_reynolds_in) * preboiling_path_length_m)
            * self.vx(tcon)
            * (liquid_mass_flux_in**2)
        ) / (self.inner_radius_m * 4.0)
        outlet_liquid_only_pressure_gradient = (
            self.lambda_tot(liquid_reynolds_out) * self.vx(tcon) * (liquid_mass_flux_out**2)
        ) / (4.0 * self.inner_radius_m)
        # Потери в последующем участке, посчитанные по выходным двухфазным
        # параметрам.
        outlet_section_pressure_drop_pa = (
            outlet_two_phase_multiplier * outlet_liquid_only_pressure_gradient * self.outlet_section_length_m
        )

        # Эффективная плотность смеси на выходе и полный перепад давления в
        # контуре.
        outlet_mixture_density_kg_m3 = (
            liquid_volume_fraction_out / self.vx(tcon) + gas_volume_fraction_out / self.vgx(tcon)
        )
        total_pressure_drop_pa = (
            boiling_section_pressure_drop_pa
            + inlet_liquid_pressure_drop_pa
            + outlet_section_pressure_drop_pa
            + acceleration_pressure_drop_pa
        )
        # Требуемый циркуляционный напор. Движущая сила естественной циркуляции
        # равна g * (rho_l - rho_mix). Режим самосогласован, когда Hy == H.
        required_head_m = total_pressure_drop_pa / (
            9.81 * ((self.vx(tcon) ** -1) - outlet_mixture_density_kg_m3)
        )

        return {
            # Ключи результата сохраняют обозначения рабочего листа, чтобы не
            # ломать существующие отчеты и внешние сценарии.
            "U_W": float(total_heat_w),
            "yn": float(preboiling_length_fraction),
            "GG_out_kg_s": float(vapor_mass_flow_out_kg_s),
            "GL_out_kg_s": float(liquid_mass_flow_out_kg_s),
            "GL_in_kg_s": float(liquid_mass_flow_in_kg_s),
            "phiG_formula": float(gas_volume_fraction_out),
            "phiL_formula": float(liquid_volume_fraction_out),
            "VG_out_m_s": float(gas_velocity_out_m_s),
            "VL_out_m_s": float(liquid_velocity_out_m_s),
            "VL_in_m_s": float(liquid_velocity_in_m_s),
            "deltaP_Pa": float(total_pressure_drop_pa),
            "sumPsiL_Pa": float(boiling_section_pressure_drop_pa),
            "delta_pX_Pa": float(inlet_liquid_pressure_drop_pa),
            "delta_pL1_Pa": float(outlet_section_pressure_drop_pa),
            "delta_Pu_Pa": float(acceleration_pressure_drop_pa),
            "rhoef_kg_m3": float(outlet_mixture_density_kg_m3),
            "Hy_m": float(required_head_m),
            # Массовая сухость на выходе: chi = GG / (GG + GL) = 1 / (1 + f).
            "chiG1_mass": float(1.0 / (1.0 + f)),
            # Объемные расходы в жидкостном эквиваленте в обозначениях исходного
            # рабочего листа и его таблиц.
            "GL1_lph": float(liquid_mass_flow_out_kg_s * self.vx(tcon) * 1000.0 * 3600.0),
            "GL0_lph": float(liquid_mass_flow_in_kg_s * self.vx(tcon) * 1000.0 * 3600.0),
            "GG0_lph": float(vapor_mass_flow_out_kg_s * self.vx(tcon) * 1000.0 * 3600.0),
            # Истинное газосодержание на выходе по объемным расходам фаз.
            "phiG1_true": float(
                (vapor_mass_flow_out_kg_s * self.vgx(tcon))
                / (
                    (vapor_mass_flow_out_kg_s * self.vgx(tcon))
                    + (liquid_mass_flow_out_kg_s * self.vx(tcon))
                )
            ),
        }

    def hy_minus_H(self, H: float, qtr: float, Li: float, tcon: float, f: float) -> float:
        """Невязка главного циркуляционного баланса для пробного значения ``f``."""
        pass_result = self.one_pass(H=H, qtr=qtr, Li=Li, tcon=tcon, f=f, ngrid=250)
        if pass_result is None or not np.isfinite(pass_result["Hy_m"]):
            return np.nan
        return pass_result["Hy_m"] - H

    def solve_f(self, H: float, qtr: float, Li: float, tcon: float, fmin: float = 1e-6, fmax: float = 200.0, nsamp: int = 220) -> Optional[float]:
        """Подбирает параметр циркуляции ``f`` из условия Hy(f) = H."""
        circulation_factor_grid = np.logspace(np.log10(fmin), np.log10(fmax), nsamp)
        head_residuals = np.array([self.hy_minus_H(H, qtr, Li, tcon, f) for f in circulation_factor_grid], dtype=float)
        finite_mask = np.isfinite(head_residuals)
        sign_change_indices = np.where(
            finite_mask[:-1] & finite_mask[1:] & (head_residuals[:-1] * head_residuals[1:] < 0.0)
        )[0]
        if len(sign_change_indices) == 0:
            return None
        bracket_index = int(sign_change_indices[0])
        # Метод Брента надежен, если уже найден отрезок со сменой знака.
        sol = root_scalar(
            lambda f: self.hy_minus_H(H, qtr, Li, tcon, f),
            bracket=[circulation_factor_grid[bracket_index], circulation_factor_grid[bracket_index + 1]],
            method="brentq",
            xtol=1e-10,
            rtol=1e-10,
        )
        return float(sol.root)

    def solve_tmm(self, H: float, qtr: float, Li: float, tcon: float, f: float) -> Optional[float]:
        """Восстанавливает вспомогательную температуру насыщения из рабочего листа.

        Уравнение переводит гидростатические и фрикционные перепады давления в
        эквивалентные сдвиги температуры насыщения через dp_sat/dT.
        """
        pass_result = self.one_pass(H=H, qtr=qtr, Li=Li, tcon=tcon, f=f, ngrid=500)
        if pass_result is None:
            return None
        inlet_liquid_pressure_drop_pa = pass_result["delta_pX_Pa"]

        def temperature_residual(candidate_temperature_c: float) -> float:
            mean_temperature_c = 0.5 * (candidate_temperature_c + tcon)
            return (
                (tcon - candidate_temperature_c)
                - (inlet_liquid_pressure_drop_pa / self.dp_sat_dT(mean_temperature_c))
                + ((9.81 * H) / (self.vx(mean_temperature_c) * self.dp_sat_dT(mean_temperature_c)))
            )

        temperature_grid_c = np.linspace(tcon - 50.0, tcon + 10.0, 800)
        residual_values = np.array([temperature_residual(t) for t in temperature_grid_c], dtype=float)
        sign_change_indices = np.where(
            np.isfinite(residual_values[:-1])
            & np.isfinite(residual_values[1:])
            & (residual_values[:-1] * residual_values[1:] < 0.0)
        )[0]
        if len(sign_change_indices) == 0:
            return None
        bracket_index = int(sign_change_indices[0])
        sol = root_scalar(
            temperature_residual,
            bracket=[temperature_grid_c[bracket_index], temperature_grid_c[bracket_index + 1]],
            method="brentq",
            xtol=1e-12,
            rtol=1e-12,
        )
        return float(sol.root)

    def run(self, H: float, qtr: float, Li: float, tcon: float) -> Dict[str, float | bool]:
        """Решает один режим полностью от начала до конца."""
        circulation_factor = self.solve_f(H=H, qtr=qtr, Li=Li, tcon=tcon)
        if circulation_factor is None:
            return {"converged": False, "H": H, "qtr": qtr, "Li": Li, "tcon": tcon}

        pass_result = self.one_pass(H=H, qtr=qtr, Li=Li, tcon=tcon, f=circulation_factor, ngrid=1200)
        if pass_result is None:
            return {"converged": False, "H": H, "qtr": qtr, "Li": Li, "tcon": tcon}

        auxiliary_temperature_c = self.solve_tmm(H=H, qtr=qtr, Li=Li, tcon=tcon, f=circulation_factor)
        # Переводим характерные гидростатические перепады давления обратно в
        # эквивалентные температуры насыщения, как это делает рабочий лист.
        outlet_mixture_temperature_c = tcon + (9.81 * ((H * pass_result["rhoef_kg_m3"]) / self.dp_sat_dT(tcon)))
        # Средняя температура как длиновзвешенная комбинация участка догрева и
        # кипящего участка испарителя.
        average_temperature_c = (
            0.5 * (tcon + auxiliary_temperature_c) * pass_result["yn"]
            + 0.5 * (outlet_mixture_temperature_c + auxiliary_temperature_c) * (1.0 - pass_result["yn"])
        )
        total_heat_w = qtr * Li
        # Нормированные теплогидравлические показатели из рабочего листа,
        # сохраненные для сверки с исходным Mathcad-файлом.
        normalized_head_indicator = (
            (0.5 * (((9.81 * pass_result["Hy_m"]) * (self.vx(tcon) ** -1)))) / (total_heat_w * self.dp_sat_dT(tcon))
        )
        normalized_temperature_indicator = (average_temperature_c - tcon) / total_heat_w
        geometric_head_indicator = ((0.5 * 9.81) * H) / ((self.dp_sat_dT(tcon) * self.vx(tcon)) * total_heat_w)

        result: Dict[str, float | bool] = {
            "converged": True,
            "H": H,
            "qtr": qtr,
            "Li": Li,
            "tcon": tcon,
            "fff": float(circulation_factor),
            "tmm_C": float(auxiliary_temperature_c),
            "tav_C": float(average_temperature_c),
            "tvih_C": float(outlet_mixture_temperature_c),
            "RVN0": float(normalized_head_indicator),
            "RVN": float(normalized_temperature_indicator),
            "RV1": float(geometric_head_indicator),
        }
        result.update(pass_result)
        return result

    def cached_checks(self) -> Dict[str, Dict[str, float]]:
        """Возвращает несколько точных или почти точных контрольных точек."""
        # Значения, которые видны в кэше рабочего листа или однозначно следуют
        # из его констант.
        expected = {
            "px_m10_Pa": 2647719.0,
            "rx_m10_J_kg": 261716.868,
            "RV1_default": 8.008966711394417e-06,
            "R2x": 1.8356164383561646,
        }
        actual = {
            "px_m10_Pa": float(self.px(-10.0)),
            "rx_m10_J_kg": float(self.rx(-10.0)),
            "RV1_default": float(((0.5 * 9.81) * 2.5) / ((self.dp_sat_dT(0.0) * self.vx(0.0)) * (76.68 * 200.0))),
            "R2x": float(self.reference_diameter_2_m / self.reference_diameter_1_m),
        }
        rel_err = {
            key: float(abs(actual[key] - expected[key]) / abs(expected[key])) if expected[key] != 0 else 0.0
            for key in expected
        }
        return {"expected": expected, "actual": actual, "rel_err": rel_err}



DEFAULT_SCENARIOS = [
    Scenario(name="xmcd_default", H=2.5, qtr=76.68, Li=200.0, tcon=0.0),
    Scenario(name="co2_lower_benchmark_qmin_table4_5", H=2.5, qtr=2.48, Li=200.0, tcon=0.0),
    Scenario(name="co2_upper_benchmark_qmax_appG3", H=2.5, qtr=71.18, Li=200.0, tcon=0.0),
    Scenario(name="moderate_regime_q20", H=2.5, qtr=20.0, Li=200.0, tcon=0.0),
    Scenario(name="hot_regime_q90", H=2.5, qtr=90.0, Li=200.0, tcon=0.0),
]
