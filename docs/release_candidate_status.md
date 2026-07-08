# Release-candidate status

Дата стабилизационного прохода: 2026-07-06.
Документальный source-gate refresh: 2026-07-08.

Базовый коммит: `974c1e3 Improve boiling onset source tracing`.
Source-gate pipeline commit: `bda8cac Improve source-gate physics pipeline`.

## Решение по статусу

Текущее состояние можно рассматривать как source-gated release candidate:

- CO2 MathCAD-compatible ветка, общий CO2/NH3 solver, CoolProp-backed свойства,
  pressure-balance diagnostics, scenario matrix, qcrit scaffold и designer/API
  metadata transport находятся в runtime.
- `boiling_onset_model="mathcad_baseline"` остается default.
- `boiling_onset_model="ishkov_superheat"` является opt-in веткой с
  диссертационным источником и пользовательским `onset_superheat_k`.
- Published HTC, dryout/CHF, Wojtan/Taitel regime maps, Zuber-Findlay
  drift-flux coefficients, MSH и Friedel остаются `SOURCE_REQUIRED` или
  `SOURCE_CANDIDATE`; runtime-корреляции для них не released.
- Вторичные формульные кандидаты, найденные после основного release-candidate
  прохода, зафиксированы как `SECONDARY_FORMULA_CANDIDATE / NOT_RELEASED` в
  `docs/secondary_formula_candidates.md`; они не меняют runtime status и не
  снимают primary-source-only gates.
- `source_gate_pipeline.py`, `python -m source_gate_pipeline --pretty` и
  `/api/source-gates` теперь дают машинный план закрытия: `current_blocking_stage`,
  `release_criteria`, `release_basis`, `allowed_release_bases`, `audit_stage`,
  milestone groups, `parallel_work_orders` и `next_priorities`.

Документальный refresh от 2026-07-07 добавил явный dissertation/monograph
release path: такие источники могут закрывать gate только как named
`release_basis` с локальным full text, SHA256, page/equation audit, mapping в
`docs/formula_registry.md` и reference tests. Это не меняет runtime physics и
не снимает текущие guards без недостающих доказательств.

Endpoint refresh от 2026-07-08 (`docs/source_endpoint_refresh_2026-07-08.md`)
повторно проверил DOI redirects, Crossref, OpenAlex, publisher PDF/TDM routes,
EPFL landing pages и OSTI. Он подтвердил ту же картину: библиографические
записи доступны, но releasable full text для MSH, Friedel, Zuber-Findlay,
Taitel-Barnea-Dukler, WUT Part I/II, Kandlikar и Gungor-Winterton не получен;
Chen/OSTI остаётся `source_candidate`, а не released HTC runtime model.

Академический контекст синхронизирован с этим решением в
`docs/get_co2_academic_reference.md`, `docs/formula_registry.md`,
`docs/source_gate_manifest.json`, `docs/primary_source_inventory.md`,
`docs/physics_gap_matrix.md`, `docs/secondary_formula_candidates.md`,
`docs/milestone_closure_pipeline.md`, `docs/source_gate_unresolved_questions.md`,
`docs/source_endpoint_refresh_2026-07-08.md`,
`docs/chen_1962_formula_audit_2026-07-06.md`,
`docs/chen_1962_graph_digitization_2026-07-07.md`,
`docs/chen_1962_graph_review_2026-07-08.md`,
`docs/chen_1962_si_mapping_2026-07-07.md`,
`docs/chen_1962_validation_tables_2026-07-07.md`,
`docs/chen_1962_reference_value_audit_2026-07-08.md`,
`docs/chen_1962_scope_audit_2026-07-08.md`,
`docs/chen_1962_hand_calculation_2026-07-08.md`,
`docs/dissertation_formula_audit_2026-07-06.md`,
`docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md`,
`docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md`,
`docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md`,
`docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md`,
`docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md`,
`docs/wojtan_th2978_text_layer_audit_2026-07-08.md`,
`docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md`,
`docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md` и `plan.md`.

## Source-gate audit

Локальные full-text candidates теперь есть для Chen/OSTI 1962, EPFL TH2978 и
EPFL TH3337, но их решения в `docs/primary_source_inventory.md` остаются
`candidate_only`. Они дают audit guidance и page/equation maps, но не снимают
runtime gates. TH3337 `xdi`/`xde` dryout-boundary transcription is now locked
only as `boiling_heat_transfer.wojtan_th3337_candidate_dryout_boundaries`;
Chen 1962 now also has `docs/chen_1962_hand_calculation_2026-07-08.md` for
candidate direct Eqs. (9)/(17)/(18) and graph-to-SI arithmetic fixtures, and
`docs/chen_1962_reference_value_audit_2026-07-08.md` records that the audited
report pages do not print pointwise HTC reference cases.
`docs/chen_1962_scope_audit_2026-07-08.md` fixes the source-based Chen release
scope as vertical heated axial flow only and records that the current
horizontal evaporator is unsupported. The ledger is not a
pointwise report validation value and does not release the HTC adapter;
`docs/chen_1962_graph_review_2026-07-08.md` reviews Fig. 7/8 rendered graph
fits as candidate evidence but still leaves the `F/S`
uncertainty/authoritative-table decision open;
TH2978 text-layer status is recorded in
`docs/wojtan_th2978_text_layer_audit_2026-07-08.md`; follow-up rendered-page
audit in `docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md` locks
dryout-limit Eqs. (7.47)-(7.48) only as
`boiling_heat_transfer.wojtan_th2978_candidate_dryout_limits`, while Eq. (7.49),
WUT map transitions and Part II HTC equations remain unreleased;
TH3337 annular pressure-drop Eq. (7.4)/(7.5) is locked only as
`published_friction.moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m`;
TH3337 mist pressure-drop Eq. (7.13)-(7.17) is locked only as
`published_friction.moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m`;
TH3337 dryout pressure-drop interpolation Eq. (7.18) is locked only as
`published_friction.moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m`;
TH3337 slug/intermittent pressure-drop interpolation Eq. (7.6)/(7.12) is
locked only as
`published_friction.moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m`;
TH3337 stratified-wavy pressure-drop Eq. (7.9)-(7.11) is locked only as
`published_friction.moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m`.
Для MSH, Friedel, Zuber-Findlay, Taitel-Barnea-Dukler,
Wojtan/Thome journal Part I/II, Kandlikar и Gungor-Winterton локальный
релизный full text по-прежнему отсутствует. Tracked `sources/primary/README.md`
только описывает правила drop directory; PDF, сканы и извлеченный полный текст
не коммитятся.

Снятие любого `SOURCE_REQUIRED` gate по-прежнему требует:

- локального полного первоисточника под `sources/primary/`;
- записи SHA256, страниц/уравнений и решения аудита в
  `docs/primary_source_inventory.md`;
- обновления `docs/formula_registry.md` и `docs/source_gate_manifest.json`;
- reference-тестов до снятия runtime guard.

Secondary formula candidates могут использоваться только как audit guidance.
Они не заменяют локальный полный первоисточник, SHA256 inventory и reference
tests.

Текущий `python -m source_gate_pipeline --pretty` summary:

| Release state | Count |
| --- | ---: |
| `candidate_local_intake_ready` | 1 |
| `blocked_primary_source_required_secondary_available` | 3 |
| `blocked_primary_source_required_dissertation_candidate_available` | 2 |
| `blocked_primary_source_required` | 3 |

Первый приоритет pipeline - `HTC-CHEN-1962-SOURCE-CANDIDATE`: локальный OSTI PDF
принят и SHA256 совпадает; Eqs. (9), (17), (18) scan-verified, но
`audit_formulas_and_limits` остаётся `in_progress`, пока не закрыты release-grade
`F/S` interpolation, reviewed source-unit SI/graph-axis helpers, vertical-only geometry guards, selectable runtime adapter, reference tests и
release manifest.

## Verification

Release gate:

```powershell
pytest -q
```

Результат:

```text
252 passed in 515.07s (0:08:35)
```

Focused source-gate / secondary-candidate check after documentation update:

```powershell
pytest tests/test_formula_registry.py tests/test_source_gate_manifest.py -q
```

Результат:

```text
151 passed in 0.24s
```

Профиль медленных тестов:

```powershell
pytest -q --durations=25
```

Результат:

```text
252 passed in 515.29s (0:08:35)
```

Самые тяжелые проверки на этом проходе:

| Duration | Test |
| --- | --- |
| 63.58s | `tests/test_co2_result_fields.py::test_alternative_closure_models_change_branch_characteristics` |
| 41.99s | `tests/test_baseline_compatibility.py::test_experimental_regime_aware_preserves_legacy_regime_aware_numerics` |
| 32.10s | `tests/test_baseline_compatibility.py::test_closure_scientific_status_is_exposed_for_baseline_modes` |
| 31.60s | `tests/test_nh3_loop_solver.py::test_same_geometry_object_solves_co2_and_nh3_with_different_results` |
| 25.66s | `tests/test_co2_model_sweep.py::test_heat_load_sweep_convergence_map_matches_baseline` |
| 24.14s | `tests/test_co2_model_sweep.py::test_heat_load_sweep_preserves_expected_trends` |

## Follow-up test-speed plan

Не менять физику ради ускорения тестов. Отдельный test-speed pass должен:

- добавить или уточнить `slow`/`distributed` markers для вычислительно тяжелых
  steady/distributed сценариев, не меняя assertions;
- вынести повторяющиеся solve calls в безопасные fixtures только там, где это
  не скрывает побочные эффекты фасадов;
- сохранить полный `pytest -q` как release gate;
- использовать `pytest -q -m "not slow"` только как preflight, а не как замену
  полного прогона.
