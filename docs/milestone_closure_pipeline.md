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
`docs/source_gate_unresolved_questions.md`.
Each source-gate object reports `current_blocking_stage` and structured
`release_criteria` so UI/API clients can show the exact missing proof without
parsing this Markdown file.

## Current groups

| Group | Source ids | Next action | Required proof |
| --- | --- | --- | --- |
| `local_candidate_audit` | `HTC-CHEN-1962-SOURCE-CANDIDATE` | Finish local Chen 1962 formula audit: digitize `F/S`, manually verify Eqs. (9), (17), (18), map units to SI, and add reference HTC tests. | Audited equations, applicability limits, SI mapping, reference tests and `released` manifest decision. |
| `secondary_guided_primary_required` | `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE`, `TP-FRIEDEL-1979-SOURCE-GATE`, `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` | Use secondary formulas only as audit guidance; acquire the full primary text or archival scan before implementation. | Local primary full text under `sources/primary`, SHA256 inventory, convention audit and reference tests. |
| `dissertation_guided_primary_required` | `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE`, `HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE` | Use dissertation pages as audit guidance; obtain the target journal article or record a dissertation-specific release path. | Explicit release decision, page/equation audit, applicability limits and reference tests. |
| `primary_acquisition_required` | `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE`, `HTC-KANDLIKAR-1990-SOURCE-CANDIDATE`, `HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE` | Acquire authorized primary full text and record local intake before formula transcription. | Local primary full text and inventory row. |

## Closure sequence

1. Acquire or confirm the full primary text.
   - Put PDFs/scans under `sources/primary`.
   - Record SHA256, citation, audited pages/equations and decision in
     `docs/primary_source_inventory.md`.
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
   - Run focused source-gate tests and the release verification suite.

## Per-source work orders

| Source id | Current evidence | Blocking question | Minimum next artifact |
| --- | --- | --- | --- |
| `HTC-CHEN-1962-SOURCE-CANDIDATE` | OSTI PDF is local; page/equation audit exists in `docs/chen_1962_formula_audit_2026-07-06.md`. | `F/S` are graphical, formula OCR is degraded, SI mapping and reference HTC tests are incomplete. | Digitized `F/S` table plus manual Eq. (9)/(17)/(18) verification notes. |
| `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` | DOI/publisher metadata, secondary candidate and Moreno Quiben dissertation guidance. | Full MSH 1986 article is missing; Darcy/Fanning and mass-flux conventions are not primary-audited. | Local full article or authorized TDM text with SHA256 inventory. |
| `TP-FRIEDEL-1979-SOURCE-GATE` | Secondary candidate and Moreno Quiben dissertation guidance; bibliography points to Friedel 1979/1980. | Archival Friedel primary paper/scan is missing. | Locate archival full text for Friedel 1979 paper E2 or 3R International record. |
| `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE` | DOI and ASME PDF endpoint are known; open access failed with HTTP 403. | Full ASME article is missing, so `C0`, weighted drift velocity and averaging conventions are unaudited. | Local full article with SHA256 inventory. |
| `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE` | EPFL thesis TH2978 is local but partially custom-encoded; journal record is metadata-only. | WUT Part I transition equations and dryout boundaries are not released. | Target article full text or OCR/manual dissertation release decision with reference boundary tests. |
| `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` | DOI/Wiley record and secondary horizontal Taitel-Dukler guidance. | Vertical upflow transition equations are not audited from the full 1980 paper. | Local full article with vertical transition page/equation audit. |
| `HTC-KANDLIKAR-1990-SOURCE-CANDIDATE` | DOI and ASME PDF endpoint are known; open access failed with HTTP 403. | Correlation terms, boiling-number definitions, fluid factors and applicability are unaudited. | Local full article with formula registry update and HTC reference tests. |
| `HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE` | DOI and Elsevier TDM endpoint are known; open access failed with HTTP 400. | Enhancement/suppression factors, nucleate-boiling base equation and applicability are unaudited. | Local full article with formula registry update and HTC reference tests. |
| `HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE` | EPFL thesis TH2978 is local but partially custom-encoded; journal record is metadata-only. | Heat-transfer, dryout and mist-flow equations are not source-audited; dependency on Part I map is unresolved. | Target article full text or OCR/manual dissertation release decision plus tests that Part II refuses to run without Part I inputs. |

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
