# Научная основа для режимно-зависимой модели GET CO₂/NH₃

## 1. Зачем нужен этот файл

Текущий код уже умеет диагностировать локальные режимы течения и переключать замыкания
в `distributed_steady`, но часть этих переключений была введена как инженерная эвристика.

Если принимать только опубликованные научные данные, то следующий этап должен опираться
не на "разумные коэффициенты", а на конкретные статьи и корреляции из первоисточников.

Этот файл фиксирует:

- какие режимы реально наблюдаются в текущей системе;
- какие элементы текущей модели уже имеют опору на классические публикации;
- какие элементы нужно заменить на корреляции из литературы;
- в каком порядке это лучше реализовывать.

После Checkpoint 8 модель умеет считать NH₃/R717 через тот же `SteadyLoopSolver`
и CoolProp-свойства, а после Checkpoint 9 получила отдельный qcrit-отчёт
`critical_loads.py`. Этот файл по-прежнему относится к режимной физике, а не к
backend свойств или critical-load solver. NH₃-ветка не добавляет опубликованных
режимных карт и не легализует перенос CO₂-ориентированных эвристик на аммиак.

## 2. Какие режимы реально наблюдаются в системе

Ниже перечислены режимы, полученные в текущем `distributed_steady` расчете
для геометрии `H=2.5 m`, `Li=200 m`, `tcon=0 C` и sweep по `qtr`
в режиме `closure_model="regime_aware"`.

### 2.1. Доминирующие режимы по участкам

- При `qtr = 2.48...5 W/m`:
  - испаритель: `annular_transition`
  - riser: `churn`
- При `qtr = 10...120 W/m`:
  - испаритель: `intermittent`
  - riser: `churn`

### 2.2. Локальные режимы, встречающиеся внутри профиля испарителя

Даже когда доминирующий режим один, локальный профиль содержит несколько режимов.
По текущим расчетам в горизонтальном испарителе встречаются:

- `single_liquid_heating`
- `bubble_onset`
- `bubbly`
- `stratified_wavy`
- `intermittent`
- `annular_transition`
- `annular`
- `annular_mist`

В вертикальном riser по текущим расчетам встречаются:

- `bubbly`
- `slug`
- `churn`
- `annular`
- `annular_mist`

### 2.3. Практический вывод

Для научно корректной следующей версии модели нужны, как минимум:

- режимная карта для **горизонтального испаряющегося потока**;
- режимная карта для **вертикального восходящего двухфазного потока**;
- published correlation для **void fraction / slip / mixture density**;
- published correlation для **frictional pressure drop**.

## 3. Что в текущем коде уже имеет опору на опубликованные корреляции

Следующие элементы уже можно считать опирающимися на классические публикации:

- `Lockhart-Martinelli` для двухфазного параметра `X`
- `Chisholm` для двухфазного множителя к жидкостным потерям
- `Zivi` для оценки скольжения фаз
- `homogeneous equilibrium` как опубликованное предельное допущение без скольжения
- CoolProp/REFPROP свойства насыщения CO₂/NH₃ как published property backend,
  но не как валидация гидродинамической режимной карты

После source-strict части Checkpoint 5 эти элементы вынесены в отдельные
модули:

- `published_friction.py`;
- `published_void_fraction.py`.

`two_phase_closures.py` остаётся совместимым фасадом solver и хранит
worksheet/experimental-логику, но published-функции больше не добавляются туда
как первичное место реализации.

После Checkpoint 6 split режимная часть также разделена:

- `experimental_regimes.py` — текущие эвристические пороги, явно помеченные как
  `EXPERIMENTAL / NO PRIMARY SOURCE`;
- `two_phase_regimes.py` — compatibility wrappers и summary helpers;
- `published_regimes.py` — защитные заготовки published-карт, которые пока
  возвращают `unknown_or_out_of_range` / `source_required`, а не физический
  режим.

После source-gate обновления Checkpoint 5-6 в публичном API появился отдельный
параметр `regime_model`. Он не меняет выбранное замыкание пустотности/трения
(`closure_model`), а управляет только режимной диагностикой и её научным
статусом:

- `experimental_regime_aware` — старые эвристические пороги со статусом
  `experimental`;
- `published_regime_map` — source-gated published-заготовка со статусом
  `source_required`.

То есть режимы:

- `worksheet_compatible`
- `homogeneous_equilibrium`
- `zivi`

можно считать научно понятными и прослеживаемыми по литературе.

## 4. Что в текущем коде не должно считаться научно верифицированным

Следующие части текущего `regime_aware` режима нельзя считать опубликованными
корреляциями в строгом смысле:

- пороги в `experimental_regimes.py`
  для переходов `bubbly / intermittent / annular / churn`;
- коэффициенты `distribution_parameter` и `drift_prefactor`
  в `drift_flux_void_fraction(...)` из `two_phase_closures.py`;
- коэффициенты в `annular_core_void_fraction(...)`;
- коэффициенты и веса в `separated_shear`, `annular_film`,
  `stratified_separated`, `homogeneous_mixture` из `two_phase_closures.py`.

Эти элементы были введены как исследовательские эвристики и должны быть либо:

- заменены опубликованными корреляциями;
- либо оставлены только как `experimental`.

Это ограничение одинаково важно для CO₂ и NH₃. Новая возможность выбрать
`fluid="NH3"` меняет свойства фаз, но не превращает текущие пороги
`experimental_regimes.py` в опубликованную карту аммиачного течения.

## 5. Какие первоисточники следует принять за основу

Ниже перечислены публикации, которые подходят по физике задачи и должны стать
опорой для следующей реализации.

### 5.1. Базовые корреляции, которые уже согласуются с кодом

1. Lockhart, R.W., Martinelli, R.C. (1949)
   Proposed correlation for isothermal two-phase, two-component flow in pipes.

2. Chisholm, D. (1973)
   Pressure gradients due to friction during the flow of evaporating two-phase mixtures in smooth tubes and channels.

3. Zivi, S.M. (1964)
   Estimation of steady-state steam void-fraction by means of the principle of minimum entropy production.

### 5.2. Для вертикального riser

4. Zuber, N., Findlay, J.A. (1965)
   Average volumetric concentration in two-phase flow systems.

   Что брать из статьи:
   - drift-flux представление для `void fraction`;
   - структуру вида `alpha = j_g / (C0 * j + Vgj)`.

5. Taitel, Y., Barnea, D., Dukler, A.E. (1980)
   Modeling flow pattern transitions for steady upward gas-liquid flow in vertical tubes.

   Что брать из статьи:
   - published regime map для вертикального восходящего потока;
   - переходы `bubbly -> slug -> churn -> annular`.

### 5.3. Для горизонтального испарителя

6. Wojtan, L., Ursenbacher, T., Thome, J.R. (2005)
   Investigation of flow boiling in horizontal tubes: Part I – a new diabatic two-phase flow pattern map.

   Что брать из статьи:
   - режимную карту именно для **горизонтального испаряющегося потока**;
   - различение `stratified-wavy`, `intermittent`, `annular`, `mist/dryout`.

### 5.4. Для frictional pressure drop как published fallback

7. Friedel, L. (1979)
   Improved friction pressure drop correlations for horizontal and vertical two-phase pipe flow.

8. Muller-Steinhagen, H., Heck, K. (1986)
   A simple friction pressure drop correlation for two-phase flow in pipes.

Эти две публикации нужны как published fallback для расчета `deltaP`,
если на первом шаге не удастся сразу реализовать полноценную
flow-pattern-based pressure-drop model из специализированных статей по испарению.

Текущий source-gate аудит не подтвердил полный перенос формул в код: для
Muller-Steinhagen-Heck доступная библиографическая информация и предварительная страница статьи
подтверждает статью, DOI, область pressure-drop correlation и наличие двух
подгоночных параметров, но не даёт достаточной формульной записи и соглашений о величинах.
Для Friedel полный первичный текст доклада в текущем окружении также не доступен. Поэтому
в коде допустимы только защитные функции, которые явно требуют первоисточник и
не участвуют в расчёте.

Политика source-audit от 2026-07-04: для всех перечисленных source-gate
записей действует primary-source-only критерий. DOI, Crossref, abstract,
учебник, обзорная статья или готовая формула из вторичного источника могут
использоваться для библиографической ориентации, но не для снятия
`SOURCE_REQUIRED` и не для подключения расчётной published-корреляции.

## 6. Научно корректная архитектура следующей версии

### 6.1. Горизонтальный испаритель

Для испарителя рекомендуется такая цепочка:

1. Определить режим по published flow-pattern map:
   - `Wojtan-Ursenbacher-Thome (2005)`.

2. Для `void fraction / slip` использовать только published closure:
   - на первом шаге допустим `Zivi (1964)` как fallback;
   - после получения точной формулы из первоисточника можно подключить
     `Zuber-Findlay` или другую published evaporating-flow void-fraction correlation,
     если она явно применима к горизонтальному испарению.

3. Для frictional pressure drop:
   - временный published fallback: `Lockhart-Martinelli + Chisholm`,
     либо после source-аудита `Friedel`/`Muller-Steinhagen-Heck`;
   - следующий уровень: regime-specific pressure-drop model из статьи,
     если будет доступен первоисточник с точной формой корреляции.

### 6.2. Вертикальный riser

Для riser рекомендуется такая цепочка:

1. Определить режим по:
   - `Taitel-Barnea-Dukler (1980)`.

2. Рассчитать `void fraction` и плотность смеси по:
   - `Zuber-Findlay (1965)` как базовой published drift-flux модели.

3. Рассчитать frictional part:
   - на первом шаге оставить published fallback:
     `Lockhart-Martinelli + Chisholm` или homogeneous-mixture published form;
   - затем, при необходимости, добавить более специализированную vertical-up correlation.

## 7. Что нужно сделать в коде

### Шаг 1. Разделить published и experimental

В коде нужно явно отделить:

- published closures;
- эвристические experimental closures.

Практический статус:

- текущий `regime_aware` сохранён только как alias на
  `experimental_regime_aware`;
- режимная диагностика отделена от `closure_model` параметром `regime_model`;
- published closures вынесены в `published_friction.py` и
  `published_void_fraction.py`;
- режимные эвристики вынесены в `experimental_regimes.py`;
- новый научно корректный режим должен развиваться из
  `published_regime_map` только после проверки полных первоисточников.

### Шаг 2. Вынести режимные карты в отдельный published layer

Структурное разделение уже выполнено:

- текущая эвристическая карта находится в `experimental_regimes.py`;
- `two_phase_regimes.py` оставлен как слой совместимости;
- `published_regimes.py` содержит только защитные заготовки.

Остаётся реализовать новые published-карты для:

- горизонтального испарителя;
- вертикального riser.

### Шаг 3. Вынести published closures отдельно от экспериментальных

Статус: базовый published слой выделен. Уже реализованы:

- `published_void_fraction.zivi_1964_slip_ratio(...)`;
- `published_void_fraction.homogeneous_equilibrium_slip_ratio(...)`;
- `published_void_fraction.void_fraction_from_quality(...)`;
- `published_friction.martinelli_parameter(...)`;
- `published_friction.chisholm_constant(...)`;
- `published_friction.two_phase_multiplier_liquid_reference(...)`.

Не реализованы без полного первоисточника:

- `zuber_findlay_1965_void_fraction(...)`;
- `friedel_1979_pressure_gradient(...)` — в коде есть только защитная
  source-gate функция `friedel_1979_pressure_gradient_pa_per_m(...)`;
- `muller_steinhagen_heck_1986_pressure_gradient(...)` — в коде есть только
  защитная source-gate функция
  `muller_steinhagen_heck_1986_pressure_gradient_pa_per_m(...)`.

### Шаг 4. Перевести solver на published mode

В `co2_steady_solver.py`
новый published mode должен:

- для испарителя использовать published horizontal flow-pattern map;
- для riser использовать published vertical flow-pattern map;
- для каждого control volume вызывать только published correlations;
- не использовать коэффициенты, которые не восходят к статье.

## 8. Что можно делать уже сейчас, а что нельзя

### Можно делать уже сейчас

- использовать `worksheet_compatible` как reference mode;
- использовать `zivi` и `homogeneous_equilibrium` как published fallback closures;
- использовать `Lockhart-Martinelli + Chisholm` как published базовый pressure-drop layer.
- использовать `RefrigerantLoopModel(fluid="NH3", property_backend="coolprop")`
  для программно проверенных steady-state sanity-сценариев;
- проверять published closures тестами `tests/test_void_fraction_models.py`,
  `tests/test_two_phase_pressure_drop.py` и guard-тестом реестра формул.

### Нельзя считать научно корректным без замены

- текущие коэффициенты `drift_flux_void_fraction(...)`;
- текущие `annular_core`, `separated_shear`, `annular_film`;
- текущие пороги режима в `experimental_regimes.py`.
- результаты NH₃ как экспериментально валидированную аммиачную ГЕТ без
  отдельного сопоставления с данными.
- реализацию WUT/TBD/Zuber-Findlay/MSH/Friedel по вторичному пересказу без
  полного первоисточника и обновления `docs/formula_registry.md`.

## 9. Практический следующий шаг

Следующий корректный шаг не в том, чтобы "подкрутить" существующие эвристики,
а в том, чтобы:

1. изолировать текущий experimental режим; структурная изоляция и
   source/status metadata уже выполнены;
2. получить полный текст и точные формулы для нового published vertical layer:
   - `Zuber-Findlay (1965)` для void fraction в riser;
   - `Taitel-Barnea-Dukler (1980)` для вертикальной regime map;
3. после этого внедрить published horizontal regime map:
   - `Wojtan-Ursenbacher-Thome (2005)`.

Если полный первоисточник не получен, корректный следующий шаг — не переносить
формулу из пересказа, а сохранять source-gate, расширять аудит и тестировать,
что runtime-результат остаётся `model_source_status="source_required"`.

## 10. Ограничение текущего этапа

По состоянию на Checkpoint 6 split точные формулы для HEM, Zivi и
Lockhart-Martinelli/Chisholm уже вынесены в source-strict published-слой, а
режимные эвристики отделены от будущих published-карт. Следующий шаг реализации
published-карт должен выполняться только после того, как точные формулы
остальных перечисленных статей будут доступны локально или подтверждены по
полному тексту статей.

До этого момента корректно считать, что:

- `worksheet_compatible`, `homogeneous_equilibrium`, `zivi` — научно прослеживаемые режимы;
- NH₃ поддержан на уровне свойств и общего solver, но не на уровне published
  regime map;
- `published_friction.py` и `published_void_fraction.py` — единственные места для новых published closure-функций;
- `published_regimes.py` — только source-gate заготовка с `source_required`, не published-карта;
- текущий `regime_aware` / `experimental_regime_aware` — исследовательский режим, а не окончательная научная модель.

После source-gate finish результат solver дополнительно содержит:

- `model_source_status`;
- `source_gate_reasons`.

Эти поля нужны для академически корректной интерпретации `RefrigerantLoopModel`.
Если фасад использует `closure_model="zivi"` и `regime_model="published_regime_map"`,
то closure-слой может быть `published`, но весь результат остаётся
`source_required`, пока опубликованные WUT/TBD-карты, Zuber-Findlay drift-flux,
boiling HTC и dryout/CHF корреляции не перенесены из полных первоисточников.
Для `experimental_regime_aware` агрегированный статус должен читаться как
`experimental_no_primary_source`, даже если отдельные базовые формулы трения и
пустотности имеют published-источники.
