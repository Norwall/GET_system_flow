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

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np

from co2_geometry import LoopGeometry
from co2_properties import CO2SaturationProperties
from co2_results import SteadyLoopResult
from co2_steady_solver import SteadyLoopInputs, SteadyLoopSolver
from two_phase_closures import darcy_friction_factor


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
    критических таблиц из приложений этим портом не гарантируется.
    """

    def __init__(self) -> None:
        # Геометрия и пакет свойств вынесены в отдельные модули, чтобы далее
        # можно было заменять или сравнивать разные физические closure-модели
        # без переписывания решателя.
        self.geometry = LoopGeometry()
        self.properties = CO2SaturationProperties()

        self.inner_radius_m = self.geometry.inner_radius_m
        self.reference_diameter_1_m = self.geometry.reference_diameter_1_m
        self.reference_diameter_2_m = self.geometry.reference_diameter_2_m
        self.outlet_section_length_m = self.geometry.outlet_section_length_m
        self.inlet_section_length_m = self.geometry.inlet_section_length_m
        self.relative_roughness = self.geometry.relative_roughness
        self.flow_area_m2 = self.geometry.flow_area_m2
        self.hydraulic_diameter_m = self.geometry.hydraulic_diameter_m
        self.steady_solver = SteadyLoopSolver(geometry=self.geometry, properties=self.properties)

        # Старые имена оставлены как алиасы, чтобы не ломать совместимость с
        # существующими отчетами, проверками и внешними сценариями.
        self.aa = self.inner_radius_m
        self.d1 = self.reference_diameter_1_m
        self.d2 = self.reference_diameter_2_m
        self.Lot = self.outlet_section_length_m
        self.Lpod = self.inlet_section_length_m
        self.Delta = self.relative_roughness

    def px(self, t: float | np.ndarray) -> Any:
        """Давление насыщения p_sat(T), Па."""
        return self.properties.pressure_pa(t)

    def rx(self, t: float | np.ndarray) -> Any:
        """Теплота парообразования r(T), Дж/кг."""
        return self.properties.latent_heat_j_per_kg(t)

    def aaa(self, t: float | np.ndarray) -> Any:
        """Производная dp_sat/dT на линии насыщения, Па/К."""
        return self.dp_sat_dT(t)

    def dp_sat_dT(self, t: float | np.ndarray) -> Any:
        """Более понятное имя для производной dp_sat/dT на линии насыщения."""
        return self.properties.dp_sat_dT_pa_per_k(t)

    def vx(self, t: float | np.ndarray) -> Any:
        """Удельный объем жидкости, м^3/кг. Плотность жидкости равна 1 / vx."""
        return self.properties.liquid_specific_volume_m3_per_kg(t)

    def vgx(self, t: float | np.ndarray) -> Any:
        """Удельный объем пара, м^3/кг. Плотность пара равна 1 / vgx."""
        return self.properties.vapor_specific_volume_m3_per_kg(t)

    def cp_l(self, t: float | np.ndarray) -> Any:
        """Теплоемкость жидкости, Дж/(кг*К)."""
        return self.properties.liquid_heat_capacity_j_per_kgk(t)

    def mu_g(self, t: float | np.ndarray) -> Any:
        """Динамическая вязкость пара, Па*с."""
        return self.properties.vapor_dynamic_viscosity_pa_s(t)

    def mu_l(self, t: float | np.ndarray) -> Any:
        """Динамическая вязкость жидкости, Па*с."""
        return self.properties.liquid_dynamic_viscosity_pa_s(t)

    def lambda_tot(self, re: float | np.ndarray) -> Any:
        """Сглаженный коэффициент трения Дарси для разных режимов течения."""
        return darcy_friction_factor(re, self.relative_roughness)

    def one_pass(
        self,
        H: float,
        qtr: float,
        Li: float,
        tcon: float,
        f: float,
        ngrid: int = 500,
        mode: str = "worksheet_compatible",
        closure_model: str = "worksheet_compatible",
    ) -> Optional[Dict[str, float]]:
        """Совместимый фасад над отдельным steady-state solver."""
        pass_result = self.steady_solver.one_pass(
            inputs=SteadyLoopInputs(H=H, qtr=qtr, Li=Li, tcon=tcon, mode=mode, closure_model=closure_model),
            circulation_factor=f,
            ngrid=ngrid,
        )
        if pass_result is None:
            return None
        return pass_result.to_dict()

    def hy_minus_H(self, H: float, qtr: float, Li: float, tcon: float, f: float, mode: str = "worksheet_compatible", closure_model: str = "worksheet_compatible") -> float:
        """Невязка главного циркуляционного баланса для пробного значения ``f``."""
        return self.steady_solver.head_residual(
            inputs=SteadyLoopInputs(H=H, qtr=qtr, Li=Li, tcon=tcon, mode=mode, closure_model=closure_model),
            circulation_factor=f,
        )

    def solve_f(self, H: float, qtr: float, Li: float, tcon: float, fmin: float = 1e-6, fmax: float = 200.0, nsamp: int = 220, mode: str = "worksheet_compatible", closure_model: str = "worksheet_compatible") -> Optional[float]:
        """Подбирает параметр циркуляции ``f`` из условия Hy(f) = H."""
        root_search = self.steady_solver.find_circulation_factor(
            inputs=SteadyLoopInputs(H=H, qtr=qtr, Li=Li, tcon=tcon, mode=mode, closure_model=closure_model),
            fmin=fmin,
            fmax=fmax,
            nsamp=nsamp,
        )
        return root_search.circulation_factor

    def solve_tmm(self, H: float, qtr: float, Li: float, tcon: float, f: float, mode: str = "worksheet_compatible", closure_model: str = "worksheet_compatible") -> Optional[float]:
        """Восстанавливает вспомогательную температуру насыщения из рабочего листа."""
        auxiliary_temperature_c, _ = self.steady_solver.solve_auxiliary_temperature(
            inputs=SteadyLoopInputs(H=H, qtr=qtr, Li=Li, tcon=tcon, mode=mode, closure_model=closure_model),
            circulation_factor=f,
        )
        return auxiliary_temperature_c

    def run_result(self, H: float, qtr: float, Li: float, tcon: float, mode: str = "worksheet_compatible", closure_model: str = "worksheet_compatible") -> SteadyLoopResult:
        """Возвращает структурированный результат расчета с диагностикой решателя."""
        return self.steady_solver.solve(
            SteadyLoopInputs(H=H, qtr=qtr, Li=Li, tcon=tcon, mode=mode, closure_model=closure_model)
        )

    def run(self, H: float, qtr: float, Li: float, tcon: float, mode: str = "worksheet_compatible", closure_model: str = "worksheet_compatible") -> Dict[str, float | bool | str | tuple[float, float] | None]:
        """Совместимый пользовательский API поверх нового результата-датакласса."""
        return self.run_result(H=H, qtr=qtr, Li=Li, tcon=tcon, mode=mode, closure_model=closure_model).to_dict()

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
