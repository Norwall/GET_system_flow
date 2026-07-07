# Release-candidate status

Дата стабилизационного прохода: 2026-07-06.

Базовый коммит: `974c1e3 Improve boiling onset source tracing`.

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

Академический контекст синхронизирован с этим решением в
`docs/get_co2_academic_reference.md`, `docs/physics_gap_matrix.md`,
`docs/secondary_formula_candidates.md`, `docs/milestone_closure_pipeline.md`
`docs/source_gate_unresolved_questions.md` и `plan.md`.

## Source-gate audit

Локальных полных первоисточников для снятия gates в этом проходе нет.
Tracked `sources/primary/README.md` только описывает правила drop directory;
PDF, сканы и извлеченный полный текст не коммитятся.

Снятие любого `SOURCE_REQUIRED` gate по-прежнему требует:

- локального полного первоисточника под `sources/primary/`;
- записи SHA256, страниц/уравнений и решения аудита в
  `docs/primary_source_inventory.md`;
- обновления `docs/formula_registry.md` и `docs/source_gate_manifest.json`;
- reference-тестов до снятия runtime guard.

Secondary formula candidates могут использоваться только как audit guidance.
Они не заменяют локальный полный первоисточник, SHA256 inventory и reference
tests.

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
