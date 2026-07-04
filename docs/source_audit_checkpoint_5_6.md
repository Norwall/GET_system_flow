# Аудит источников Checkpoint 5-6

Дата проверки: 2026-07-03.
Повторная проверка политики: 2026-07-04.

Цель проверки - отделить библиографически подтвержденные published-модели от
формул, которые можно переносить в расчет только после сверки полного
первоисточника. Этот документ является академическим ограничителем: наличие DOI
или landing page не считается достаточным основанием для переноса коэффициентов,
transition equations или областей применимости в код.

## Политика проверки 2026-07-04

Для снятия source-gate по Checkpoint 5-6 требуется полный первоисточник:
publisher PDF, авторская копия, скан доклада или институционально доступный
полный текст. Crossref, DOI landing page, abstract, цитирование в обзоре,
учебник или пересказ формулы не являются достаточным основанием для подключения
модели как `published`.

Если полный первоисточник недоступен, код должен сохранять `SOURCE_REQUIRED`
или `source_required`, а runtime-результат не должен выглядеть как полностью
source-complete published-модель.

## Подтвержденные библиографические записи

| Модель | Первичная запись | Статус доступа |
| --- | --- | --- |
| Muller-Steinhagen-Heck pressure drop | H. Muller-Steinhagen, K. Heck. A simple friction pressure drop correlation for two-phase flow in pipes. Chemical Engineering and Processing, 1986, 20(6), 297-308. DOI `10.1016/0255-2701(86)80008-3`. | Crossref подтверждает DOI, страницы и Elsevier landing/TDM endpoints. Полный текст через проверенный endpoint без авторизованного API-контекста не получен. |
| Friedel pressure drop | L. Friedel. Improved friction pressure drop correlations for horizontal and vertical two-phase flow. European Two-Phase Flow Group Meeting, Ispra, paper E2, 1979. | Первичная DOI-запись в Crossref по названию не найдена. Оставлено как `SOURCE_REQUIRED`. |
| Zuber-Findlay drift-flux | N. Zuber, J. A. Findlay. Average Volumetric Concentration in Two-Phase Flow Systems. Journal of Heat Transfer, 1965, 87(4), 453-468. DOI `10.1115/1.3689137`. | Crossref подтверждает DOI, страницы и ASME PDF URL. Прямой HEAD-запрос к PDF вернул `403 Forbidden`, поэтому коэффициенты не перенесены. |
| Taitel-Barnea-Dukler vertical upflow map | Y. Taitel, D. Barnea, A. E. Dukler. Modelling flow pattern transitions for steady upward gas-liquid flow in vertical tubes. AIChE Journal, 1980, 26(3), 345-354. DOI `10.1002/aic.690260304`. | Crossref подтверждает DOI, страницы и Wiley PDF URL. Прямой HEAD-запрос к PDF вернул `403 Forbidden`, поэтому transition equations не перенесены. |
| Wojtan-Ursenbacher-Thome horizontal boiling map | L. Wojtan, T. Ursenbacher, J. R. Thome. Investigation of flow boiling in horizontal tubes: Part I - A new diabatic two-phase flow pattern map. International Journal of Heat and Mass Transfer, 2005, 48, 2955-2969. DOI `10.1016/j.ijheatmasstransfer.2004.12.012`. | Crossref подтверждает DOI, страницы и Elsevier landing/TDM endpoints. Полный текст через проверенный endpoint без авторизованного API-контекста не получен. |

## Связь с реестром формул

| Registry ID | Source-gate объект | Решение 2026-07-04 |
| --- | --- | --- |
| `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` | `published_friction.muller_steinhagen_heck_1986_pressure_gradient_pa_per_m` | Оставить guard-функцию. Не реализовывать MSH pressure-drop без полного первоисточника и сверки Darcy/Fanning, total/phase mass flux и опорных градиентов. |
| `TP-FRIEDEL-1979-SOURCE-GATE` | `published_friction.friedel_1979_pressure_gradient_pa_per_m` | Оставить guard-функцию. Не реализовывать Friedel pressure-drop без полного текста доклада и сверки всех безразмерных комплексов. |
| `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE` | будущий drift-flux adapter | Не подключать published drift-flux ветку. `C0`, `Vgj` и соглашения по средним величинам остаются source-gated. |
| `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE` | `published_regimes.classify_horizontal_evaporator_regime_result` | Оставить `unknown_or_out_of_range/source_required`. Не переносить transition criteria и dryout boundaries без полного первоисточника. |
| `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` | `published_regimes.classify_vertical_riser_regime_result` | Оставить `unknown_or_out_of_range/source_required`. Не переносить transition equations без полного первоисточника. |

## Решение для кода

- `published_regimes.py` остается source-gated: горизонтальная WUT-карта и
  вертикальная TBD-карта возвращают `unknown_or_out_of_range` со статусом
  `source_required`.
- `published_friction.py` оставляет MSH и Friedel как функции-заглушки,
  выбрасывающие `SourceRequiredCorrelationError`.
- Zuber-Findlay пока не добавляется как расчетная drift-flux ветка; текущие
  коэффициенты `C0/Kd` остаются только в experimental-слое.
- Новый вход `regime_model` отделяет режимную диагностику от `closure_model`.
  Значение `published_regime_map` означает source-gated published metadata, а
  `experimental_regime_aware` - старые эвристические пороги.
- Результаты steady-run содержат `model_source_status` и `source_gate_reasons`.
  Эти поля агрегируют source-gate ограничения активной цепочки расчета, поэтому
  published fallback closure не маскирует тот факт, что режимные карты,
  Zuber-Findlay drift-flux, boiling HTC и dryout/CHF ещё требуют полного
  первоисточника.

## Что нужно для снятия source-gate

- Локальный или институционально доступный полный текст первоисточника.
- Переписанные в `docs/formula_registry.md` формулы, коэффициенты, переменные,
  размерности и область применимости.
- Тесты на численные контрольные точки и граничные режимы.
- Проверка соглашений Darcy/Fanning, полного или фазового массового потока,
  определения опорных градиентов давления и ориентации участка.
