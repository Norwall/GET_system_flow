# План физически строгой доработки модели ГЕТ для CO₂ и NH₃

## 1. Цель

Доработать текущий Python-код из Mathcad-совместимого инженерного расчёта CO₂ в физически прослеживаемую модель естественной циркуляции хладагента для двух рабочих тел:

- CO₂ / R744;
- NH₃ / R717 / ammonia.

Главное правило реализации: каждая формула, коэффициент, таблица свойств, режимная граница и эмпирическая поправка должны иметь источник. Допустимые источники:

- исходный `CO2.xmcd`;
- диссертация А. А. Ишкова;
- опубликованная статья или справочник;
- NIST REFPROP / NIST Chemistry WebBook;
- CoolProp с указанной reference-моделью;
- явно помеченный экспериментальный режим `experimental_*`.

Эвристические элементы без источника нельзя использовать в режимах, которые называются `published`, `validated`, `academic` или `physical`.

## 2. Текущая отправная точка

В проекте уже есть:

- `co2_properties.py` — табличные свойства насыщенного CO₂ из Mathcad/справочных таблиц;
- `co2_steady_solver.py` — стационарный solver;
- `co2_geometry.py` — базовая геометрия и заготовки участков;
- `two_phase_closures.py` — трение, Lockhart–Martinelli, Chisholm, пустотность, Zivi и эвристические режимные замыкания;
- `two_phase_regimes.py` — текущие эвристические классификаторы режимов;
- `get_co2_model.py` — совместимый фасад `CO2MathcadModel`;
- `get_designer_geometry.py` и `get_designer_api.py` — интерфейс сценариев/designer;
- `docs/get_co2_academic_reference.md` — академическая справка и аудит ограничений.

Главные физические слабые места текущей реализации:

- неоднозначность `log` Mathcad против `np.log` Python в формуле шероховатого трения;
- риск двойного учёта гидростатики в распределённом расчёте;
- эвристический `regime_aware`;
- свойства CO₂ из ограниченных таблиц с `CubicSpline` и возможной экстраполяцией;
- designer хранит сегменты, диаметры и шероховатости, но solver фактически использует упрощённую встроенную геометрию;
- нет ветки NH₃;
- нет отдельного физического алгоритма критических нагрузок.

## 3. Целевая архитектура

Итоговая архитектура должна сохранить старый фасад:

```python
CO2MathcadModel().run(
    H,
    qtr,
    Li,
    tcon,
    mode="worksheet_compatible",
    closure_model="worksheet_compatible",
)
```

И добавить новый универсальный фасад:

```python
RefrigerantLoopModel(
    fluid="CO2",
    property_backend="coolprop",
    geometry=geometry,
).run(...)
```

```python
RefrigerantLoopModel(
    fluid="NH3",
    property_backend="coolprop",
    geometry=geometry,
).run(...)
```

Целевые модули:

- `refrigerant_properties.py` — общий интерфейс свойств CO₂/NH₃;
- `pressure_balance.py` — единый баланс давления по контуру;
- `published_friction.py` — опубликованные однофазные и двухфазные модели трения;
- `published_void_fraction.py` — опубликованные модели пустотности и скольжения;
- `published_regimes.py` — опубликованные режимные карты;
- `experimental_regimes.py` — текущие эвристики, явно вынесенные в experimental-слой;
- `boiling_heat_transfer.py` — диагностика кипения, heat-transfer и dryout;
- `critical_loads.py` — отдельный расчёт нижних/верхних критических нагрузок;
- `docs/formula_registry.md` — реестр формул, источников, областей применимости и тестов.

## 4. Checkpoint 0 — фиксация baseline

Цель: защитить текущую Mathcad-совместимость перед изменениями физики.

### Задачи

- [x] Запустить все текущие тесты.
- [x] Зафиксировать baseline для:
  - `worksheet_compatible`;
  - `distributed_steady`;
  - `homogeneous_equilibrium`;
  - `zivi`;
  - текущего `regime_aware`.
- [x] Переименовать текущий эвристический `regime_aware` в `experimental_regime_aware`.
- [x] На переходный период оставить alias `regime_aware -> experimental_regime_aware`.
- [x] Добавить в результат поле `model_scientific_status`:
  - `mathcad_compatible`;
  - `published`;
  - `experimental`;
  - `mixed` зарезервирован для следующих комбинированных режимов.
- [x] Проверить и документировать расхождение Mathcad `log` и Python `np.log`.
- [x] Добавить тест, который явно показывает отличие `ln` и `log10` на контрольной сетке Reynolds/roughness.

### Тесты

- [x] `tests/test_baseline_compatibility.py`
  - старые baseline-значения не изменились в совместимом режиме;
  - `CO2MathcadModel.run(...)` принимает старые параметры;
  - старый ключ `regime_aware` работает как alias.
- [x] `tests/test_mathcad_log_audit.py`
  - `mathcad_rough_log10` и текущий `numpy_ln` дают разные значения;
  - формула трения явно сообщает, какой логарифм использован.

### Критерий готовности

Старый пользовательский API работает, текущие тесты проходят, эвристический режим больше не позиционируется как опубликованный.

## 5. Checkpoint 1 — общий интерфейс свойств хладагента

Цель: заменить жёсткую привязку solver к `CO2SaturationProperties` на общий интерфейс свойств насыщенного хладагента.

### Задачи

- [ ] Создать `refrigerant_properties.py`.
- [ ] Ввести `SaturationState`.
- [ ] Ввести protocol/interface `RefrigerantSaturationProperties`.
- [ ] Реализовать backends:
  - `MathcadCO2SaturationProperties`;
  - `CoolPropSaturationProperties(fluid="CO2")`;
  - `CoolPropSaturationProperties(fluid="NH3")`;
  - `RefpropSaturationProperties` как optional adapter.
- [ ] Добавить aliases рабочих тел:
  - `CO2`, `R744`, `CarbonDioxide`;
  - `NH3`, `R717`, `Ammonia`.
- [ ] Добавить запрет неявной экстраполяции:
  - `allow_property_extrapolation=False` по умолчанию;
  - выход за диапазон должен давать понятную ошибку.
- [ ] В результат добавить:
  - `fluid`;
  - `property_backend`;
  - `property_source`;
  - `property_warning`;
  - `near_critical_warning`.

### Целевая структура `SaturationState`

```python
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
```

### Источники свойств

- NIST REFPROP: <https://www.nist.gov/srd/refprop>
- NIST Chemistry WebBook SRD 69: <https://webbook.nist.gov/chemistry/fluid/>
- CoolProp High-Level API: <https://coolprop.org/coolprop/HighLevelAPI.html>
- CoolProp CO₂: <https://coolprop.org/fluid_properties/fluids/CarbonDioxide.html>
- CoolProp NH₃: <https://coolprop.org/fluid_properties/fluids/Ammonia.html>
- Span, Wagner — CO₂ equation of state: <https://doi.org/10.1063/1.555991>

Для NH₃ первичным практическим источником на первом этапе принять CoolProp/REFPROP. Конкретную reference-EOS для ammonia взять из документации CoolProp и/или REFPROP и внести в `docs/formula_registry.md` до реализации численных baseline-тестов.

### Тесты

- [ ] `tests/test_refrigerant_properties.py`
  - CO₂: проверка насыщенного состояния на сетке температур;
  - NH₃: проверка насыщенного состояния на сетке температур;
  - `latent_heat_j_kg == h_g_j_kg - h_l_j_kg`;
  - `rho_l > rho_g`;
  - `mu_l > 0`, `mu_g > 0`, `cp_l > 0`, `cp_g > 0`;
  - near-critical область даёт warning/error;
  - неявная экстраполяция запрещена.

### Критерий готовности

CO₂ и NH₃ возвращают насыщенные свойства через один интерфейс, а solver не зависит от конкретного класса CO₂.

## 6. Checkpoint 2 — академический реестр формул

Цель: формально связать код, формулы, источники и тесты.

### Задачи

- [ ] Создать `docs/formula_registry.md`.
- [ ] Для каждой формулы указать:
  - ID;
  - математическую запись;
  - переменные и размерности;
  - область применимости;
  - источник;
  - функцию/класс в коде;
  - тесты.
- [ ] Запретить добавление новых published-моделей без записи в реестре.
- [ ] Для эвристик указывать статус `EXPERIMENTAL / NO PRIMARY SOURCE`.

### Минимальный набор формул

Darcy–Weisbach:

```math
\frac{\Delta p_f}{L}=f_D\frac{G^2}{2\rho D_h}
```

Reynolds:

```math
Re=\frac{GD_h}{\mu}
```

Laminar Darcy friction:

```math
f_D=\frac{64}{Re}
```

Colebrook–White:

```math
\frac{1}{\sqrt{f_D}}=
-2\log_{10}\left(
\frac{\varepsilon/D_h}{3.7}
+\frac{2.51}{Re\sqrt{f_D}}
\right)
```

Lockhart–Martinelli:

```math
X^2=\frac{(dp/dz)_l}{(dp/dz)_g}
```

Chisholm:

```math
\Phi_l^2=1+\frac{C}{X}+\frac{1}{X^2}
```

Homogeneous void fraction:

```math
\alpha=
\left[
1+\frac{1-x}{x}\frac{\rho_g}{\rho_l}
\right]^{-1}
```

Zivi slip:

```math
S=\left(\frac{\rho_l}{\rho_g}\right)^{1/3}
```

Zivi void fraction:

```math
\alpha=
\left[
1+\frac{1-x}{x}
\left(\frac{\rho_g}{\rho_l}\right)^{2/3}
\right]^{-1}
```

Zuber–Findlay drift-flux structure:

```math
\alpha=\frac{j_g}{C_0j+V_{gj}}
```

Energy balance for vapor generation:

```math
\dot m_g(z)=\frac{Q(z)}{h_g-h_l}
```

Hydrostatic pressure contribution:

```math
dp_h=\rho g\,dz
```

Closed-loop pressure balance:

```math
\oint dp_h+\oint dp_f+\oint dp_{loc}+\oint dp_{acc}=0
```

### Источники

- Lockhart, Martinelli, 1949.
- Chisholm, 1973: <https://doi.org/10.1016/0017-9310(73)90063-X>
- Zivi, 1964: <https://doi.org/10.1115/1.3687113>
- Zuber, Findlay, 1965: <https://doi.org/10.1115/1.3689137>
- Taitel, Barnea, Dukler, 1980: <https://doi.org/10.1002/aic.690260304>
- Wojtan, Ursenbacher, Thome, 2005: <https://doi.org/10.1016/j.ijheatmasstransfer.2004.12.012>
- Müller-Steinhagen, Heck, 1986: <https://doi.org/10.1016/0255-2701(86)80008-3>
- Мельников и др., 2017: <https://doi.org/10.21782/KZ1560-7496-2017-3(41-48)>

### Критерий готовности

У каждой физической формулы в коде есть источник, область применимости и тест.

## 7. Checkpoint 3 — строгий гидравлический баланс

Цель: убрать неоднозначность баланса давления и исключить двойной учёт гидростатики.

### Задачи

- [ ] Создать `pressure_balance.py`.
- [ ] Ввести `PressureTerm`.
- [ ] Ввести `SectionPressureBalance`.
- [ ] Для каждого участка отдельно считать:
  - `delta_p_hydrostatic_pa`;
  - `delta_p_friction_pa`;
  - `delta_p_acceleration_pa`;
  - `delta_p_local_pa`;
  - `delta_p_total_pa`.
- [ ] Для замкнутого контура считать:
  - сумму гидростатики;
  - сумму трения;
  - сумму ускорительных потерь;
  - сумму местных сопротивлений;
  - итоговую невязку.
- [ ] Добавить `friction_model`:
  - `mathcad_compat`;
  - `colebrook_white`;
  - `churchill_explicit`;
  - `laminar_only`;
  - `zero_friction` для тестов.
- [ ] Сделать `log10` явным в опубликованных формулах трения.
- [ ] Оставить Mathcad-вариант как отдельный compatibility mode.

### Сценарии, которые должны быть обработаны

- чистая однофазная жидкость;
- двухфазный riser;
- горизонтальный испаритель с кипением;
- нулевое трение;
- нулевая высота;
- отрицательная высота — validation error;
- near-critical свойства CO₂ — warning/error;
- отсутствие корня по `f`;
- несколько корней по `f`.

### Тесты

- [ ] `tests/test_pressure_balance.py`
  - `zero_friction` даёт чисто гидростатический предел;
  - сумма pressure terms равна total;
  - гидростатика не учитывается дважды;
  - знак hydrostatic term зависит от направления `dz`;
  - при `H=0` нет движущего гидростатического напора.

### Критерий готовности

В результатах можно увидеть полный баланс давления по участкам, а не только итоговый `deltaP`.

## 8. Checkpoint 4 — реальная сегментная геометрия

Цель: сделать designer настоящим источником расчётной геометрии.

### Задачи

- [ ] Расширить `LoopGeometry` до списка `FlowSection`.
- [ ] Каждый `FlowSection` должен иметь:
  - `id`;
  - `kind`;
  - `orientation`;
  - `length_m`;
  - `dz_m`;
  - `hydraulic_diameter_m`;
  - `roughness_m`;
  - `relative_roughness`;
  - `area_m2`;
  - `heat_mode`.
- [ ] Передавать из designer в solver:
  - реальные длины;
  - реальные высоты;
  - диаметры;
  - шероховатости;
  - тип участка.
- [ ] Сохранить `default_mathcad_geometry`.
- [ ] Добавить `geometry_source`:
  - `mathcad_default`;
  - `designer`;
  - `manual_sections`.

### Тесты

- [ ] `tests/test_segmented_geometry.py`
  - изменение диаметра меняет потери давления;
  - изменение шероховатости меняет потери давления;
  - изменение высоты riser меняет hydrostatic contribution;
  - designer JSON round-trip сохраняет геометрию;
  - схема без evaporator даёт validation error;
  - схема без положительного напора даёт validation error.

### Критерий готовности

Если пользователь меняет диаметр или шероховатость в designer, расчётный результат меняется физически ожидаемым образом.

## 9. Checkpoint 5 — опубликованные двухфазные замыкания

Цель: отделить published-слой от эвристик.

### Задачи

- [ ] Разделить closure models на:
  - `mathcad_compatible`;
  - `published`;
  - `experimental`.
- [ ] Оставить текущие эвристики только в `experimental_regime_aware`.
- [ ] Реализовать или формально подтвердить:
  - `homogeneous_equilibrium`;
  - `zivi_1964`;
  - `lockhart_martinelli_chisholm`;
  - `muller_steinhagen_heck_1986`;
  - `friedel_1979`, если первоисточник доступен и формула точно воспроизведена.
- [ ] Для вертикального riser добавить published drift-flux-ветку на основе Zuber–Findlay.
- [ ] Все коэффициенты `C0`, `Vgj`, annular/slug/churn брать только из источников.

### Тесты

- [ ] `tests/test_void_fraction_models.py`
  - `0 <= alpha <= 1`;
  - homogeneous-пределы при `x -> 0` и `x -> 1`;
  - Zivi даёт `S > 1` при `rho_l > rho_g`;
  - mixture density лежит между `rho_g` и `rho_l`.
- [ ] `tests/test_two_phase_pressure_drop.py`
  - Lockhart–Martinelli/Chisholm возвращает положительный multiplier;
  - pressure gradient положителен при положительном расходе;
  - нулевой vapor mass flow обрабатывается без NaN/Inf.

### Критерий готовности

`published_two_phase` не содержит коэффициентов без источника.

## 10. Checkpoint 6 — опубликованные режимные карты

Цель: заменить фиксированные эвристические пороги на published-классификаторы.

### Задачи

- [ ] Создать `published_regimes.py`.
- [ ] Создать `experimental_regimes.py`.
- [ ] Перенести текущие эвристики в `experimental_regimes.py`.
- [ ] Для горизонтального испарителя реализовать карту Wojtan–Ursenbacher–Thome.
- [ ] Для вертикального подъёмного участка реализовать Taitel–Barnea–Dukler.
- [ ] В каждом локальном control volume сохранять:
  - regime name;
  - source;
  - transition criteria;
  - confidence/status.
- [ ] В результатах выводить summary режимов по длине участка.

### Режимы, которые должны поддерживаться

- `single_liquid`;
- `bubble_onset`;
- `bubbly`;
- `slug`;
- `churn`;
- `stratified`;
- `stratified_wavy`;
- `intermittent`;
- `annular`;
- `mist`;
- `dryout`;
- `single_vapor`;
- `unknown_or_out_of_range`.

### Тесты

- [ ] `tests/test_regime_maps.py`
  - старые пороги доступны только через `experimental_*`;
  - published classifier возвращает source-tagged regime;
  - out-of-range сценарий не маскируется под физический режим;
  - summary по длине участка суммируется к 100%.

### Критерий готовности

`published_regime_model` не использует текущие фиксированные пороги пустотности как физические границы.

## 11. Checkpoint 7 — кипение, теплообмен и dryout

Цель: отделить гидродинамическую сходимость от тепловых ограничений кипения.

### Задачи

- [ ] Создать `boiling_heat_transfer.py`.
- [ ] Поддержать два уровня постановки:
  - prescribed heat input — текущая задача;
  - wall/soil coupled heat transfer — следующая физическая задача.
- [ ] Добавить диагностический расчёт saturated flow boiling heat transfer.
- [ ] Выбрать опубликованную корреляцию после сверки первоисточника:
  - Kandlikar;
  - Shah;
  - Gungor–Winterton.
- [ ] Не смешивать nucleate boiling и flow boiling без явной постановки wall superheat.
- [ ] Добавить dryout/critical heat flux diagnostics отдельно от hydrodynamic qcrit.
- [ ] В результатах разделить:
  - `hydrodynamic_limit`;
  - `boiling_heat_transfer_limit`;
  - `dryout_limit`;
  - `property_limit`;
  - `numerical_failure`.

### Тесты

- [ ] `tests/test_boiling_diagnostics.py`
  - prescribed heat input не требует wall temperature;
  - wall heat-transfer mode требует wall/soil boundary;
  - dryout diagnostic не подменяет solver convergence;
  - near-critical CO₂ не считается без warning/error.

### Критерий готовности

Критическая нагрузка не выводится только из факта несходимости численного solver.

## 12. Checkpoint 8 — ветка NH₃ / R717

Цель: добавить аммиак как полноценное рабочее тело без копирования CO₂-специфичных коэффициентов.

### Задачи

- [ ] Добавить aliases:
  - `NH3`;
  - `Ammonia`;
  - `R717`.
- [ ] Подключить NH₃ через общий `RefrigerantSaturationProperties`.
- [ ] Использовать те же уравнения баланса массы, энергии и давления.
- [ ] Не переносить CO₂-калибровки на NH₃ без источника.
- [ ] Добавить reference CSV:
  - `data/reference_properties/co2_saturation_coolprop.csv`;
  - `data/reference_properties/nh3_saturation_coolprop.csv`.
- [ ] Добавить NH₃ scenarios:
  - номинальный режим;
  - малый `qtr`;
  - высокий `qtr`;
  - низкая температура насыщения;
  - около верхней границы допустимого диапазона.
- [ ] В результатах явно указывать:
  - `fluid`;
  - `fluid_cas`;
  - `refrigerant_name`;
  - `property_backend`.

### Тесты

- [ ] `tests/test_nh3_properties.py`
  - NH₃ насыщенная жидкость плотнее пара;
  - latent heat положительна;
  - давление насыщения растёт с температурой;
  - вязкости положительны.
- [ ] `tests/test_nh3_loop_solver.py`
  - один и тот же geometry object считается для CO₂ и NH₃;
  - результаты CO₂ и NH₃ различаются;
  - solver не использует `CO2SaturationProperties` напрямую.

### Критерий готовности

Один и тот же solver считает CO₂ и NH₃ через общий интерфейс свойств.

## 13. Checkpoint 9 — критические нагрузки

Цель: реализовать физический `qcrit`, а не карту численной сходимости.

### Задачи

- [ ] Создать `critical_loads.py`.
- [ ] Реализовать поиск:
  - нижней критической нагрузки;
  - верхней критической нагрузки;
  - special limit `f -> 0`, если он требуется постановкой диссертации.
- [ ] Разделить причины отказа:
  - `no_boiling`;
  - `no_root`;
  - `multiple_roots`;
  - `f_to_zero_limit`;
  - `dryout_limit`;
  - `property_out_of_range`;
  - `near_critical_region`;
  - `numerical_failure`.
- [ ] Добавить continuation по:
  - `qtr`;
  - `H`;
  - `Li`;
  - `tcon`;
  - `fluid`.
- [ ] Не использовать “максимальную сошедшуюся точку сетки” как физический `qcrit`.

### Тесты

- [ ] `tests/test_qcrit_solver.py`
  - low heat load;
  - nominal heat load;
  - high heat load;
  - no boiling;
  - no root;
  - multiple roots;
  - `f -> 0`;
  - near-critical rejection;
  - out-of-range rejection.

### Критерий готовности

Отчёт по `qcrit` объясняет физическую причину предела, а не только статус сходимости.

## 14. Checkpoint 10 — сценарная матрица

Цель: проверять модель не только на одной точке, а на наборе физических сценариев.

### Обязательные сценарии

- [ ] CO₂, `tcon = -20, -10, 0, 10, 20 °C`.
- [ ] NH₃, аналогичная температурная сетка в допустимом диапазоне backend.
- [ ] `qtr` от малых нагрузок до верхнего предела.
- [ ] `H`: малый, номинальный, большой.
- [ ] `Li`: короткий, номинальный, длинный испаритель.
- [ ] Диаметр: малый, номинальный, большой.
- [ ] Шероховатость: гладкая, номинальная, грубая труба.
- [ ] Горизонтальный испаритель без riser — должен корректно показать отсутствие движущего напора.
- [ ] Высокий riser.
- [ ] Сценарий около критической точки CO₂ — warning/error.
- [ ] Нулевые/отрицательные входы — validation error.
- [ ] Недоступный CoolProp/REFPROP — понятный fallback или ошибка.

### Тесты

- [ ] `tests/test_scenario_matrix.py`
  - все сценарии возвращают структурированный статус;
  - невалидные сценарии не возвращают псевдофизический результат;
  - failure reasons входят в фиксированный enum.

### Критерий готовности

Матрица сценариев показывает не только числа, но и физический/численный статус каждой точки.

## 15. Публичные API и результат

### Новые входы solver

- `fluid`;
- `property_backend`;
- `friction_model`;
- `regime_model`;
- `two_phase_closure`;
- `allow_property_extrapolation`;
- `geometry_source`;
- `heat_transfer_model`;
- `qcrit_model`.

### Новые поля результата

- `fluid`;
- `property_backend`;
- `property_source`;
- `formula_registry_version`;
- `model_scientific_status`;
- `pressure_balance_terms`;
- `section_results`;
- `dominant_regime_by_section`;
- `qcrit_status`;
- `failure_class`;
- `warnings`.

### Совместимость

Старые поля не удалять сразу. Для неоднозначных старых имён добавить физически понятные aliases:

- `phiG1_true` оставить как compatibility alias;
- добавить `outlet_no_slip_gas_volume_fraction`;
- добавить `outlet_closure_void_fraction`;
- добавить `outlet_slip_ratio`;
- добавить `outlet_mass_quality`.

## 16. Общая тестовая структура

Минимальный набор новых тестовых файлов:

- `tests/test_baseline_compatibility.py`;
- `tests/test_mathcad_log_audit.py`;
- `tests/test_refrigerant_properties.py`;
- `tests/test_nh3_properties.py`;
- `tests/test_friction_models.py`;
- `tests/test_void_fraction_models.py`;
- `tests/test_two_phase_pressure_drop.py`;
- `tests/test_pressure_balance.py`;
- `tests/test_segmented_geometry.py`;
- `tests/test_regime_maps.py`;
- `tests/test_boiling_diagnostics.py`;
- `tests/test_qcrit_solver.py`;
- `tests/test_scenario_matrix.py`;
- `tests/test_refrigerant_loop_model.py`.

Каждый checkpoint считается завершённым только после:

- unit tests;
- integration tests;
- обновления `docs/formula_registry.md`;
- обновления академической справки или changelog;
- проверки, что старый compatibility mode не сломан.

## 17. Порядок реализации

Рекомендуемый порядок:

1. Baseline и audit старых режимов.
2. Общий интерфейс свойств CO₂/NH₃.
3. `docs/formula_registry.md`.
4. Явный гидравлический баланс.
5. Сегментная геометрия.
6. Published двухфазные замыкания.
7. Published режимные карты.
8. NH₃ ветка на общем solver.
9. Диагностика кипения и dryout.
10. Отдельный `qcrit`.
11. Полная сценарная матрица.
12. Обновление отчётов и designer UI.

## 18. Критерии завершения всей доработки

- [ ] CO₂ Mathcad-compatible ветка воспроизводит старые baseline-тесты.
- [ ] CO₂ published ветка не содержит эвристических коэффициентов без источника.
- [ ] NH₃ ветка работает через тот же solver и тот же интерфейс свойств.
- [ ] Свойства насыщенной жидкости и пара берутся из CoolProp/REFPROP/NIST или явно помеченного Mathcad baseline.
- [ ] Все формулы задокументированы в `docs/formula_registry.md`.
- [ ] Все режимные карты имеют ссылки на публикации.
- [ ] Solver различает физический отказ, численную несходимость, dryout и выход за диапазон свойств.
- [ ] Designer реально передаёт геометрию в solver.
- [ ] Тесты покрывают CO₂, NH₃, свойства, трение, пустотность, гидростатику, режимы, `qcrit` и ошибочные входы.
