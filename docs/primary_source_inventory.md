# Локальный инвентарь полных первоисточников

`docs/primary_source_inventory.md` фиксирует полный текст, который был реально
использован для снятия source-gate. Сами PDF, сканы и извлечённый полный текст хранятся локально в
`sources/primary/` и не коммитятся в репозиторий.

## Правила

- Каждая release-запись в `docs/source_gate_manifest.json` должна ссылаться на
  файл из `sources/primary/` через `local_full_text_ref`.
- Для файла обязателен `SHA256`, полная библиографическая ссылка, страницы или
  номера уравнений, дата аудита и решение: `audited_release`,
  `audited_rejected` или `candidate_only`.
- Формулы, коэффициенты, переменные, размерности и область применимости должны
  быть перенесены в `docs/formula_registry.md` до изменения runtime-кода.
- Численные reference-тесты и guard-removal/source-gate тесты должны проходить
  до смены решения manifest на `released`.
- DOI landing page, Crossref/OpenAlex/Unpaywall metadata, abstract, учебник,
  обзор, пересказ формулы или repository landing page без доступного
  full-text/`ORIGINAL` bitstream не являются достаточным основанием для release.

## Инвентарь

На 2026-07-06 локально добавлены полный OSTI PDF для Chen 1962 и два
openaccess EPFL doctoral-thesis PDF как `candidate_only`: это подтверждает
наличие полных текстов для дальнейшего аудита, но не выпускает runtime
HTC/pressure-drop/regime-корреляции. Все активные Checkpoint 5-6 журнальные
модели остаются `source_required`.

| Local file | SHA256 | Citation / model | Audited pages/equations | Decision | Notes |
| --- | --- | --- | --- | --- | --- |
| _none_ | _none_ | MSH/Friedel/Zuber-Findlay/WUT/TBD | _none_ | `source_required` | Полный локальный первоисточник ещё не предоставлен. |
| `sources/primary/chen_1962_osti_4636495.pdf` | `5DDE91B1FE38B2CE6E4977AEE2A25A61BBEDC83C5A7214802496754E4989017E` | `HTC-OSTI-1962-SOURCE-CANDIDATE`; J. C. Chen, "A correlation for boiling heat transfer to saturated fluids in convective flow", OSTI ID 4636495, DOI `10.2172/4636495` | Pages 4, 6, 10-19, 20-25, 32-35 reviewed in `docs/chen_1962_formula_audit_2026-07-06.md`, `docs/chen_1962_reference_value_audit_2026-07-08.md`, and `docs/chen_1962_scope_audit_2026-07-08.md`; confirms additive micro/macro structure, scan-verified Eqs. (9), (17), and (18), applicability conditions, graphical `F`/`S` functions, vertical-heated-flow-only scope, and quality limits; candidate Fig. 7/Fig. 8 digitization in `docs/chen_1962_graph_digitization_2026-07-07.md`; rendered graph review in `docs/chen_1962_graph_review_2026-07-08.md`; candidate SI mapping and graph-axis helpers in `docs/chen_1962_si_mapping_2026-07-07.md`; candidate direct and graph-to-SI arithmetic ledger in `docs/chen_1962_hand_calculation_2026-07-08.md`; Tables I/II condition and average-deviation context in `docs/chen_1962_validation_tables_2026-07-07.md`; reference-value audit found no printed pointwise HTC cases in the audited report pages. | `candidate_only` | Full text is locally available for audit; `boiling_heat_transfer.chen_1962_candidate_heat_transfer_coefficient_si`, `boiling_heat_transfer.chen_1962_candidate_inverse_martinelli_parameter`, `boiling_heat_transfer.chen_1962_candidate_two_phase_reynolds`, and `boiling_heat_transfer.chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si` lock down candidate unit/transcription, graph-axis, graph-to-SI composition checks and documented arithmetic, but `F`/`S` graph uncertainty, helper-to-runtime mapping and source/reference HTC tests are not release-grade. Tables I/II and Figs. 9/10 do not provide printed pointwise HTC reference cases; the current horizontal evaporator is outside the Chen source scope. |
| `sources/primary/wojtan_2004_epfl_th2978.pdf` | `0F17826CA107DD8744E8AFA914E11FB422D5BC551589ACE5492B04F5669075D5` | `DISS-WOJTAN-2004-EPFL-TH2978`; Leszek Wojtan, "Experimental and analytical investigation of void fraction and heat transfer during evaporation in horizontal tubes", EPFL thesis no. 2978, 2004, openaccess ORIGINAL bitstream `EPFL_TH2978.pdf` | Pages 1, 9-13, 172-184 reviewed in `docs/dissertation_formula_audit_2026-07-06.md`; `docs/wojtan_th2978_text_layer_audit_2026-07-08.md` confirms figure-level `hexp`/`xdi`/`xde`, heat-transfer coefficient and dryout labels; `docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md` locks rendered dryout-limit Eqs. (7.47)-(7.48) as candidate-only and records that Eq. (7.49) remains a separate map-update dependency. | `candidate_only` | Dissertation full text is locally available for audit guidance for void fraction, horizontal evaporation HTC, and Wojtan/Thome context; it does not release WUT journal gates, project dryout, CHF or HTC without rendered-page/OCR formula transcription, SI mapping, page/equation audit and reference tests. |
| `sources/primary/moreno_quiben_2005_epfl_th3337.pdf` | `B3FD9477D189C7720836C222BFD927BED34AD9E99CB4D1C188102423E26D1A77` | `DISS-MORENO-QUIBEN-2005-EPFL-TH3337`; Jesus Moreno Quiben, "Experimental and analytical study of two-phase pressure drops during evaporation in horizontal tubes", EPFL thesis no. 3337, 2005, openaccess ORIGINAL bitstream `EPFL_TH3337.pdf` | Pages 1, 5, 20-25, 53-66, 109-125, 146, 149, 152 reviewed in `docs/dissertation_formula_audit_2026-07-06.md`; confirms definitions, Friedel/MSH candidate formulas, WUT-map segmentation, annular pressure-drop Eqs. (7.1)-(7.5), stratified-wavy pressure-drop Eqs. (7.9)-(7.11), slug/intermittent pressure-drop Eqs. (7.6)/(7.12), mist pressure-drop Eqs. (7.13)-(7.17), dryout pressure-drop Eq. (7.18), dryout-boundary formulas `xdi`/`xde`, and bibliography links; candidate helpers in `published_friction.py` lock down TH3337 Friedel/MSH transcriptions and the annular/stratified-wavy/slug/mist/dryout pressure-drop branches documented in `docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md`, `docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md`, `docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md`, `docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md`, and `docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md`, while `docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md` and `boiling_heat_transfer.wojtan_th3337_candidate_dryout_boundaries` lock down WUT dryout-boundary guidance. | `candidate_only` | Dissertation full text is locally available for pressure-drop and WUT dryout-boundary audit guidance; `published_friction.moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m`, `published_friction.moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m`, `published_friction.moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m`, `published_friction.moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m`, and `published_friction.moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m` are only audit helpers and do not release friction, WUT Part I/Part II, dryout, CHF, or HTC gates without primary article audit or dissertation-specific formula release decision and tests. |

## Минимальный release-чеклист

1. Скопировать полный PDF/скан в `sources/primary/`.
2. Посчитать SHA256 локального файла и записать его в таблицу.
3. Выписать страницы, номера уравнений, коэффициенты, convention details и
   область применимости.
4. Обновить `docs/formula_registry.md`,
   `docs/source_audit_checkpoint_5_6.md` и
   `docs/source_gate_manifest.json`.
5. Добавить численные reference-тесты и тест, доказывающий корректное снятие
   guard/source-gate.
6. Только после этого подключать опубликованную модель в runtime.

## Release-basis fields

Every source-gate manifest entry must now carry explicit release metadata:
`release_basis`, `allowed_release_bases`, `audited_source_ref`,
`audited_equations`, `source_scope`, and `source_limitations`.

A dissertation, monograph, handbook, technical report, conference paper, or
archival scan can close a gate only as an explicit release basis with the same
evidence chain as a journal article: local full text under `sources/primary`,
SHA256 inventory, page/equation audit, SI and convention mapping, reference
tests, and a named runtime scope. Until that evidence is complete,
`audited_source_ref` and `audited_equations` stay empty and runtime guards stay
active.
