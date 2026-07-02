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

## Статус физической доработки

В текущей версии закрыты Checkpoint 0-4 аудита модели и выполнена
source-strict часть Checkpoint 5:

- зафиксированы baseline-тесты MathCAD-совместимой ветки;
- режим `regime_aware` переименован в `experimental_regime_aware`, а старое имя
  оставлено как alias для совместимости;
- результаты содержат `model_scientific_status`, `fluid`, `property_backend`,
  `property_source`, `property_warning` и `near_critical_warning`;
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

Сегментная геометрия сейчас ограничена одним участком каждого типа:
`evaporator`, `riser`, `condenser`, `downcomer`. Произвольные connector-сегменты,
несколько однотипных участков и местные сопротивления на переходах диаметра
остаются задачей следующих этапов.

Реестр формул фиксирует источник, область применимости, код и тесты для каждой
реализованной формулы. Опубликованные модели отделены от MathCAD-compatible
записей и эвристик. Все эвристики без первоисточника помечены как
`EXPERIMENTAL / NO PRIMARY SOURCE`. Результаты `run(...)` и `run_result(...)`
дополнительно содержат `friction_model`, `pressure_balance_terms`,
`pressure_balance_sections`, суммарные pressure-balance вклады и
`pressure_balance_residual_pa`.

Müller-Steinhagen-Heck, Friedel, Zuber-Findlay, Taitel-Barnea-Dukler и
Wojtan-Ursenbacher-Thome пока не подключаются как расчетные `published`-модели:
для них требуется сверка точных формул и областей применимости по полному
первоисточнику.

## Демонстрационный отчет

```powershell
python run_get_co2_demo-1.py
```

Скрипт создает и обновляет файлы в `artifacts/`:

- `get_co2_results.csv` - расчетные сценарии;
- `get_co2_sweep.csv` - sweep по тепловой нагрузке;
- `get_co2_report.md` - сводный отчет;
- `*.png` - графики sweep, профилей испарителя/райзера и режимов течения.

Файлы `get_co2_*.csv`, `get_co2_*.png` и `get_co2_*.md` в корне проекта являются
историческими артефактами. Новые результаты следует писать в `artifacts/`.

## Тесты

Полный набор:

```powershell
pytest -q
```

Если окружение не дает писать во внешний temp-каталог, используйте локальный temp:

```powershell
$tmp = (Resolve-Path '.pytest-tmp').Path; $env:TMP = $tmp; $env:TEMP = $tmp; pytest -q
```

Быстрый набор без тяжелых распределенных расчетов:

```powershell
pytest -q -m "not slow"
```

Только тяжелые тесты:

```powershell
pytest -q -m slow
```

## Ограничения

- Модель ориентирована на воспроизведение рабочего стационарного режима MathCAD
  worksheet, а не на универсальный расчет любых CO2-контуров.
- Критические тепловые нагрузки и предельные режимы из диссертации не реализованы
  как полный внешний алгоритм поиска границ.
- Свойства CO2 заданы таблично и интерполируются; расчеты вне области исходных
  таблиц нужно трактовать осторожно.
- Для CO2/NH3 через CoolProp свойства насыщения доступны через общий интерфейс,
  но полноценная ветка NH3 в loop solver еще не завершена.
- Режим `distributed_steady` дает более подробные профили и диагностику, но он
  заметно тяжелее базового `worksheet_compatible`.
- Геометрический конструктор передает основные расчетные участки, но пока не
  поддерживает произвольное число однотипных участков, connector-сегменты и
  местные сопротивления на переходах диаметра.
- Режимные карты и drift-flux-коэффициенты без полного первоисточника остаются
  experimental, даже если их структура похожа на опубликованные модели.
