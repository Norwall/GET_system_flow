# Матрица физики, источников и незакрытых gap

Этот документ отделяет активную runtime-физику от source-gated кандидатов.
Он намеренно консервативен: библиографическая запись, DOI landing page,
abstract или чужой пересказ формулы не являются достаточным основанием для
переноса корреляции в расчёт.

Текущее стабилизированное состояние зафиксировано отдельно в
`docs/release_candidate_status.md`: это source-gated release candidate, а не
снятие `SOURCE_REQUIRED` ограничений.
Полный порядок закрытия оставшихся source-gates зафиксирован в
`docs/milestone_closure_pipeline.md`.

| Область | Runtime-статус | Источник | Gap / gate |
| --- | --- | --- | --- |
| Свойства насыщения CO2 из Mathcad | Released default для совместимой CO2-ветки | `CO2.xmcd`; табличный backend `MathcadCO2SaturationProperties` | Ограниченный диапазон таблиц; экстраполяция запрещена по умолчанию. |
| Свойства CO2/NH3 через CoolProp | Released optional backend | CoolProp High-Level API; страницы CoolProp CarbonDioxide и Ammonia; EOS-ссылки Span-Wagner и Gao-Wu-Bell-Lemmon в реестре | CoolProp валидирует свойства, но не валидирует гидродинамическую постановку ГЕТ. |
| REFPROP adapter | Optional adapter | NIST REFPROP / SRD 23 | Требует локальной лицензированной установки REFPROP; backend может быть недоступен. |
| Начало кипения baseline | Released default `mathcad_baseline` | `CO2.xmcd`; диссертационный баланс Ишкова | Сохраняет старые baseline-результаты и не содержит явный внешний перегрев. |
| Начало кипения с перегревом | Released opt-in `ishkov_superheat` | Диссертация Ишкова, eq. (3.3); `docs/formula_registry.md` | Использует пользовательский `onset_superheat_K` и итерационный перепад давления конденсатора; не является отдельной экспериментальной калибровкой. |
| Однофазное трение | Released alternatives | Darcy-Weisbach, laminar, Blasius, Colebrook-White, Churchill; записи `docs/formula_registry.md` | Legacy Mathcad blend остаётся compatibility/audit веткой. |
| Двухфазные потери давления | Released Lockhart-Martinelli/Chisholm/Zivi paths; MSH/Friedel остаются gated | Primary-source записи `docs/formula_registry.md` | MSH/Friedel не являются runtime-корреляциями до сверки полных формул, ограничений и convention details. |
| Режимные карты | Experimental local classifier или source-gated published placeholders | Wojtan-Ursenbacher-Thome и Taitel-Barnea-Dukler records | Published transition equations не реализуются без полного primary-source audit. |
| Flow-boiling HTC | Diagnostic heat-flux only; Chen 1962 записан как source-candidate | OSTI record/PDF для DOI `10.2172/4636495` | HTC, dryout и CHF не рассчитываются; нужна расшифровка уравнений, коэффициентов, границ применимости и reference tests. |
| Dryout/CHF | Not evaluated | Candidate sources tracked in source-gate docs | Численная несходимость solver не трактуется как dryout/CHF criterion. |
| Secondary formula candidates | Documentation-only audit layer | `docs/secondary_formula_candidates.md`; `docs/formula_registry.md`; `docs/source_gate_manifest.json` | Формулы из `fluids`, ACHP и `ht` помогают будущему аудиту, но имеют статус `SECONDARY_FORMULA_CANDIDATE / NOT_RELEASED` и не снимают `SOURCE_REQUIRED`. |
| Source-gate closure pipeline | Documentation/API planning layer, not physics | `source_gate_pipeline.py`; `/api/source-gates`; `docs/milestone_closure_pipeline.md`; `docs/source_gate_unresolved_questions.md` | Показывает `current_blocking_stage`, `release_criteria` и milestone groups, но не заменяет full-text audit, SI mapping и reference tests. |
| EPFL dissertation audit candidates | Local candidate-only audit guidance | `docs/dissertation_formula_audit_2026-07-06.md`; `docs/primary_source_inventory.md`; TH2978/TH3337 local files under `sources/primary` | TH3337 даёт candidate formulas для MSH/Friedel и dryout-boundary guidance; TH2978 требует OCR/manual audit. Эти кандидаты не release WUT/MSH/Friedel gates без отдельного решения и тестов. |
| Critical loads | Released как границы текущего steady solver | `critical_loads.py`; диссертационный предел `f=0` | Это не published CHF/dryout и не экспериментальная валидация. |
| Scenario/API/UI | Released metadata transport | Scenario schema, REST API, web UI, tests | UI показывает source-status и onset controls, но не заявляет validation. |
| Release-candidate snapshot | Source-gated release candidate | `docs/release_candidate_status.md`; полный `pytest -q` от 2026-07-06 | Статус подтверждает прохождение тестов и активные gates, но не добавляет новую физику. |

## Внешние источники, используемые или отслеживаемые

- CoolProp High-Level API: <https://coolprop.org/coolprop/HighLevelAPI.html>
- CoolProp CarbonDioxide: <https://coolprop.org/fluid_properties/fluids/CarbonDioxide.html>
- CoolProp Ammonia: <https://coolprop.org/fluid_properties/fluids/Ammonia.html>
- NIST REFPROP: <https://www.nist.gov/srd/refprop>
- Chen/OSTI source-candidate record: <https://www.osti.gov/biblio/4636495>
- Chen/OSTI full-text candidate: <https://www.osti.gov/servlets/purl/4636495>
- Source-gate closure pipeline: `source_gate_pipeline.py`,
  `docs/milestone_closure_pipeline.md`, `/api/source-gates`
- Candidate-only formula audits: `docs/chen_1962_formula_audit_2026-07-06.md`,
  `docs/dissertation_formula_audit_2026-07-06.md`
- Secondary formula candidate registry: `docs/secondary_formula_candidates.md`
- Secondary formula source families tracked there: `fluids`, ACHP and `ht`
  documentation pages with cited primary records.

## Правило обновления

Любая новая runtime-корреляция должна обновлять одновременно:

- `docs/formula_registry.md`;
- `docs/source_gate_manifest.json`, если модель была source-gated;
- `docs/primary_source_inventory.md`, если release основан на локальном полном
  первоисточнике;
- численные reference-тесты;
- пользовательскую документацию и поля результата, если меняется API.
