# Реестр формул и свойств

Версия реестра: `checkpoint-5-source-strict`.

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
| `BAL-VAPOR-GENERATION` | DISSERTATION | `SteadyLoopSolver.one_pass` |
| `BAL-PREBOILING-FRACTION` | DISSERTATION / MATHCAD_COMPATIBLE | `SteadyLoopSolver.one_pass` |
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
| `EXP-REGIME-AWARE-CLASSIFIERS` | EXPERIMENTAL / NO PRIMARY SOURCE | `experimental_regimes.py` |
| `EXP-DRIFT-FLUX-LIKE-VOID` | EXPERIMENTAL / NO PRIMARY SOURCE | `drift_flux_void_fraction` |
| `EXP-ANNULAR-CORE-VOID` | EXPERIMENTAL / NO PRIMARY SOURCE | `annular_core_void_fraction` |
| `EXP-REGIME-FRICTION-GRADIENTS` | EXPERIMENTAL / NO PRIMARY SOURCE | `_resolve_two_phase_friction_response` |

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
- Тесты: `tests/test_refrigerant_properties.py`.

## PROP-COOLPROP-NH3-HEOS

- Статус: PUBLISHED.
- Математическая запись: вызовы CoolProp HEOS через `PropsSI` на линии насыщения.
- Переменные и размерности: температура насыщения, K или град C; давление, Па; качество `Q=0` для жидкости и `Q=1` для пара; остальные свойства в SI.
- Область применимости: aliases NH3/R717/Ammonia в диапазоне насыщения CoolProp ниже критической точки.
- Источник: CoolProp HEOS; Gao, Wu, Bell, Lemmon, ammonia EOS, J. Phys. Chem. Ref. Data, 2020.
- Код: `refrigerant_properties.CoolPropSaturationProperties(fluid="NH3")`.
- Тесты: `tests/test_refrigerant_properties.py`.

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

## Правила сопровождения

- Новые модели со статусом `published`, `validated`, `academic` или `physical` нельзя подключать без записи в этом реестре.
- Эвристики без первоисточника должны иметь статус `EXPERIMENTAL / NO PRIMARY SOURCE`.
- Published closure models не должны ссылаться на записи `EXP-*`; это проверяется `tests/test_formula_registry.py`.
- Вызовы свойств вне диапазона backend должны давать понятную ошибку, если экстраполяция не включена явно.
- Текущая blended-модель трения не является Colebrook-White и сохранена как `mathcad_compat`. Для аудита и опубликованных альтернатив доступны `colebrook_white`, `churchill_explicit`, `laminar_only` и `zero_friction`.
- `published_regimes.py` содержит только guarded-заготовки, возвращающие `unknown_or_out_of_range` / `not_implemented`; опубликованные горизонтальная и вертикальная режимные карты в Checkpoint 6 не реализованы.
- Müller-Steinhagen-Heck, Friedel, Zuber-Findlay, Taitel-Barnea-Dukler и Wojtan-Ursenbacher-Thome не подключаются как расчетные `published`-модели, пока точные формулы и области применимости не сверены с полным первоисточником.
