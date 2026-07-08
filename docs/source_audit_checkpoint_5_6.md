# Аудит источников Checkpoint 5-6

Дата проверки: 2026-07-03.
Повторная проверка политики: 2026-07-04.
Контрольная endpoint-проверка: 2026-07-05.
Дополнительный secondary-formula context: 2026-07-06.
Open-web проверка доступности: `docs/source_audit_open_web_2026-07-05.md`
(предыдущий проход: `docs/source_audit_open_web_2026-07-04.md`).
Структурированный manifest: `docs/source_gate_manifest.json`.
Source-gate manifest/pipeline refresh: 2026-07-07.

Цель проверки - отделить библиографически подтвержденные published-модели от
формул, которые можно переносить в расчет только после сверки полного
первоисточника. Этот документ является академическим ограничителем: наличие DOI
или landing page не считается достаточным основанием для переноса коэффициентов,
transition equations или областей применимости в код.

Обновление 2026-07-07 закрепляет явный release-basis слой:
`docs/source_gate_manifest.json`, `source_gate_pipeline.py` и `/api/source-gates`
показывают `release_basis`, `allowed_release_bases`, `audited_source_ref`,
`audited_equations`, `source_scope`, `source_limitations`, `audit_stage` и
`parallel_work_orders`. Диссертация, монография, справочник, technical report или
архивный скан могут быть основанием release только как явно выбранный
`release_basis` с локальным полным текстом, page/equation-level audit,
ограничениями применимости и reference tests; это не автоматическая замена
целевой journal/conference статьи.

## Политика проверки 2026-07-04

Для снятия source-gate по Checkpoint 5-6 требуется полный первоисточник:
publisher PDF, авторская копия, скан доклада или институционально доступный
полный текст. Crossref, DOI landing page, abstract, цитирование в обзоре,
учебник или пересказ формулы не являются достаточным основанием для подключения
модели как `published`.

Если полный первоисточник недоступен, код должен сохранять `SOURCE_REQUIRED`
или `source_required`, а runtime-результат не должен выглядеть как полностью
source-complete published-модель.

Дополнение open-web проверки 2026-07-04: repository landing page без
доступного full-text/`ORIGINAL` bitstream не снимает source-gate, даже если
Unpaywall/OpenAlex помечают запись как green OA. Единственный найденный
открытый PDF-кандидат, OSTI `10.2172/4636495`, не относится к уже выбранным
MSH/Friedel/Zuber-Findlay/Taitel/Wojtan source-gate моделям и требует
отдельного аудита применимости перед любым подключением.

Контрольная endpoint-проверка 2026-07-05 не сняла ни один source-gate:
Elsevier TDM endpoints для MSH, Wojtan Part I/II и Gungor-Winterton вернули
HTTP 400 без авторизованного API-контекста; Wiley PDF для Taitel-Barnea-Dukler
и ASME PDF для Zuber-Findlay/Kandlikar вернули HTTP 403; EPFL DSpace API для
Wojtan Part I/II по-прежнему показывает только `LICENSE` bundle без
`ORIGINAL`/full-text bitstream. OSTI `10.2172/4636495` снова подтвердился как
доступный `application/pdf`, `Content-Length 1533908`, но остаётся
`source_candidate`, а не released HTC-моделью.

## Локальный intake полных первоисточников

Следующий путь снятия gate — не повторное использование metadata, а локальный
аудит полного текста. Полные PDF, сканы или извлечённые полные тексты должны
размещаться в `sources/primary/`; эта папка предназначена для локальной рабочей
evidence-базы и не коммитится, кроме `sources/primary/README.md`.

Каждый локальный источник, используемый для release, должен быть занесён в
`docs/primary_source_inventory.md` с именем файла, SHA256, библиографической
записью, страницами/уравнениями, аудированными convention details и решением
аудита. Перед снятием gate manifest также должен заполнить `release_basis`,
`audited_source_ref`, `audited_equations`, `source_scope` и
`source_limitations`. Только после этого допустимы обновления
`docs/formula_registry.md`, `docs/source_gate_manifest.json`, численные
reference-тесты и снятие guard в runtime-коде.

## Вторичные формульные кандидаты 2026-07-06

Если полный первоисточник не найден, вторичная формула может быть занесена
только как `SECONDARY_FORMULA_CANDIDATE / NOT_RELEASED`. Такой статус
используется для audit guidance и не является release-доказательством.

Текущий secondary pass оформлен в `docs/secondary_formula_candidates.md` и
связан с `docs/formula_registry.md` / `docs/source_gate_manifest.json`.
Найдены вторичные формульные кандидаты для MSH, Friedel, Zivi, ACHP
acceleration pressure drop, Shah evaporation, Chen-Bennett, Liu-Winterton и
Taitel-Dukler 1976 horizontal map. При этом:

- MSH/Friedel guard-функции остаются активными;
- Taitel-Dukler 1976 horizontal map не заменяет вертикальный
  Taitel-Barnea-Dukler 1980 gate;
- Shah/Chen-Bennett/Liu-Winterton не являются dryout/CHF prediction;
- runtime-код не меняется и ни один `SOURCE_REQUIRED` gate не снимается.

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
| `HTC-CHEN-1962-SOURCE-CANDIDATE` | `boiling_heat_transfer.chen_1962_source_candidate` | Оставить `SOURCE_CANDIDATE / NOT_RELEASED`. OSTI полный текст найден; Eqs. (9), (17), (18) scan-verified, Fig. 7/8 `F/S` имеют candidate-only digitization and rendered graph review in `docs/chen_1962_graph_review_2026-07-08.md`, source-unit SI mapping, graph-axis, graph-to-SI helpers and hand-calculation ledger in `docs/chen_1962_hand_calculation_2026-07-08.md`, но accepted release interpolation/authoritative table, reviewed helper-to-runtime mapping, ограничения применимости и source/reference tests не аудированы для runtime HTC/dryout/CHF. |

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
- Chen 1962 / OSTI `10.2172/4636495` учитывается как отдельный
  `source_candidate`: metadata и candidate helper
  `boiling_heat_transfer.chen_1962_candidate_heat_transfer_coefficient_si`
  доступны для аудита переноса формул; `docs/chen_1962_hand_calculation_2026-07-08.md`
  фиксирует candidate-only арифметику прямого и graph-to-SI расчёта, но расчётные
  runtime HTC, dryout и CHF correlation остаются не выпущенными.
- Moreno Quiben TH3337 annular pressure-drop Eq. (7.4)/(7.5) теперь
  зафиксирован только как candidate-only helper
  `published_friction.moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m`
  и audit-документ
  `docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md`; это не
  снимает MSH/Friedel/WUT/HTC gates.
- Moreno Quiben TH3337 mist pressure-drop Eq. (7.13)-(7.17) теперь
  зафиксирован только как candidate-only helper
  `published_friction.moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m`
  и audit-документ
  `docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md`; это не
  снимает MSH/Friedel/WUT/HTC gates.
- Moreno Quiben TH3337 dryout pressure-drop interpolation Eq. (7.18) теперь
  зафиксирована только как candidate-only helper
  `published_friction.moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m`
  и audit-документ
  `docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md`; это не
  снимает MSH/Friedel/WUT/HTC gates.
- Moreno Quiben TH3337 slug/intermittent pressure-drop interpolation
  Eq. (7.6)/(7.12) теперь зафиксирована только как candidate-only helper
  `published_friction.moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m`
  и audit-документ
  `docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md`; это не
  снимает MSH/Friedel/WUT/HTC gates.
- Moreno Quiben TH3337 stratified-wavy pressure-drop Eq. (7.9)-(7.11) теперь
  зафиксирована только как candidate-only helper
  `published_friction.moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m`
  и audit-документ
  `docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md`; это не
  снимает MSH/Friedel/WUT/HTC gates.
- `docs/secondary_formula_candidates.md` добавляет только context для будущего
  аудита. Записи `SECONDARY_FORMULA_CANDIDATE / NOT_RELEASED` не считаются
  достаточным основанием для снятия guard.

## Что нужно для снятия source-gate

- Локальный или институционально доступный полный текст первоисточника.
- Переписанные в `docs/formula_registry.md` формулы, коэффициенты, переменные,
  размерности и область применимости.
- Тесты на численные контрольные точки и граничные режимы.
- Проверка соглашений Darcy/Fanning, полного или фазового массового потока,
  определения опорных градиентов давления и ориентации участка.
