# Milestone closure pipeline

This document is the working pipeline for closing the remaining source-gated
physics milestones. It is intentionally conservative: no runtime model is
released until the primary-source evidence, formula audit, implementation and
reference tests are all complete.

Authoritative machine-readable status is produced by:

```powershell
python -m source_gate_pipeline --pretty
```

The same report is exposed through `/api/source-gates`.
The source-specific unresolved formula, scope and test questions are tracked in
`docs/source_gate_unresolved_questions.md`. The WUT dryout-boundary candidate
transcription from TH3337 is separately locked in
`docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md` and remains
candidate-only. The direct TH2978 rendered dryout-limit transcription
Eqs. (7.47)-(7.48) is separately locked in
`docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md` and also remains
candidate-only. The Moreno Quiben TH3337 annular pressure-drop branch
Eq. (7.4)/(7.5) is separately locked in
`docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md` and
also remains candidate-only. The Moreno Quiben TH3337 mist pressure-drop branch
Eq. (7.13)-(7.17) is separately locked in
`docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md` and also
remains candidate-only.
The Moreno Quiben TH3337 dryout pressure-drop interpolation Eq. (7.18) is
separately locked in
`docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md` and also
remains candidate-only.
The Moreno Quiben TH3337 slug/intermittent pressure-drop interpolation
Eq. (7.6)/(7.12) is separately locked in
`docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md` and also
remains candidate-only.
The Moreno Quiben TH3337 stratified-wavy pressure-drop branch Eq. (7.9)-(7.11)
is separately locked in
`docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md`
and also remains candidate-only.
The latest official-route refresh is
`docs/source_endpoint_refresh_2026-07-08.md`; it rechecked DOI redirects,
Crossref, OpenAlex, publisher PDF/TDM endpoints, EPFL landing pages and OSTI,
and left all acquisition-blocked gates closed.
Each source-gate object reports `current_blocking_stage` and structured
`release_criteria` so UI/API clients can show the exact missing proof without
parsing this Markdown file.
Each object also reports `release_basis`, `allowed_release_bases`,
`audited_source_ref`, `audited_equations`, `source_scope`,
`source_limitations`, and `audit_stage`. These fields make dissertation,
monograph, handbook, technical-report, or archival-scan release paths explicit
instead of silently treating them as journal-article evidence.
The pipeline also fails a declared `released` entry closed unless the local
source intake is inventoried as `audited_release`, SHA256 matches, and the
manifest records `release_basis`, `audited_source_ref`, `audited_equations`,
`source_scope`, `source_limitations`, and release tests.
The top-level report includes `parallel_work_orders` for the full open front;
`next_priorities` is only a sorted view and must not be interpreted as the only
work queue.

## Accepted release bases

The default target remains the source named in each gate, usually a journal
article. A dissertation, monograph, handbook, technical report, conference
paper, or archival scan may close a gate only when it is a full locally
auditable source with SHA256 inventory, page/equation audit, formula registry
mapping, runtime tests, and an explicit `release_basis`. If that basis differs
from the original article, the runtime adapter and docs must name the released
model accordingly.

## Current groups

| Group | Source ids | Next action | Required proof |
| --- | --- | --- | --- |
| `local_candidate_audit` | `HTC-CHEN-1962-SOURCE-CANDIDATE` | Finish local Chen 1962 formula audit: decide whether `docs/chen_1962_graph_review_2026-07-08.md`, source-unit SI/graph-axis helpers and `docs/chen_1962_hand_calculation_2026-07-08.md` are acceptable release proof after `docs/chen_1962_reference_value_audit_2026-07-08.md` found no printed pointwise HTC case in the report; use `docs/chen_1962_scope_audit_2026-07-08.md` to keep any released adapter vertical-heated-flow-only, then add or approve source/reference HTC tests. | Accepted graphical-function interpolation or authoritative table, reviewed helper-to-runtime mapping, vertical-only geometry guards, reference tests and `released` manifest decision. |
| `secondary_guided_primary_required` | `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE`, `TP-FRIEDEL-1979-SOURCE-GATE`, `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` | Use secondary formulas only as audit guidance; acquire the full primary text or archival scan before implementation. | Local primary full text under `sources/primary`, SHA256 inventory, convention audit and reference tests. |
| `dissertation_guided_primary_required` | `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE`, `HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE` | Use dissertation pages as audit guidance; `docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md` candidate-locks TH2978 dryout-limit Eqs. (7.47)-(7.48), but Eq. (7.49), map transitions and Part II HTC still need audit; obtain the target journal article or record a dissertation-specific release path. | Explicit release decision, rendered-page/OCR page/equation audit, applicability limits and reference tests. |
| `primary_acquisition_required` | `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE`, `HTC-KANDLIKAR-1990-SOURCE-CANDIDATE`, `HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE` | Acquire authorized primary full text and record local intake before formula transcription. | Local primary full text and inventory row. |

## Closure sequence

1. Acquire or confirm the full primary text.
   - Put PDFs/scans under `sources/primary`.
   - Record SHA256, citation, audited pages/equations and decision in
     `docs/primary_source_inventory.md`.
   - Record the selected `release_basis` and the exact `audited_source_ref`.
   - Repository landing pages, DOI metadata, abstracts, reviews and secondary
     formula transcriptions are not release evidence.

2. Audit formulas and definitions.
   - Transcribe exact equations, constants, exponents and variable definitions.
   - Record property evaluation points, units, friction-factor convention,
     quality/mass-flux convention and applicability limits.
   - Close the matching question in `docs/source_gate_unresolved_questions.md`
     with direct evidence before changing runtime behavior.
   - For graphical functions such as Chen 1962 `F/S`, digitize or obtain an
     authoritative table before any numeric runtime implementation.

3. Map audited source variables to project state variables.
   - Update `docs/formula_registry.md`.
   - Update `docs/source_gate_manifest.json`.
   - Keep dryout, CHF, HTC, pressure-drop and regime-map scopes separate.

4. Implement only after the audit is complete.
   - Runtime code must fail closed while source status is `source_required` or
     `source_candidate`.
   - Guard removal requires a manifest decision change and tests proving the
     change.

5. Add reference tests.
   - Include at least one source-based numeric reference point or a documented
     hand calculation.
   - Add convention tests for Darcy/Fanning, mass flux, property evaluation and
     domain limits where relevant.
   - Add API/result-field tests if new diagnostics or selectable models are
     exposed.

6. Release the gate.
   - Set `evidence_status="audited"` and `decision="released"` only after docs,
     implementation and tests agree.
   - Fill `audited_source_ref` and `audited_equations`; leave them empty while
     the source is only `source_required` or `source_candidate`.
   - Run focused source-gate tests and the release verification suite.

## Per-source work orders

| Source id | Current evidence | Blocking question | Minimum next artifact |
| --- | --- | --- | --- |
| `HTC-CHEN-1962-SOURCE-CANDIDATE` | OSTI PDF is local; page/equation audit exists in `docs/chen_1962_formula_audit_2026-07-06.md`; Eqs. (9), (17), and (18) are scan-verified; candidate graph digitization exists in `docs/chen_1962_graph_digitization_2026-07-07.md` and rendered graph review exists in `docs/chen_1962_graph_review_2026-07-08.md`; candidate SI mapping, graph-axis helpers, and graph-to-SI composition exist in `docs/chen_1962_si_mapping_2026-07-07.md`; direct and graph-to-SI arithmetic fixtures are documented in `docs/chen_1962_hand_calculation_2026-07-08.md`; Tables I/II are transcribed in `docs/chen_1962_validation_tables_2026-07-07.md`; printed reference-value audit exists in `docs/chen_1962_reference_value_audit_2026-07-08.md`; vertical-only applicability/geometry scope is fixed in `docs/chen_1962_scope_audit_2026-07-08.md`. | `F/S` graph uncertainty and SI/axis/composition helper-to-runtime mapping are not yet release-grade runtime code; the hand-calculation ledger is candidate-only unless explicitly accepted as release proof; Tables I/II and Figs. 9/10 provide aggregate or plotted validation context, not printed pointwise HTC references; the current horizontal evaporator is outside Chen source scope unless a separate non-source extrapolation is explicitly accepted. | Accepted `F/S` interpolation or authoritative table plus SI/axis/composition helper-to-runtime mapping, vertical-only geometry guards and source-based or approved hand-calculation HTC reference tests. |
| `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` | DOI/publisher metadata, secondary candidate and Moreno Quiben dissertation guidance. TH3337 annular pressure-drop Eq. (7.4)/(7.5), stratified-wavy pressure-drop Eq. (7.9)-(7.11), slug/intermittent pressure-drop Eq. (7.6)/(7.12), mist pressure-drop Eq. (7.13)-(7.17), and dryout pressure-drop interpolation Eq. (7.18) are locked separately in `docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md`, `docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md`, `docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md`, `docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md`, `docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md`, `published_friction.moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m`, `published_friction.moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m`, `published_friction.moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m`, `published_friction.moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m`, and `published_friction.moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m`. | Full MSH 1986 article is missing; Darcy/Fanning and mass-flux conventions are not primary-audited. TH3337 branch guidance is not the MSH primary formula. | Local full article or authorized TDM text with SHA256 inventory. |
| `TP-FRIEDEL-1979-SOURCE-GATE` | Secondary candidate and Moreno Quiben dissertation guidance; bibliography points to Friedel 1979/1980. | Archival Friedel primary paper/scan is missing. | Locate archival full text for Friedel 1979 paper E2 or 3R International record. |
| `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE` | DOI and ASME PDF endpoint are known; open access failed with HTTP 403. | Full ASME article is missing, so `C0`, weighted drift velocity and averaging conventions are unaudited. | Local full article with SHA256 inventory. |
| `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE` | EPFL thesis TH2978 is local but partially custom-encoded; `docs/wojtan_th2978_text_layer_audit_2026-07-08.md` records figure-level dryout/HTC labels, and `docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md` candidate-locks dryout-limit Eqs. (7.47)-(7.48); journal record is metadata-only. | WUT Part I transition equations, Eq. (7.49) and release-grade dryout-boundary tests are not released. | Target article full text or OCR/manual dissertation release decision with reference boundary tests. |
| `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` | DOI/Wiley record and secondary horizontal Taitel-Dukler guidance. | Vertical upflow transition equations are not audited from the full 1980 paper. | Local full article with vertical transition page/equation audit. |
| `HTC-KANDLIKAR-1990-SOURCE-CANDIDATE` | DOI and ASME PDF endpoint are known; open access failed with HTTP 403. | Correlation terms, boiling-number definitions, fluid factors and applicability are unaudited. | Local full article with formula registry update and HTC reference tests. |
| `HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE` | DOI and Elsevier TDM endpoint are known; open access failed with HTTP 400. | Enhancement/suppression factors, nucleate-boiling base equation and applicability are unaudited. | Local full article with formula registry update and HTC reference tests. |
| `HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE` | EPFL thesis TH2978 is local but partially custom-encoded; `docs/wojtan_th2978_text_layer_audit_2026-07-08.md` records figure-level `hexp`/`xdi`/`xde`, HTC axes and dryout labels; `docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md` and `boiling_heat_transfer.wojtan_th2978_candidate_dryout_limits` candidate-lock TH2978 dryout-limit Eqs. (7.47)-(7.48); journal record is metadata-only. TH3337 `xdi/xde` dryout-boundary transcription is locked as candidate-only in `docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md` and `boiling_heat_transfer.wojtan_th3337_candidate_dryout_boundaries`; TH3337 annular/stratified-wavy/slug/mist/dryout pressure-drop guidance is locked separately in `docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md`, `docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md`, `docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md`, `docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md`, and `docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md`. | Part II stratified-wavy, dryout and mist-flow heat-transfer equations are not source-audited; dependency on Part I map is unresolved. Dryout-limit and pressure-drop guidance are not Part II HTC. | Target article full text or OCR/manual dissertation release decision plus tests that Part II refuses to run without Part I inputs. |

## Verification gates

Focused source-gate verification:

```powershell
pytest tests\test_source_gate_pipeline.py tests\test_source_gate_manifest.py -q
```

Runtime/API preflight:

```powershell
pytest -q -m "not slow" --durations=10
```

Full release verification remains:

```powershell
pytest -q
```
