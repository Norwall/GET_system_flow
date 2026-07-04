# Реестр формул и свойств

Версия реестра: `checkpoint-10-source-gated-regime-model`.

Этот документ связывает реализованный код, формулы, источник, область применимости и
тесты. Статус `PUBLISHED` допустим только для формул и коэффициентов, которые
прослеживаются до публикации, справочника или стандартной физической записи.
Текущие эвристики режимно-зависимого расчета явно помечены как
`EXPERIMENTAL / NO PRIMARY SOURCE`.

Для каждой реализованной записи обязательны поля: статус, математическая запись,
переменные и размерности, область применимости, источник, код и тесты.

## Сводка реализованных записей

| ID | Статус | Код |
| --- | --- | --- |
| `PROP-MATHCAD-CO2-TABLE` | MATHCAD_COMPATIBLE | `MathcadCO2SaturationProperties` |
| `PROP-COOLPROP-CO2-HEOS` | PUBLISHED | `CoolPropSaturationProperties(fluid="CO2")` |
| `PROP-COOLPROP-NH3-HEOS` | PUBLISHED | `CoolPropSaturationProperties(fluid="NH3")` |
| `PROP-REFPROP-ADAPTER` | OPTIONAL_ADAPTER | `RefpropSaturationProperties` |
| `BAL-HEAT-INPUT` | DISSERTATION | `SteadyLoopSolver.one_pass` |
| `HEAT-LINEAR-TO-WALL-FLUX` | DEFINITIONAL | `boiling_heat_transfer.diagnose_prescribed_heat_input` |
| `BAL-VAPOR-GENERATION` | DISSERTATION | `SteadyLoopSolver.one_pass` |
| `BAL-PREBOILING-FRACTION` | DISSERTATION / MATHCAD_COMPATIBLE | `SteadyLoopSolver.one_pass` |
| `QCRIT-DISSERTATION-SCAN` | DISSERTATION / NUMERICAL_SEARCH | `critical_loads.find_critical_loads` |
| `QCRIT-DISSERTATION-F-ZERO` | DISSERTATION | `critical_loads.CriticalLoadSolver.f_zero_residual` |
| `FRIC-REYNOLDS` | PUBLISHED | `co2_steady_solver`, `two_phase_closures` |
| `FRIC-DARCY-MASS-FLUX` | PUBLISHED | `published_friction.single_phase_pressure_gradient_pa_per_m` |
| `FRIC-LAMINAR-DARCY` | PUBLISHED | `darcy_friction_factor` |
| `FRIC-BLASIUS-SMOOTH` | PUBLISHED | `darcy_friction_factor` |
| `FRIC-LEGACY-BLENDED-DARCY` | MATHCAD_COMPATIBLE / REQUIRES_AUDIT | `darcy_friction_factor` |
| `FRIC-COLEBROOK-WHITE` | PUBLISHED | `colebrook_white_friction_factor` |
| `FRIC-CHURCHILL-1977` | PUBLISHED | `churchill_1977_friction_factor` |
| `FRIC-ZERO-TEST` | TEST_ONLY | `friction_factor_from_model("zero_friction")` |
| `TP-LOCKHART-MARTINELLI` | PUBLISHED | `published_friction.martinelli_parameter` |
| `TP-CHISHOLM-CONSTANT` | PUBLISHED | `published_friction.chisholm_constant` |
| `TP-CHISHOLM-MULTIPLIER` | PUBLISHED | `published_friction.two_phase_multiplier_liquid_reference` |
| `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` | SOURCE_REQUIRED | `published_friction.muller_steinhagen_heck_1986_pressure_gradient_pa_per_m` |
| `TP-FRIEDEL-1979-SOURCE-GATE` | SOURCE_REQUIRED | `published_friction.friedel_1979_pressure_gradient_pa_per_m` |
| `FLOW-MASS-QUALITY` | PUBLISHED / DEFINITIONAL | `published_void_fraction.mass_quality_from_mass_flows` |
| `VOID-GENERIC-SLIP` | PUBLISHED / DEFINITIONAL | `published_void_fraction.void_fraction_from_quality` |
| `VOID-WORKSHEET-PHI2L` | MATHCAD_COMPATIBLE / DISSERTATION | `worksheet_void_fraction_from_phi2l` |
| `VOID-HOMOGENEOUS-EQUILIBRIUM` | PUBLISHED LIMITING MODEL | `published_void_fraction.homogeneous_equilibrium_slip_ratio` |
| `VOID-ZIVI-1964` | PUBLISHED | `published_void_fraction.zivi_1964_slip_ratio` |
| `FLOW-PHASE-VELOCITIES` | DEFINITIONAL | `compute_phase_velocities` |
| `FLOW-SLIP-RATIO` | DEFINITIONAL | `compute_slip_ratio` |
| `FLOW-MIXTURE-DENSITY` | DEFINITIONAL | `compute_mixture_density` |
| `PRESS-ACCELERATION-MOMENTUM` | DISSERTATION / ENGINEERING | `SteadyLoopSolver.one_pass` |
| `PRESS-WORKSHEET-DRIVING-HEAD` | DISSERTATION / MATHCAD_COMPATIBLE | `SteadyLoopSolver.one_pass` |
| `PRESS-DISTRIBUTED-RISER-GRADIENT` | ENGINEERING / REQUIRES_AUDIT | `SteadyLoopSolver._one_pass_distributed` |
| `PRESS-HYDROSTATIC-SECTION` | PUBLISHED / DEFINITIONAL | `pressure_balance.hydrostatic_pressure_pa` |
| `PRESS-LOOP-BALANCE` | PUBLISHED / DEFINITIONAL | `LoopPressureBalance` |
| `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE` | SOURCE_REQUIRED | `published_regimes.py`, future drift-flux adapter |
| `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE` | SOURCE_REQUIRED | `published_regimes.classify_horizontal_evaporator_regime_result` |
| `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` | SOURCE_REQUIRED | `published_regimes.classify_vertical_riser_regime_result` |
| `EXP-REGIME-AWARE-CLASSIFIERS` | EXPERIMENTAL / NO PRIMARY SOURCE | `experimental_regimes.py` |
| `EXP-DRIFT-FLUX-LIKE-VOID` | EXPERIMENTAL / NO PRIMARY SOURCE | `drift_flux_void_fraction` |
| `EXP-ANNULAR-CORE-VOID` | EXPERIMENTAL / NO PRIMARY SOURCE | `annular_core_void_fraction` |
| `EXP-REGIME-FRICTION-GRADIENTS` | EXPERIMENTAL / NO PRIMARY SOURCE | `_resolve_two_phase_friction_response` |
| `SCENARIO-MATRIX-STATUS` | REGRESSION_DIAGNOSTIC | `scenario_matrix.run_scenario_case` |

## Интерфейс свойств

Все backend-реализации свойств возвращают насыщенное состояние жидкости и пара
через общую структуру:

```python
SaturationState(
    fluid,
    temperature_c,
    pressure_pa,
    dp_sat_dT_pa_per_k,
    h_l_j_kg,
    h_g_j_kg,
    latent_heat_j_kg,
    rho_l_kg_m3,
    rho_g_kg_m3,
    v_l_m3_kg,
    v_g_m3_kg,
    mu_l_pa_s,
    mu_g_pa_s,
    cp_l_j_kgk,
    cp_g_j_kgk,
    k_l_w_mk,
    k_g_w_mk,
    surface_tension_n_m,
)
```

Старые имена полей сохранены как compatibility aliases:
`latent_heat_j_per_kg`, `v_l_m3_per_kg`, `v_g_m3_per_kg`,
`cp_l_j_per_kgk`.

## PROP-MATHCAD-CO2-TABLE

- Статус: MATHCAD_COMPATIBLE.
- Математическая запись: табличная интерполяция свойств насыщенного CO2 из исходного worksheet.
- Переменные и размерности: `T_sat`, град C; `p_sat`, Па; `h_g - h_l`, Дж/кг; `rho`, кг/м3; `v`, м3/кг; `mu`, Па с; `cp_l`, Дж/(кг К).
- Область применимости: только CO2/R744; Mathcad-compatible ветка.
- Источник: `CO2.xmcd`; проектная академическая справка связывает таблицы с исходным Mathcad-листом и справочными данными по CO2.
- Код: `refrigerant_properties.MathcadCO2SaturationProperties`; compatibility alias `co2_properties.CO2SaturationProperties`.
- Тесты: `tests/test_refrigerant_properties.py`; `tests/test_co2_properties_baseline.py`.

## PROP-COOLPROP-CO2-HEOS

- Статус: PUBLISHED.
- Математическая запись: вызовы CoolProp HEOS через `PropsSI` на линии насыщения.
- Переменные и размерности: температура насыщения, K или град C; давление, Па; качество `Q=0` для жидкости и `Q=1` для пара; остальные свойства в SI.
- Область применимости: aliases CO2/R744/CarbonDioxide в диапазоне насыщения CoolProp ниже критической точки.
- Источник: CoolProp HEOS; Span and Wagner, equation of state for carbon dioxide, DOI `10.1063/1.555991`.
- Код: `refrigerant_properties.CoolPropSaturationProperties(fluid="CO2")`.
- Reference CSV: `data/reference_properties/co2_saturation_coolprop.csv`.
- Тесты: `tests/test_refrigerant_properties.py`; `tests/test_nh3_properties.py`; `tests/test_refrigerant_loop_model.py`.

## PROP-COOLPROP-NH3-HEOS

- Статус: PUBLISHED.
- Математическая запись: вызовы CoolProp HEOS через `PropsSI` на линии насыщения.
- Переменные и размерности: температура насыщения, K или град C; давление, Па; качество `Q=0` для жидкости и `Q=1` для пара; остальные свойства в SI.
- Область применимости: aliases NH3/R717/Ammonia в диапазоне насыщения CoolProp ниже критической точки.
- Источник: CoolProp HEOS; Gao, Wu, Bell, Lemmon, ammonia EOS, J. Phys. Chem. Ref. Data, 2020.
- Код: `refrigerant_properties.CoolPropSaturationProperties(fluid="NH3")`.
- Reference CSV: `data/reference_properties/nh3_saturation_coolprop.csv`.
- Тесты: `tests/test_refrigerant_properties.py`; `tests/test_nh3_properties.py`; `tests/test_nh3_loop_solver.py`; `tests/test_refrigerant_loop_model.py`.

## PROP-REFPROP-ADAPTER

- Статус: OPTIONAL_ADAPTER.
- Математическая запись: тот же интерфейс `RefrigerantSaturationProperties`, но через строку backend `REFPROP::` в CoolProp.
- Переменные и размерности: те же SI-свойства насыщения, что и у CoolProp backend.
- Область применимости: опциональный адаптер NIST REFPROP для поддерживаемых веществ при наличии лицензированной установки REFPROP.
- Источник: NIST REFPROP.
- Код: `refrigerant_properties.RefpropSaturationProperties`.
- Тесты: `tests/test_refrigerant_properties.py`.

## BAL-HEAT-INPUT

- Статус: DISSERTATION.
- Математическая запись: `U = q_l L_i`.
- Переменные и размерности: `U`, Вт; `q_l`/`qtr`, Вт/м; `L_i`, м.
- Область применимости: текущая постановка с заданной линейной тепловой нагрузкой.
- Источник: `CO2.xmcd`; диссертационная постановка теплового баланса; `docs/get_co2_academic_reference.md`.
- Код: `co2_steady_solver.SteadyLoopSolver.one_pass`; `get_co2_model.CO2MathcadModel.run`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_model_regression.py`.

## HEAT-LINEAR-TO-WALL-FLUX

- Статус: DEFINITIONAL.
- Математическая запись:

```math
q'' = \frac{q_l}{P_h},
\qquad
P_h = \frac{4A}{D_h}
```

- Переменные и размерности: `q''`, Вт/м2; `q_l`/`qtr`, Вт/м; `P_h`, м; `A`, м2; `D_h`, м.
- Область применимости: диагностический пересчёт заданной линейной тепловой нагрузки в средний тепловой поток на смоченный периметр испарителя. Не является корреляцией теплоотдачи, dryout или CHF.
- Источник: определение гидравлического диаметра и теплового потока через площадь поверхности; без эмпирических коэффициентов.
- Код: `boiling_heat_transfer.hydraulic_perimeter_m`; `boiling_heat_transfer.diagnose_prescribed_heat_input`; `co2_steady_solver.SteadyLoopSolver._result_common_fields`.
- Тесты: `tests/test_boiling_diagnostics.py`; `tests/test_co2_result_fields.py`.

## BAL-VAPOR-GENERATION

- Статус: DISSERTATION.
- Математическая запись:

```math
\dot m_g(z)=\frac{Q(z)}{h_g-h_l}
```

- Переменные и размерности: `dot m_g`, кг/с; `Q(z)`, Вт; `h_g-h_l`, Дж/кг.
- Область применимости: насыщенная зона кипения при заданном тепловом потоке.
- Источник: баланс энергии; `CO2.xmcd`; диссертация; `docs/get_co2_academic_reference.md`.
- Код: `co2_steady_solver.SteadyLoopSolver.one_pass`; `co2_steady_solver.SteadyLoopSolver._one_pass_distributed`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`; `tests/test_regime_maps.py`.

## BAL-PREBOILING-FRACTION

- Статус: DISSERTATION / MATHCAD_COMPATIBLE.
- Математическая запись:

```math
y_n =
\frac{gH\rho_l(1+f)c_{p,l}}
{(dp_s/dT)(h_g-h_l)}
```

- Переменные и размерности: `y_n`, безразмерная доля; `H`, м; `rho_l`, кг/м3; `f`, безразмерный параметр циркуляции; `c_p`, Дж/(кг К); `dp_s/dT`, Па/К; `h_g-h_l`, Дж/кг.
- Область применимости: Mathcad-derived оценка участка до начала кипения.
- Источник: `CO2.xmcd`; уравнения диссертации; `docs/get_co2_academic_reference.md`.
- Код: `co2_steady_solver.SteadyLoopSolver.one_pass`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_model_regression.py`.

## QCRIT-DISSERTATION-SCAN

- Статус: DISSERTATION / NUMERICAL_SEARCH.
- Математическая запись:

```math
q_{\rm cr}^{\min}<q_l<q_{\rm cr}^{\max}
```

Границы определяются как нижняя и верхняя граница интервала тепловых нагрузок, для которых существует стационарное решение текущей системы уравнений. В реализации конечная сетка используется только для bracket-поиска, после чего граница уточняется бисекцией; последняя сошедшаяся точка сетки сама по себе не объявляется физическим `qcrit`.

- Переменные и размерности: `q_l`/`qtr`, Вт/м; `H`, м; `L_i`, м; `tcon`, град C; `f`, безразмерный параметр циркуляции.
- Область применимости: стационарная модель ГЕТ с заданной линейной тепловой нагрузкой и выбранными свойствами/closure-моделью. Результат относится к текущей реализации solver и не является экспериментальной валидацией.
- Источник: диссертация А. А. Ишкова, разделы 2.4 и 4.3; `docs/get_co2_academic_reference.md`.
- Код: `critical_loads.find_critical_loads`; `critical_loads.CriticalLoadSolver.evaluate_qtr`; фасады `CO2MathcadModel.critical_loads` и `RefrigerantLoopModel.critical_loads`.
- Тесты: `tests/test_qcrit_solver.py`.

## QCRIT-DISSERTATION-F-ZERO

- Статус: DISSERTATION.
- Математическая запись:

```math
f=0,\qquad x_{\rm out}=1,\qquad \alpha_{\rm out}=1,
\qquad Hy(q_l,f=0)-H=0
```

- Переменные и размерности: `f`, безразмерный параметр циркуляции; `x_out`, массовая сухость на выходе; `alpha_out`, паросодержание на выходе; `Hy`, м; `H`, м; `q_l`, Вт/м.
- Область применимости: верхняя гидродинамическая критическая нагрузка по предельной постановке диссертации. Не является dryout/CHF/HTC-корреляцией.
- Источник: диссертация А. А. Ишкова, раздел 2.4; `docs/get_co2_academic_reference.md`.
- Код: `critical_loads.CriticalLoadSolver.f_zero_residual`; `critical_loads.find_critical_loads`.
- Тесты: `tests/test_qcrit_solver.py`.

## FRIC-REYNOLDS

- Статус: PUBLISHED.
- Математическая запись:

```math
Re = \frac{G D_h}{\mu}
```

- Переменные и размерности: `G`, кг/(м2 с); `D_h`, м; `mu`, Па с.
- Область применимости: фазовые и однофазные числа Reynolds в текущей трубной гидравлике.
- Источник: классическая гидравлика внутреннего течения; `docs/get_co2_academic_reference.md`.
- Код: `co2_steady_solver.SteadyLoopSolver.one_pass`; `co2_steady_solver.SteadyLoopSolver._one_pass_distributed`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## FRIC-DARCY-MASS-FLUX

- Статус: PUBLISHED.
- Математическая запись:

```math
\frac{dp_f}{dz}=f_D\frac{G^2}{2\rho D_h}
=f_D\frac{vG^2}{2D_h}
```

- Переменные и размерности: `dp_f/dz`, Па/м; `f_D`, безразмерный Darcy friction factor; `G`, кг/(м2 с); `rho`, кг/м3; `v=1/rho`, м3/кг; `D_h`, м.
- Область применимости: однофазный градиент давления и жидкостная база для двухфазного множителя.
- Источник: Darcy-Weisbach в форме через массовый поток; `docs/get_co2_academic_reference.md`.
- Код: `two_phase_closures.single_phase_pressure_gradient_pa_per_m`; эквивалентные inline-выражения в `co2_steady_solver.py`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## FRIC-LAMINAR-DARCY

- Статус: PUBLISHED.
- Математическая запись:

```math
f_D = \frac{64}{Re}
```

- Переменные и размерности: `f_D` и `Re` безразмерны.
- Область применимости: ламинарная ветка текущей blended-модели трения.
- Источник: Hagen-Poiseuille для ламинарного трубного течения.
- Код: `two_phase_closures.darcy_friction_factor`.
- Тесты: `tests/test_mathcad_log_audit.py`; `tests/test_baseline_compatibility.py`.

## FRIC-BLASIUS-SMOOTH

- Статус: PUBLISHED.
- Математическая запись:

```math
f_D = \frac{0.3164}{Re^{0.25}}
```

- Переменные и размерности: `f_D` и `Re` безразмерны.
- Область применимости: гладкая турбулентная ветка внутри текущей blended-модели трения.
- Источник: аппроксимация Blasius; `docs/get_co2_academic_reference.md`.
- Код: `two_phase_closures.darcy_friction_factor`.
- Тесты: `tests/test_mathcad_log_audit.py`; `tests/test_baseline_compatibility.py`.

## FRIC-LEGACY-BLENDED-DARCY

- Статус: MATHCAD_COMPATIBLE / REQUIRES_AUDIT.
- Математическая запись:

```math
f_D=f_{\rm lam}(1-w_t)+f_{\rm Bl}w_t(1-w_r)+f_{\rm rough}w_tw_r
```

```math
f_{\rm rough} =
\left[1.8\log_b\left(\frac{8.3}{\varepsilon/D_h}\right)\right]^{-2}
```

В текущем Python-коде по умолчанию `b=e`; audit-ветка позволяет `b=10`.

- Переменные и размерности: `Re` и `epsilon/D_h` безразмерны; `w_t`, `w_r` — веса сглаживания через `erf`.
- Область применимости: legacy friction behavior для совместимости с текущими baseline. Эта запись не является опубликованным уравнением Colebrook-White.
- Источник: `CO2.xmcd`; аудит логарифма Mathcad/Python в `docs/get_co2_academic_reference.md`.
- Код: `two_phase_closures.darcy_friction_factor`; `rough_turbulent_friction_factor_ln`; `rough_turbulent_friction_factor_log10`.
- Тесты: `tests/test_mathcad_log_audit.py`; `tests/test_baseline_compatibility.py`.

## FRIC-COLEBROOK-WHITE

- Статус: PUBLISHED.
- Математическая запись:

```math
\frac{1}{\sqrt{f_D}} =
-2\log_{10}\left(
\frac{\varepsilon/D_h}{3.7}
+\frac{2.51}{Re\sqrt{f_D}}
\right)
```

- Переменные и размерности: `f_D`, `Re`, `epsilon/D_h` безразмерны.
- Область применимости: турбулентное однофазное трубное течение; в коде ламинарная ветка `64/Re` используется ниже `Re=2300`.
- Источник: Colebrook, White, 1939, Journal of the Institution of Civil Engineers, https://doi.org/10.1680/ijoti.1939.13150.
- Код: `two_phase_closures.colebrook_white_friction_factor`; `two_phase_closures.friction_factor_from_model`.
- Тесты: `tests/test_pressure_balance.py`; `tests/test_mathcad_log_audit.py`.

## FRIC-CHURCHILL-1977

- Статус: PUBLISHED.
- Математическая запись:

```math
f_D=8\left[\left(\frac{8}{Re}\right)^{12}
+(A+B)^{-3/2}\right]^{1/12}
```

```math
A=\left[2.457\ln\frac{1}{(7/Re)^{0.9}+0.27\varepsilon/D_h}\right]^{16},
\quad
B=\left(\frac{37530}{Re}\right)^{16}
```

- Переменные и размерности: `f_D`, `Re`, `epsilon/D_h`, `A`, `B` безразмерны.
- Область применимости: явная all-regime аппроксимация для внутреннего трубного течения.
- Источник: Churchill, S. W., 1977, "Friction-factor equation spans all fluid-flow regimes", Chemical Engineering, 84(24), 91-92.
- Код: `two_phase_closures.churchill_1977_friction_factor`; `two_phase_closures.friction_factor_from_model`.
- Тесты: `tests/test_pressure_balance.py`.

## FRIC-ZERO-TEST

- Статус: TEST_ONLY.
- Математическая запись:

```math
f_D = 0
```

- Переменные и размерности: `f_D` безразмерен.
- Область применимости: только unit-тесты гидравлического баланса; не является физической моделью.
- Источник: тестовый предел для изоляции гидростатики и ускорительного слагаемого.
- Код: `two_phase_closures.friction_factor_from_model`.
- Тесты: `tests/test_pressure_balance.py`.

## TP-LOCKHART-MARTINELLI

- Статус: PUBLISHED.
- Математическая запись:

```math
X =
\frac{\dot m_l}{\dot m_g}
\sqrt{\frac{f_l v_l}{f_g v_g}}
```

эквивалентно:

```math
X^2=\frac{(dp_f/dz)_l}{(dp_f/dz)_g}
```

- Переменные и размерности: `X` безразмерен; массовые расходы, кг/с; friction factors безразмерны; удельные объемы, м3/кг.
- Область применимости: liquid-reference separated two-phase friction multiplier.
- Источник: Lockhart and Martinelli, 1949; диссертация; `docs/get_co2_academic_reference.md`.
- Код: `published_friction.martinelli_parameter`; compatibility re-export `two_phase_closures.martinelli_parameter`.
- Тесты: `tests/test_two_phase_pressure_drop.py`; `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## TP-CHISHOLM-CONSTANT

- Статус: PUBLISHED.
- Математическая запись: таблица `C` по ламинарному/турбулентному состоянию газа и жидкости при текущем пороге `Re=2320`: `20`, `12`, `10`, `5`.
- Переменные и размерности: газовое и жидкостное `Re` безразмерны; `C` безразмерна.
- Область применимости: текущий множитель Lockhart-Martinelli по жидкостной базе.
- Источник: Chisholm; таблица 2.1 диссертации; `docs/get_co2_academic_reference.md`.
- Код: `published_friction.chisholm_constant`; compatibility re-export `two_phase_closures.chisholm_constant`.
- Тесты: `tests/test_two_phase_pressure_drop.py`; `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## TP-CHISHOLM-MULTIPLIER

- Статус: PUBLISHED.
- Математическая запись:

```math
\Phi_l^2 = 1+\frac{C}{X}+\frac{1}{X^2}
```

- Переменные и размерности: `Phi_l^2`, `C`, `X` безразмерны.
- Область применимости: двухфазный множитель трения для worksheet, homogeneous, Zivi и базового experimental пути.
- Источник: Chisholm; диссертация; `docs/get_co2_academic_reference.md`.
- Код: `published_friction.two_phase_multiplier_liquid_reference`; compatibility re-export `two_phase_closures.two_phase_multiplier_liquid_reference`.
- Тесты: `tests/test_two_phase_pressure_drop.py`; `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE

- Статус: SOURCE_REQUIRED.
- Математическая запись: не реализована в расчёте. Полная формула, определения жидкостного и газового опорных градиентов давления, соглашение по полному массовому потоку и соглашение по коэффициенту трения Darcy/Fanning должны быть переписаны только после проверки полного первоисточника.
- Переменные и размерности: ожидаемые величины для будущей сверки — массовая сухость `x`, безразмерная; градиенты давления, Па/м; массовый поток, кг/(м2 с); плотности, кг/м3; вязкости, Па с; гидравлический диаметр, м; friction factor безразмерен.
- Область применимости: ожидаемая резервная published pressure-drop корреляция для двухфазного течения в трубах; не подключена к `closure_model` и не участвует в solver.
- Источник: Müller-Steinhagen H., Heck K. A simple friction pressure drop correlation for two-phase flow in pipes. Chemical Engineering and Processing, 1986, 20(6), 297-308, DOI `10.1016/0255-2701(86)80008-3`. Доступная предварительная страница статьи подтверждает статью, abstract и наличие двух подгоночных параметров, но не даёт полной формулы и соглашений о величинах.
- Код: `published_friction.muller_steinhagen_heck_1986_pressure_gradient_pa_per_m` — защитная заглушка, которая выбрасывает `SourceRequiredCorrelationError`.
- Тесты: `tests/test_two_phase_pressure_drop.py`; `tests/test_formula_registry.py`.

## TP-FRIEDEL-1979-SOURCE-GATE

- Статус: SOURCE_REQUIRED.
- Математическая запись: не реализована в расчёте. Формула Friedel, коэффициенты, безразмерные комплексы и области применимости должны быть внесены только после проверки полного первичного текста доклада.
- Переменные и размерности: ожидаемые величины для будущей сверки — массовая сухость `x`, безразмерная; градиенты давления, Па/м; массовый поток, кг/(м2 с); плотности, кг/м3; вязкости, Па с; поверхностное натяжение, Н/м; гидравлический диаметр, м; безразмерные комплексы.
- Область применимости: ожидаемая резервная published pressure-drop корреляция для горизонтального и вертикального двухфазного течения; не подключена к `closure_model` и не участвует в solver.
- Источник: Friedel L. Improved friction pressure drop correlations for horizontal and vertical two-phase flow. European Two-Phase Flow Group Meeting, Ispra, Italy, paper E2, 1979. В текущем source-аудите полный первичный текст доклада не доступен.
- Код: `published_friction.friedel_1979_pressure_gradient_pa_per_m` — защитная заглушка, которая выбрасывает `SourceRequiredCorrelationError`.
- Тесты: `tests/test_two_phase_pressure_drop.py`; `tests/test_formula_registry.py`.

## FLOW-MASS-QUALITY

- Статус: PUBLISHED / DEFINITIONAL.
- Математическая запись:

```math
x = \frac{\dot m_g}{\dot m_g+\dot m_l}
```

- Переменные и размерности: массовые расходы пара и жидкости, кг/с; `x` безразмерен.
- Область применимости: локальная и выходная массовая сухость.
- Источник: стандартное определение двухфазного течения; `docs/get_co2_academic_reference.md`.
- Код: `published_void_fraction.mass_quality_from_mass_flows`; compatibility re-export `two_phase_closures.mass_quality_from_mass_flows`; эквивалентные inline-выражения в solver.
- Тесты: `tests/test_void_fraction_models.py`; `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## VOID-GENERIC-SLIP

- Статус: PUBLISHED / DEFINITIONAL.
- Математическая запись:

```math
\alpha =
\left[
1+\frac{1-x}{x}\frac{\rho_g}{\rho_l}S
\right]^{-1}
```

- Переменные и размерности: `alpha`, `x`, `S` безразмерны; плотности, кг/м3.
- Область применимости: преобразование массовой сухости в пустотность для homogeneous, Zivi и selected-slip эвристик; точки `x=0` и `x=1` обрабатываются явно.
- Источник: стандартная slip relation; `docs/get_co2_academic_reference.md`.
- Код: `published_void_fraction.void_fraction_from_quality`; compatibility re-export `two_phase_closures.void_fraction_from_quality`.
- Тесты: `tests/test_void_fraction_models.py`; `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## VOID-WORKSHEET-PHI2L

- Статус: MATHCAD_COMPATIBLE / DISSERTATION.
- Математическая запись:

```math
\beta=(\Phi_l^2)^{-1/3},\qquad \alpha=1-\beta
```

- Переменные и размерности: `alpha`, `beta`, `Phi_l^2` безразмерны.
- Область применимости: только `worksheet_compatible`.
- Источник: `CO2.xmcd`; уравнение 2.78 диссертации; `docs/get_co2_academic_reference.md`.
- Код: `two_phase_closures.worksheet_void_fraction_from_phi2l`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## VOID-HOMOGENEOUS-EQUILIBRIUM

- Статус: PUBLISHED LIMITING MODEL.
- Математическая запись:

```math
S=1
```

далее применяется `VOID-GENERIC-SLIP`.

- Переменные и размерности: `S` безразмерен.
- Область применимости: гомогенный равновесный предельный случай, не режимная карта.
- Источник: стандартный limiting model двухфазного течения; `docs/get_co2_academic_reference.md`.
- Код: `published_void_fraction.homogeneous_equilibrium_slip_ratio`; `two_phase_closures.closure_state_from_model(model="homogeneous_equilibrium")`.
- Тесты: `tests/test_void_fraction_models.py`; `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## VOID-ZIVI-1964

- Статус: PUBLISHED.
- Математическая запись:

```math
S_{\rm Zivi}=\left(\frac{\rho_l}{\rho_g}\right)^{1/3}
```

далее применяется `VOID-GENERIC-SLIP`.

- Переменные и размерности: плотности, кг/м3; `S` безразмерен.
- Область применимости: Zivi slip closure. Исходный вывод относится к идеализированному предельному случаю; применение к текущему горизонтальному испарителю является инженерным переносом корреляции.
- Источник: Zivi, 1964, DOI `10.1115/1.3687113`; `docs/get_co2_academic_reference.md`.
- Код: `published_void_fraction.zivi_1964_slip_ratio`; compatibility wrapper `two_phase_closures.zivi_slip_ratio`; `closure_state_from_model(model="zivi")`.
- Тесты: `tests/test_void_fraction_models.py`; `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## FLOW-PHASE-VELOCITIES

- Статус: DEFINITIONAL.
- Математическая запись:

```math
u_g=\frac{G_gv_g}{\alpha},\qquad
u_l=\frac{G_lv_l}{\beta}
```

- Переменные и размерности: скорости фаз, м/с; массовые потоки, кг/(м2 с); удельные объемы, м3/кг; объемные доли безразмерны.
- Область применимости: локальные скорости фаз и ускорительный перепад.
- Источник: определение связи массового потока, удельного объема и занятой площади сечения; `docs/get_co2_academic_reference.md`.
- Код: `two_phase_closures.compute_phase_velocities`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## FLOW-SLIP-RATIO

- Статус: DEFINITIONAL.
- Математическая запись:

```math
S=\frac{u_g}{u_l}
```

- Переменные и размерности: скорости фаз, м/с; `S` безразмерен.
- Область применимости: диагностика и входы experimental regime-aware эвристик.
- Источник: стандартное определение slip ratio; `docs/get_co2_academic_reference.md`.
- Код: `two_phase_closures.compute_slip_ratio`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## FLOW-MIXTURE-DENSITY

- Статус: DEFINITIONAL.
- Математическая запись:

```math
\rho_m=\beta\rho_l+\alpha\rho_g
=\frac{\beta}{v_l}+\frac{\alpha}{v_g}
```

- Переменные и размерности: плотность смеси, кг/м3; объемные доли безразмерны; плотности, кг/м3; удельные объемы, м3/кг.
- Область применимости: движущий напор, hydrostatic term riser и diagnostics.
- Источник: объемно-осредненная плотность двухфазной смеси; `docs/get_co2_academic_reference.md`.
- Код: `two_phase_closures.compute_mixture_density`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## PRESS-ACCELERATION-MOMENTUM

- Статус: DISSERTATION / ENGINEERING.
- Математическая запись:

```math
\Delta p_a =
\rho_l u_{l,out}^2\beta_{out}
+\rho_g u_{g,out}^2\alpha_{out}
-\rho_{l,in}u_{l,in}^2
```

- Переменные и размерности: перепад давления, Па; плотности, кг/м3; скорости, м/с; объемные доли безразмерны.
- Область применимости: текущая поправка на разность потоков импульса между входом и выходом.
- Источник: диссертационный контекст уравнения импульса; `docs/get_co2_academic_reference.md`.
- Код: `co2_steady_solver.SteadyLoopSolver.one_pass`; `_one_pass_distributed`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## PRESS-WORKSHEET-DRIVING-HEAD

- Статус: DISSERTATION / MATHCAD_COMPATIBLE.
- Математическая запись:

```math
\Delta p_{\rm drive}=gH(\rho_l-\rho_{m,out})
```

и:

```math
H_y=\frac{\Delta p_\Sigma}{g(\rho_l-\rho_{m,out})}
```

- Переменные и размерности: давление, Па; напор, м; плотность, кг/м3; `g`, м/с2.
- Область применимости: lumped hydrostatic driving head в worksheet-compatible расчете.
- Источник: `CO2.xmcd`; диссертационный баланс контура естественной циркуляции; `docs/get_co2_academic_reference.md`.
- Код: `co2_steady_solver.SteadyLoopSolver.one_pass`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_model_regression.py`.

## PRESS-DISTRIBUTED-RISER-GRADIENT

- Статус: ENGINEERING / REQUIRES_AUDIT.
- Математическая запись:

```math
\left(\frac{dp}{dz}\right)_{\rm riser}
=\left(\frac{dp_f}{dz}\right)_{\rm riser}
+\rho_m g
```

и:

```math
\Delta p_{\rm drive}=\sum_j g(\rho_l-\rho_{m,j})\Delta z_j
```

- Переменные и размерности: градиент давления, Па/м; давление, Па; плотность, кг/м3; `g`, м/с2; `dz`, м.
- Область применимости: текущий `distributed_steady` riser. Локальный профиль давления в riser использует полный градиент, а замкнутый баланс контура разносит фрикционный и гидростатический вклады через `PRESS-HYDROSTATIC-SECTION` и `PRESS-LOOP-BALANCE`.
- Источник: текущая Python-реализация; `docs/get_co2_academic_reference.md`, разделы 10 и 18.2.
- Код: `co2_steady_solver.SteadyLoopSolver._one_pass_distributed`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_pressure_balance.py`.

## PRESS-HYDROSTATIC-SECTION

- Статус: PUBLISHED / DEFINITIONAL.
- Математическая запись:

```math
\Delta p_h = \rho g \Delta z
```

- Переменные и размерности: `delta_p_h`, Па; `rho`, кг/м3; `g`, м/с2; `dz`, м.
- Область применимости: signed hydrostatic term по каждому участку контура; подъем положителен, спуск отрицателен.
- Источник: стандартная гидростатика.
- Код: `pressure_balance.hydrostatic_pressure_pa`; `SectionPressureBalance`.
- Тесты: `tests/test_pressure_balance.py`.

## PRESS-LOOP-BALANCE

- Статус: PUBLISHED / DEFINITIONAL.
- Математическая запись:

```math
\sum_i \Delta p_{h,i}
+\sum_i \Delta p_{f,i}
+\sum_i \Delta p_{a,i}
+\sum_i \Delta p_{loc,i}=0
```

и:

```math
\Delta p_{\rm drive}=-\sum_i \Delta p_{h,i}
```

- Переменные и размерности: все `delta_p`, Па.
- Область применимости: замкнутый контур steady-state естественной циркуляции.
- Источник: интегральный баланс давления замкнутого контура.
- Код: `pressure_balance.LoopPressureBalance`; `co2_steady_solver.SteadyLoopSolver._build_pressure_balance`.
- Тесты: `tests/test_pressure_balance.py`; `tests/test_co2_result_fields.py`.

## VOID-ZUBER-FINDLAY-1965-SOURCE-GATE

- Статус: SOURCE_REQUIRED.
- Математическая запись: не реализована как расчетная published-модель. Общая drift-flux структура

```math
\alpha=\frac{j_g}{C_0j+V_{gj}}
```

зафиксирована библиографически, но значения `C0`, `Vgj`, соглашения по средним
величинам и область применимости должны быть сверены по полному первоисточнику
до подключения.
- Переменные и размерности: `alpha` безразмерна; `j_g`, `j`, `V_gj`, м/с; `C0` безразмерен.
- Область применимости: будущая published drift-flux диагностика/замыкание для двухфазного riser; не используется solver в published-режиме.
- Источник: Zuber N., Findlay J. A. Average Volumetric Concentration in Two-Phase Flow Systems. Journal of Heat Transfer, 1965, 87(4), 453-468, DOI `10.1115/1.3689137`; `docs/source_audit_checkpoint_5_6.md`.
- Код: source-gate запись; текущая похожая форма `two_phase_closures.drift_flux_void_fraction` остается `EXP-DRIFT-FLUX-LIKE-VOID`.
- Тесты: `tests/test_formula_registry.py`; `tests/test_regime_maps.py`.

## REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE

- Статус: SOURCE_REQUIRED.
- Математическая запись: опубликованная горизонтальная diabatic flow-boiling map не реализована. Transition criteria, dryout boundaries, dimensionless groups и область применимости должны быть перенесены только после проверки полного первоисточника.
- Переменные и размерности: ожидаемые величины для будущей сверки — массовая сухость, массовый поток, heat flux, диаметр, свойства фаз, поверхностное натяжение и безразмерные комплексы карты.
- Область применимости: будущая published regime map для горизонтального испарителя; текущий `published_regime_map` возвращает `unknown_or_out_of_range` со статусом `source_required`.
- Источник: Wojtan L., Ursenbacher T., Thome J. R. Investigation of flow boiling in horizontal tubes: Part I - A new diabatic two-phase flow pattern map. International Journal of Heat and Mass Transfer, 2005, 48, 2955-2969, DOI `10.1016/j.ijheatmasstransfer.2004.12.012`; `docs/source_audit_checkpoint_5_6.md`.
- Код: `published_regimes.classify_horizontal_evaporator_regime_result` — защитная source-gate классификация без физического режима.
- Тесты: `tests/test_regime_maps.py`; `tests/test_formula_registry.py`; `tests/test_refrigerant_loop_model.py`.

## REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE

- Статус: SOURCE_REQUIRED.
- Математическая запись: опубликованная vertical upflow flow-pattern map не реализована. Transition equations и все коэффициенты должны быть перенесены только после проверки полного первоисточника.
- Переменные и размерности: ожидаемые величины для будущей сверки — superficial velocities, диаметр, плотности, вязкости, поверхностное натяжение и безразмерные переходные критерии.
- Область применимости: будущая published regime map для вертикального подъемного участка; текущий `published_regime_map` возвращает `unknown_or_out_of_range` со статусом `source_required`.
- Источник: Taitel Y., Barnea D., Dukler A. E. Modelling flow pattern transitions for steady upward gas-liquid flow in vertical tubes. AIChE Journal, 1980, 26(3), 345-354, DOI `10.1002/aic.690260304`; `docs/source_audit_checkpoint_5_6.md`.
- Код: `published_regimes.classify_vertical_riser_regime_result` — защитная source-gate классификация без физического режима.
- Тесты: `tests/test_regime_maps.py`; `tests/test_formula_registry.py`.

## EXP-REGIME-AWARE-CLASSIFIERS

- Статус: EXPERIMENTAL / NO PRIMARY SOURCE.
- Математическая запись: фиксированные пороги по `x`, `alpha`, `j_g`, `j_l`, `S` для горизонтального испарителя и по `alpha`, `j_g` для вертикального riser.
- Переменные и размерности: массовая сухость, объемные доли и slip ratio безразмерны; superficial velocities, м/с.
- Область применимости: только diagnostics и switching внутри `experimental_regime_aware`; это не опубликованная режимная карта.
- Источник: текущая проектная эвристика; `docs/get_co2_academic_reference.md`.
- Код: `experimental_regimes.classify_horizontal_evaporator_regime_result`; `classify_vertical_riser_regime_result`; compatibility wrappers in `two_phase_regimes.py`.
- Тесты: `tests/test_baseline_compatibility.py`; `tests/test_co2_result_fields.py`.

## EXP-DRIFT-FLUX-LIKE-VOID

- Статус: EXPERIMENTAL / NO PRIMARY SOURCE.
- Математическая запись:

```math
\alpha=\frac{j_g}{C_0(j_g+j_l)+V_{gj}}
```

```math
V_{gj}=K_d\sqrt{gD_h\max((\rho_l-\rho_g)/\rho_l,0)}
```

В коде используются коэффициенты `C0=1.08`, `Kd=0.30` для горизонтального
потока и `C0=1.18`, `Kd=0.50` для вертикального потока.

- Переменные и размерности: пустотность безразмерна; superficial velocities, м/с; диаметр, м; плотности, кг/м3.
- Область применимости: ветви `bubble_onset` и `bubbly` внутри `experimental_regime_aware`. Форма похожа на drift-flux, но коэффициенты не имеют первоисточника.
- Источник: текущая проектная эвристика; Zuber-Findlay поддерживает только общую структуру drift-flux, а не эти коэффициенты.
- Код: `two_phase_closures.drift_flux_void_fraction`.
- Тесты: `tests/test_co2_result_fields.py`; `tests/test_baseline_compatibility.py`.

## EXP-ANNULAR-CORE-VOID

- Статус: EXPERIMENTAL / NO PRIMARY SOURCE.
- Математическая запись:

```math
S_{\rm ann}=\max(1.05,k_{\rm ann}S_{\rm Zivi})
```

В коде используются `k_ann=0.60` для горизонтального потока и `k_ann=0.72`
для вертикального потока.

- Переменные и размерности: slip ratios безразмерны; плотности фаз входят через `S_Zivi`.
- Область применимости: ветви `annular_transition`, `annular`, `annular_mist` внутри `experimental_regime_aware`.
- Источник: текущая проектная эвристика; первоисточник для коэффициентов не зафиксирован.
- Код: `two_phase_closures.annular_core_void_fraction`.
- Тесты: `tests/test_co2_result_fields.py`; `tests/test_baseline_compatibility.py`.

## EXP-REGIME-FRICTION-GRADIENTS

- Статус: EXPERIMENTAL / NO PRIMARY SOURCE.
- Математическая запись: режимно выбранные линейные комбинации и максимумы фазовых градиентов для `stratified_separated`, `separated_shear`, `separated_shear_vertical`, `annular_film`, `annular_film_vertical`.
- Переменные и размерности: фазовые градиенты давления, Па/м; объемные доли, веса и ограничения безразмерны.
- Область применимости: friction response только внутри `experimental_regime_aware`.
- Источник: текущая проектная эвристика; веса, ограничения и fallback multipliers не имеют первоисточника.
- Код: `two_phase_closures._resolve_two_phase_friction_response`.
- Тесты: `tests/test_co2_result_fields.py`; `tests/test_baseline_compatibility.py`.

## SCENARIO-MATRIX-STATUS

- Статус: REGRESSION_DIAGNOSTIC.
- Математическая запись: новых физических формул нет. Для рабочих сценариев используется существующая невязка текущего steady solver:

```math
Hy(f)-H=0
```

с укороченным root scan, после чего результат классифицируется дискретным статусом.
- Переменные и размерности: `H`, м; `qtr`, Вт/м; `Li`, м; `tcon`, град C; `fluid`, строка; `property_backend`, строка; `status` и `failure_class`, перечисления.
- Область применимости: smoke-регрессия выбранных CO2/NH3 сценариев Checkpoint 10. Не является published-корреляцией, режимной картой, qcrit-алгоритмом или экспериментальной валидацией.
- Источник: проектное требование Checkpoint 10; `docs/get_co2_academic_reference.md`; текущая система уравнений `SteadyLoopSolver`.
- Код: `scenario_matrix.run_scenario_case`; `scenario_matrix.run_scenario_matrix`; `scenario_matrix.default_scenario_cases`.
- Тесты: `tests/test_scenario_matrix.py`.

## Правила сопровождения

- Новые модели со статусом `published`, `validated`, `academic` или `physical` нельзя подключать без записи в этом реестре.
- Эвристики без первоисточника должны иметь статус `EXPERIMENTAL / NO PRIMARY SOURCE`.
- Сценарные и регрессионные проверки допускаются со статусом `REGRESSION_DIAGNOSTIC`, если они не добавляют формулу и не объявляются физической моделью.
- Published closure models не должны ссылаться на записи `EXP-*`; это проверяется `tests/test_formula_registry.py`.
- Вызовы свойств вне диапазона backend должны давать понятную ошибку, если экстраполяция не включена явно.
- Текущая blended-модель трения не является Colebrook-White и сохранена как `mathcad_compat`. Для аудита и опубликованных альтернатив доступны `colebrook_white`, `churchill_explicit`, `laminar_only` и `zero_friction`.
- Поля результата `model_source_status` и `source_gate_reasons` не заменяют этот реестр; они агрегируют активные `SOURCE_REQUIRED` и `EXPERIMENTAL / NO PRIMARY SOURCE` ограничения выбранной цепочки расчета.
- `published_regimes.py` содержит только защитные source-gate заготовки, возвращающие `unknown_or_out_of_range` / `source_required`; опубликованные горизонтальная и вертикальная режимные карты в Checkpoint 6 не реализованы.
- Müller-Steinhagen-Heck, Friedel, Zuber-Findlay, Taitel-Barnea-Dukler и Wojtan-Ursenbacher-Thome не подключаются как расчетные `published`-модели, пока точные формулы и области применимости не сверены с полным первоисточником.
