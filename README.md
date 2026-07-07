# Python-порт MathCAD-модели CO2

Проект содержит инженерную 1D steady-state модель естественной циркуляции CO2,
перенесенную из MathCAD workbook `CO2.xmcd`. Модель рассчитывает рабочий режим
замкнутого контура с горизонтальным испарителем: подвод тепла испаряет часть CO2,
двухфазная смесь становится легче жидкостного столба, а возникающий напор
расходуется на трение и ускорительные потери.

Это не CFD-модель и не динамический расчет устойчивости. Основной сценарий -
стационарный расчет рабочей точки и сравнение вариантов двухфазных closure-моделей.

## Что считает модель

Главные входы:

- `H` - доступный геометрический циркуляционный напор, м;
- `qtr` - линейная тепловая нагрузка на испаритель, Вт/м;
- `Li` - длина испарителя, м;
- `tcon` - температура конденсации, градусы C.

Главный результат - самосогласованный параметр циркуляции `f`, при котором
требуемый напор `Hy` совпадает с заданным `H`. Дополнительно возвращаются расходы
фаз, массовая сухость, газосодержание, потери давления, температуры и диагностические
поля решателя.

## Установка зависимостей

Рекомендуемый вариант:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

Если editable install не нужен, достаточно установить основные библиотеки:

```powershell
python -m pip install numpy scipy pandas matplotlib pytest
```

## Быстрый расчет

```powershell
python -c "from get_co2_model import CO2MathcadModel; m = CO2MathcadModel(); print(m.run(2.5, 76.68, 200.0, 0.0))"
```

В коде:

```python
from get_co2_model import CO2MathcadModel

model = CO2MathcadModel()
result = model.run(H=2.5, qtr=76.68, Li=200.0, tcon=0.0)
print(result["converged"], result["fff"], result["Hy_m"])
```

Для структурированного результата используйте `run_result(...)`. Для распределенного
профиля испарителя и райзера задайте `mode="distributed_steady"`. Модель трения
выбирается параметром `friction_model`, например:

```python
result = model.run(
    H=2.5,
    qtr=76.68,
    Li=200.0,
    tcon=0.0,
    mode="distributed_steady",
    friction_model="colebrook_white",
)
```

Начало кипения по умолчанию остаётся MathCAD-совместимым:
`boiling_onset_model="mathcad_baseline"`. Для явной диссертационной поправки
по перегреву можно включить opt-in ветку:

```python
result = model.run(
    H=2.5,
    qtr=76.68,
    Li=200.0,
    tcon=0.0,
    boiling_onset_model="ishkov_superheat",
    onset_superheat_k=1.0,
)
print(result["preboiling_status"], result["boiling_onset_source"])
```

Для расчетов через общий интерфейс свойств CO2/NH3 используйте универсальный
фасад:

```python
from refrigerant_loop_model import RefrigerantLoopModel

model = RefrigerantLoopModel(fluid="NH3", property_backend="coolprop")
result = model.run(H=2.5, qtr=76.68, Li=200.0, tcon=0.0)
print(result["fluid"], result["property_backend"], result["converged"])
```

## Статус физической доработки

В текущей версии закрыты Checkpoint 0-10 из `plan.md` в реализованной части
аудита модели:

Текущий стабилизированный статус: source-gated release candidate от 2026-07-06,
зафиксированный в `docs/release_candidate_status.md`. Он подтверждает полный
`pytest -q`, но не снимает `SOURCE_REQUIRED` ограничения с неподключённых
published-кандидатов.

Рабочий pipeline закрытия оставшихся source-gates зафиксирован в
`docs/milestone_closure_pipeline.md`; он синхронизирован с
`python -m source_gate_pipeline --pretty` и `/api/source-gates`. Реестр
незакрытых формульных, область-применимости и тестовых вопросов ведётся в
`docs/source_gate_unresolved_questions.md`.
Source-gate JSON records include `current_blocking_stage` and structured
`release_criteria` for every source, so clients do not need to parse Markdown
to find the next required proof.

- зафиксированы baseline-тесты MathCAD-совместимой ветки;
- режим `regime_aware` переименован в `experimental_regime_aware`, а старое имя
  оставлено как alias для совместимости;
- результаты содержат `model_scientific_status`, `model_source_status`,
  `source_gate_reasons`, `fluid`, `property_backend`, `property_source`,
  `property_warning` и `near_critical_warning`;
- добавлен общий интерфейс свойств насыщения CO2/NH3 в `refrigerant_properties.py`;
- создан русскоязычный реестр формул и свойств `docs/formula_registry.md`;
- введен явный баланс давления в `pressure_balance.py`;
- `distributed_steady` разносит гидростатику, трение, ускорительные и местные
  члены по отдельным pressure-balance термам;
- добавлен выбор модели трения: `mathcad_compat`, `colebrook_white`,
  `churchill_explicit`, `laminar_only`, `zero_friction`.
- designer передает в solver сегментную `LoopGeometry`: длины, высоты,
  диаметры, шероховатости, площади, ориентации и `heat_mode` основных участков;
- результат содержит `geometry_source`, а `pressure_balance_sections` показывает
  геометрию каждого расчетного участка.
- опубликованные двухфазные замыкания, уже подтвержденные источниками,
  вынесены в `published_friction.py` и `published_void_fraction.py`;
- `homogeneous_equilibrium`, `zivi` и Lockhart-Martinelli/Chisholm покрыты
  отдельными unit-тестами;
- published closure-модели дополнительно проверяются на отсутствие зависимостей
  от `EXP-*` записей реестра.
- добавлен универсальный фасад `RefrigerantLoopModel` для CO2/NH3 через общий
  `RefrigerantSaturationProperties`;
- NH3/R717/Ammonia считается тем же steady solver на CoolProp-свойствах без
  переноса CO2-specific табличного backend;
- добавлены reference CSV для CoolProp CO2/NH3 в `data/reference_properties/`;
- результаты содержат `fluid_cas`, `refrigerant_name`, `outlet_mass_quality`,
  `outlet_no_slip_gas_volume_fraction` и `outlet_closure_void_fraction`.
- добавлен safe scaffold `boiling_heat_transfer.py`: при
  `heat_transfer_model="prescribed_heat_input"` результат содержит средний
  `boiling_heat_flux_w_m2`, а `boiling_heat_transfer_limit` и `dryout_limit`
  явно остаются `not_evaluated_source_required` до published-корреляций.
- для `heat_transfer_model="wall_coupled"` добавлена пользовательская lumped
  wall/soil boundary condition: solver вычисляет `qtr` из
  `G_eff * (T_soil - tcon)` и возвращает `wall_soil_*` поля результата; это не
  снимает source-gate для published HTC/dryout корреляций.
- добавлен отдельный `critical_loads.py`: методы `critical_loads(...)` фасадов
  строят отчёт по нижней/верхней гидродинамической границе текущего steady
  solver и отдельно проверяют диссертационный предел `f=0`; одиночный
  `run(...)` по-прежнему возвращает `qcrit_status="not_evaluated"`.
- добавлен быстрый слой сценарной матрицы `scenario_matrix.py`: он проверяет
  CO2/NH3 температурные сетки, вариации `qtr`, `H`, `Li`, диаметра,
  шероховатости, near-critical область, нулевые/отрицательные входы и
  недоступный backend через структурированные статусы без запуска дорогого
  `qcrit`-sweep по умолчанию.
- добавлен отдельный вход `regime_model`: старый `CO2MathcadModel` по умолчанию
  сохраняет `experimental_regime_aware`, а `RefrigerantLoopModel` по умолчанию
  использует `published_regime_map`, который пока возвращает source-gated
  `source_required` metadata вместо неподтвержденных режимных границ.
- designer/API сценарии поддерживают выбор `fluid`, `property_backend`,
  `regime_model`, `friction_model`, `heat_transfer_model` и показывают
  `model_source_status`, `source_gate_reasons`, `failure_class`, boiling/dryout
  и `qcrit`-статусы без запуска дорогого `qcrit`-sweep.
- добавлена opt-in модель начала кипения `ishkov_superheat`: она использует
  диссертационную форму с внешним перегревом, итерационно учитывает перепад
  давления конденсатора из текущего steady-pass и возвращает
  `boiling_onset_model`, `onset_superheat_k`,
  `onset_condenser_pressure_drop_pa`, `raw_preboiling_length_fraction`,
  `preboiling_status` и `boiling_onset_source`.
- найденный внешний полный текст Chen 1962 / OSTI `10.2172/4636495`
  оформлен как `HTC-CHEN-1962-SOURCE-CANDIDATE`: metadata доступны в
  результатах diagnostics, но saturated flow-boiling HTC, dryout и CHF
  по нему не рассчитываются до отдельного аудита применимости.
- добавлен слой `SECONDARY_FORMULA_CANDIDATE / NOT_RELEASED` в
  `docs/secondary_formula_candidates.md`: формулы MSH/Friedel, ACHP
  acceleration/Shah, ht Chen-Bennett/Liu-Winterton, secondary Zivi и
  Taitel-Dukler 1976 horizontal map зафиксированы как audit guidance, но не
  снимают `SOURCE_REQUIRED` и не становятся runtime `published` моделями.
- добавлен машинный source-gate pipeline: `source_gate_pipeline.py`,
  `python -m source_gate_pipeline --pretty` и `/api/source-gates` показывают
  `current_blocking_stage`, `release_criteria`, группы milestones и ближайшие
  приоритеты по каждому незакрытому источнику.
- добавлен `docs/physics_gap_matrix.md`: компактная карта runtime-физики,
  source-gate кандидатов, внешних источников и оставшихся академических
  ограничений.

Сегментная геометрия сейчас ограничена одним участком каждого типа:
`evaporator`, `riser`, `condenser`, `downcomer`. Произвольные connector-сегменты,
несколько однотипных участков и местные сопротивления на переходах диаметра
остаются задачей следующих этапов.

Реестр формул фиксирует источник, область применимости, код и тесты для каждой
реализованной формулы. Опубликованные модели отделены от MathCAD-compatible
записей и эвристик. Все эвристики без первоисточника помечены как
`EXPERIMENTAL / NO PRIMARY SOURCE`. Результаты `run(...)` и `run_result(...)`
дополнительно содержат `friction_model`, `pressure_balance_terms`,
`pressure_balance_sections`, суммарные pressure-balance вклады,
`pressure_balance_residual_pa`, `qcrit_status` и `qcrit_model`. Поле
`model_source_status` агрегирует незакрытые source-gate ограничения: published
defaults могут быть `source_required`, даже если отдельные подтвержденные
closure-модели имеют `model_scientific_status="published"`.

Müller-Steinhagen-Heck, Friedel, Zuber-Findlay, Taitel-Barnea-Dukler и
Wojtan-Ursenbacher-Thome пока не подключаются как расчетные `published`-модели:
для них требуется сверка точных формул и областей применимости по полному
первоисточнику. Source-audit текущего состояния записан в
`docs/source_audit_checkpoint_5_6.md`. Для Müller-Steinhagen-Heck и Friedel
добавлены защитные source-gate функции в `published_friction.py`; они
выбрасывают `SourceRequiredCorrelationError`, пока первоисточник не сверен.

С 2026-07-04 для всех записей `SOURCE_REQUIRED` действует политика
primary-source-only: DOI landing page, Crossref metadata, abstract, учебник,
обзор или пересказ формулы не снимают source-gate. Published-корреляция может
быть подключена только после проверки полного первоисточника и обновления
`docs/formula_registry.md`, `docs/source_audit_checkpoint_5_6.md` и тестов.

Open-web аудит от 2026-07-04 и контрольная endpoint-проверка от 2026-07-05
оформлены отдельно в `docs/source_audit_open_web_2026-07-04.md` и
`docs/source_audit_open_web_2026-07-05.md`, а машинно-проверяемые решения по
каждой source-gate записи вынесены в `docs/source_gate_manifest.json`.
Crossref/Unpaywall/OpenAlex и publisher endpoints подтвердили библиографию для
части моделей, но не дали открытый полный текст для MSH, Zuber-Findlay,
Taitel-Barnea-Dukler, Wojtan/Thome, Kandlikar или Gungor-Winterton; повторная
проверка endpoints оставила эти gates закрытыми. EPFL landing pages для Wojtan
Part I/II не снимают gate, потому что DSpace API не показывает
`ORIGINAL`/full-text bitstream. Найденный официальный OSTI PDF
`10.2172/4636495` сохранён как `source_candidate`, но не подключён к runtime:
его применимость к текущей постановке ещё не аудирована.

Дополнительный академический поиск от 2026-07-06 зафиксировал вторичные
формульные кандидаты в `docs/secondary_formula_candidates.md` и связал их с
`docs/formula_registry.md` / `docs/source_gate_manifest.json`. Эти записи
полезны для будущего переноса формул, но являются `NOT_RELEASED`: guard-функции
MSH/Friedel остаются активными, `published_regime_map` остаётся source-gated,
а HTC/dryout/CHF по-прежнему не рассчитываются.

Локальный candidate-only аудит первоисточников разнесён по отдельным документам:
`docs/chen_1962_formula_audit_2026-07-06.md` фиксирует OSTI/Chen 1962 как
HTC-кандидат с незакрытыми Eq. (17), `F/S`, SI mapping и reference-test
вопросами; `docs/dissertation_formula_audit_2026-07-06.md` фиксирует EPFL
TH2978/TH3337 как audit guidance для WUT, MSH и Friedel, но не снимает
журнальные source-gates.

Полные первоисточники для будущего снятия gate ожидаются как локальные файлы в
`sources/primary/`. PDF, сканы и извлечённые полные тексты из этой папки не
коммитятся; tracked-инвентарь `docs/primary_source_inventory.md` должен хранить
имя локального файла, SHA256, библиографию, страницы/уравнения, решение аудита,
связанные изменения реестра формул и тесты. Без такой записи manifest не должен
переводить модель в `released`.

## Академический контекст и source-gate

Для научной прослеживаемости используйте связку документов:

- `docs/formula_registry.md` - список реализованных формул, источников,
  применимости и тестов;
- `docs/source_gate_manifest.json` - машинно-проверяемые решения по
  неподключенным published-кандидатам;
- `docs/secondary_formula_candidates.md` - формулы из авторитетных вторичных
  источников, используемые только как audit guidance и future implementation
  notes;
- `docs/primary_source_inventory.md` - локальный инвентарь полных
  первоисточников из `sources/primary/`, используемых для снятия gate;
- `docs/source_audit_checkpoint_5_6.md` и
  `docs/source_audit_open_web_2026-07-05.md` - аудит первоисточников;
- `docs/source_audit_followup_2026-07-06.md` - follow-up по Crossref,
  endpoints, OSTI и EPFL dissertation candidates;
- `docs/chen_1962_formula_audit_2026-07-06.md` - page/equation audit для
  локального Chen/OSTI HTC source-candidate;
- `docs/dissertation_formula_audit_2026-07-06.md` - page-level candidate map
  по EPFL TH2978/TH3337 для будущего аудита WUT, MSH и Friedel;
- `docs/physics_gap_matrix.md` - краткая матрица активной физики, внешних
  источников и незакрытых source-gate ограничений;
- `docs/milestone_closure_pipeline.md` - рабочий порядок закрытия оставшихся
  source-gates, сгруппированный по пути снятия блокировок;
- `docs/source_gate_unresolved_questions.md` - проверяемый реестр незакрытых
  формульных, scope и test-proof вопросов по каждому gate;
- `docs/release_candidate_status.md` - текущий source-gated release-candidate
  статус, результаты полного pytest и план ускорения тестов без изменения
  физики;
- `docs/get_co2_academic_reference.md` - академическое описание модели,
  допущений, статусов и ограничений.

`model_source_status="source_required"` не является ошибкой solver. Это
академический флаг: часть выбранной цепочки расчета ссылается на опубликованную
модель только библиографически, но формулы/коэффициенты ещё не сверены по
полному первоисточнику. `source_candidate` означает, что полный текст найден,
но применимость к текущей постановке не аудирована; такой источник тоже не
подключается к runtime автоматически.
`SECONDARY_FORMULA_CANDIDATE / NOT_RELEASED` означает, что формула найдена во
вторичном источнике высокого качества, но полный первоисточник или локальный
аудит всё ещё нужны до runtime release.

Checkpoint 6 split:

- текущие эвристические режимные классификаторы вынесены в
  `experimental_regimes.py`;
- `two_phase_regimes.py` оставлен как compatibility-слой для старых imports и
  summary helpers;
- `published_regimes.py` пока содержит только защитные заготовки с
  `unknown_or_out_of_range` / `source_required`, без опубликованных режимных
  карт.

## Сценарная матрица

Для быстрой проверки физического и численного статуса набора точек используйте
`scenario_matrix.py`:

```python
from scenario_matrix import run_scenario_matrix

report = run_scenario_matrix()
print(report.status_counts)
print(report.failure_class_counts)
```

Матрица использует быстрый root scan текущего steady solver и возвращает
`working`, `no_root`, `no_driving_head`, `near_critical_region`,
`property_out_of_range`, `validation_error`, `backend_unavailable` или
`numerical_failure`. Это smoke-диагностика покрытия режимов, а не новая
физическая модель и не расчёт `critical_loads`.

## Демонстрационный отчет

```powershell
python run_get_co2_demo-1.py
```

Скрипт создает и обновляет файлы в `artifacts/`:

- `get_co2_results.csv` - расчетные сценарии;
- `get_co2_sweep.csv` - sweep по тепловой нагрузке;
- `get_co2_report.md` - сводный отчет;
- `*.png` - графики sweep, профилей испарителя/райзера и режимов течения.

Markdown-отчет дополнительно выводит source/failure/boiling/qcrit diagnostics.
`qcrit_status="not_evaluated"` в этом отчете означает, что отдельный
`critical_loads`-расчет не запускался.

Файлы `get_co2_*.csv`, `get_co2_*.png` и `get_co2_*.md` в корне проекта являются
историческими артефактами. Новые результаты следует писать в `artifacts/`.

## Тесты

Полный набор:

```powershell
pytest -q
```

Полный прогон включает тяжёлые baseline/distributed сценарии и может занимать
несколько минут. Для проверки академического source-gate контура используйте
точечный набор ниже.

Если окружение не дает писать во внешний temp-каталог, используйте локальный temp:

```powershell
$tmp = (Resolve-Path '.pytest-tmp').Path; $env:TMP = $tmp; $env:TEMP = $tmp; pytest -q
```

Быстрый набор без тяжелых распределенных расчетов:

```powershell
pytest -q -m "not slow"
```

Сценарная матрица:

```powershell
pytest tests/test_scenario_matrix.py -q
```

Source-gate документация и академический manifest:

```powershell
pytest tests/test_formula_registry.py tests/test_source_gate_manifest.py tests/test_source_gate_pipeline.py tests/test_get_designer_api.py -q
```

Начало кипения и source-gated диагностика теплообмена:

```powershell
pytest tests/test_boiling_onset_model.py tests/test_boiling_diagnostics.py -q
```

Только тяжелые тесты:

```powershell
pytest -q -m slow
```

## Ограничения

- Модель ориентирована на воспроизведение рабочего стационарного режима MathCAD
  worksheet, а не на универсальный расчет любых CO2-контуров.
- Критические тепловые нагрузки доступны через `critical_loads.py` и методы
  `critical_loads(...)` фасадов. Это границы текущего steady solver с отдельным
  пределом `f=0`, а не экспериментальная валидация и не подгонка к таблицам
  диссертации.
- Boiling/dryout diagnostics пока не являются прогнозом heat-transfer crisis:
  Kandlikar, Shah, Gungor-Winterton, dryout и CHF-корреляции не подключены без
  сверки первоисточника.
- `boiling_onset_model="ishkov_superheat"` является opt-in уточнением начала
  кипения по диссертационной постановке с пользовательским перегревом. Оно не
  является самостоятельной экспериментальной калибровкой и не снимает
  source-gate для HTC/dryout/CHF.
- Свойства CO2 заданы таблично и интерполируются; расчеты вне области исходных
  таблиц нужно трактовать осторожно.
- NH3 через CoolProp доступен в общем loop solver; qcrit для него считается тем
  же алгоритмом границ solver, но режимные карты и boiling/dryout prediction еще
  не доведены до published-физики.
- Режим `distributed_steady` дает более подробные профили и диагностику, но он
  заметно тяжелее базового `worksheet_compatible`.
- Сценарная матрица является smoke-проверкой статусов на выбранных точках; она
  не уточняет физические критические нагрузки и не заменяет `critical_loads.py`.
- Геометрический конструктор передает основные расчетные участки, но пока не
  поддерживает произвольное число однотипных участков, connector-сегменты и
  местные сопротивления на переходах диаметра.
- Режимные карты и drift-flux-коэффициенты без полного первоисточника остаются
  experimental, даже если их структура похожа на опубликованные модели.
