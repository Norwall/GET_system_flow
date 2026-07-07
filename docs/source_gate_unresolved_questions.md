# Source-gate unresolved questions register

This register turns the remaining scientific and source-audit unknowns into
release criteria. It complements `docs/milestone_closure_pipeline.md` and is
not a release artifact by itself: every open question below still requires
primary-source evidence, updates to `docs/primary_source_inventory.md`,
`docs/formula_registry.md`, `docs/source_gate_manifest.json`, implementation
work where applicable, and tests.

Official metadata was rechecked on 2026-07-06 through Crossref records, DOI
publisher resources, OSTI, and local dissertation candidates already recorded
in `docs/primary_source_inventory.md`. Crossref/DOI metadata, repository
landing pages, abstracts, reviews, monographs, handbooks and library formula
transcriptions remain guidance only unless the full primary text is locally
audited.

## Questions closed by current evidence

| Item | Evidence now fixed | Remaining limit |
| --- | --- | --- |
| `HTC-CHEN-1962-SOURCE-CANDIDATE` | OSTI record `10.2172/4636495` and local PDF `sources/primary/chen_1962_osti_4636495.pdf`; page audit started in `docs/chen_1962_formula_audit_2026-07-06.md`; Eq. (9) and Eq. (18) structures are text-layer verified but still need visual scan confirmation. | Runtime HTC remains blocked until graphical `F/S`, Eq. (17), units, scope and reference values are audited. |
| `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` | Crossref confirms DOI `10.1016/0255-2701(86)80008-3`, Chemical Engineering and Processing 20(6), 297-308, and Elsevier TDM routes. Moreno Quiben TH3337 provides candidate text-layer formulas in Eqs. (4.53)-(4.56). | Full article text is still missing locally; formula conventions remain primary-unaudited. |
| `TP-FRIEDEL-1979-SOURCE-GATE` | MSH Crossref reference list identifies Friedel, 3R International, volume 18, issue 7, page 485, 1979, article title matching the gate. Moreno Quiben TH3337 provides candidate text-layer formulas in Eqs. (4.40)-(4.47). | No DOI, publisher endpoint, or archival scan has been verified; formulas remain primary-unaudited. |
| `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE` | Crossref confirms DOI `10.1115/1.3689137`, Journal of Heat Transfer 87(4), 453-468, and ASME PDF route. | ASME full text is not locally available; `C0` and drift velocity definitions remain unaudited. |
| `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE` | Crossref confirms DOI `10.1016/j.ijheatmasstransfer.2004.12.012`, IJHMT 48(14), 2955-2969, and Elsevier TDM routes; EPFL thesis TH2978 is local guidance. | Journal article full text is missing; thesis extraction is incomplete and cannot release the gate without a separate decision. |
| `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` | Crossref confirms DOI `10.1002/aic.690260304`, AIChE Journal 26(3), 345-354, and Wiley PDF/TDM routes. | Wiley full text is not locally available; vertical transition criteria remain unaudited. |
| `HTC-KANDLIKAR-1990-SOURCE-CANDIDATE` | Crossref confirms DOI `10.1115/1.2910348`, Journal of Heat Transfer 112(1), 219-228, and ASME PDF route. | ASME full text is not locally available; factors, fluid constants and applicability remain unaudited. |
| `HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE` | Crossref confirms DOI `10.1016/0017-9310(86)90205-X`, IJHMT 29(3), 351-358, and Elsevier TDM routes. | Elsevier full text is not locally available; enhancement/suppression terms remain unaudited. |
| `HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE` | Crossref confirms DOI `10.1016/j.ijheatmasstransfer.2004.12.013`, IJHMT 48(14), 2970-2985, and Elsevier TDM routes; EPFL thesis TH2978 is local guidance. Moreno Quiben TH3337 provides candidate dryout-boundary formulas `xdi`/`xde` from Wojtan et al. | Journal article full text is missing; Part II also depends on a released Part I regime-map path and audited heat-transfer equations. |

## Open release questions

| Source id | Formula and scope questions to close | Closing evidence | Required test proof |
| --- | --- | --- | --- |
| `HTC-CHEN-1962-SOURCE-CANDIDATE` | What are the authoritative numeric forms of `F(X_tt)` and `S(Re_tp)` from Figs. 7 and 8? What is the exact Eq. (17) transcription after visual scan audit? Which vertical-flow limits and quality limits can be mapped to the current horizontal/vertical loop geometry? | Manual audit notes or digitized tables tied to `sources/primary/chen_1962_osti_4636495.pdf`, visual confirmation of Eq. (9) and Eq. (18), SI variable mapping in `docs/formula_registry.md`, and explicit HTC-only release scope in `docs/source_gate_manifest.json`. | Reference HTC values from the report or hand calculation; unsupported-geometry/domain tests; regression proving dryout and CHF are not inferred from this HTC source. |
| `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` | TH3337 gives the candidate interpolation `(dp/dz)_frict = F*(1-x)^(1/3) + B*x^3`, `F = A + 2*(B-A)*x`, with all-liquid/all-gas gradients `A` and `B`. Does the MSH 1986 primary article use the same definitions, Darcy/Fanning convention, and total/phase mass-flux convention? | Local full article or authorized TDM text under `sources/primary` with SHA256 inventory and page/equation audit. | Numeric reference pressure-drop test; Darcy/Fanning convention test; guard-removal test tied to registry update. |
| `TP-FRIEDEL-1979-SOURCE-GATE` | TH3337 gives candidate Eqs. (4.40)-(4.47), including `phi_f0^2 = E + 3.24*F*H/(Fr_H^0.045*We_L^0.035)`. What is the archival Friedel formula source: European Two-Phase Flow Group paper E2, 3R International article, or both? Are the exponents, property evaluation rules and applicability limits identical in the primary? | Archival full text or scan for Friedel 1979/1980, with bibliographic decision recorded in `docs/primary_source_inventory.md`. | Reference pressure-drop multiplier test; high viscosity-ratio/domain rejection tests; guard-removal test. |
| `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE` | Which drift-flux equation, distribution parameter `C0`, weighted drift velocity and averaging definitions are used for the supported vertical-riser scope? | Local ASME full article with page/equation audit separating general drift-flux theory from regime-specific closures. | Void-fraction bounds and limiting-quality tests; at least one audited regime reference point; test that experimental drift-flux coefficients are not reused. |
| `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE` | What are the Part I transition equations, dryout boundary inputs, refrigerant/diameter/mass-flux ranges and out-of-range behavior? Can TH2978 be released independently, or is the journal article mandatory? | Target article full text or an explicit dissertation-specific release decision after OCR/manual audit of TH2978. | Boundary reference tests across implemented transitions; unknown/out-of-range tests; placeholder-removal test. |
| `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` | What are the vertical bubbly, slug, churn and annular transition equations and variable definitions? How are superficial velocities, surface tension and diameter used? | Local Wiley/AIChE full article or authorized text with vertical transition page/equation audit. | Classification reference tests for each regime and boundary; dimensional consistency tests; placeholder-removal test. |
| `HTC-KANDLIKAR-1990-SOURCE-CANDIDATE` | What are the exact saturated flow-boiling factors, boiling-number definition, fluid-dependent constants, convective/nucleate branches and horizontal/vertical applicability limits? | Local ASME full article with formula registry update and explicit wall/input requirements. | Source-based HTC reference values; missing wall-boundary validation tests; no dryout inference from convergence. |
| `HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE` | What are the exact enhancement and suppression factors, nucleate-boiling base equation, tube/annulus limits and required thermophysical inputs? | Local Elsevier full article or authorized TDM text with SI mapping and applicability limits. | Source-based HTC reference values; saturated/subcooled domain tests; source-status aggregation tests for any released adapter. |
| `HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE` | TH3337 gives candidate dryout boundary formulas for `xdi` and `xde`, but not the full Part II heat-transfer model. What are the Part II stratified-wavy, dryout and mist-flow heat-transfer equations? Which inputs require Part I map outputs, and what must happen if Part I is not released? | Target article full text or OCR/manual TH2978 release path, plus explicit dependency decision on Part I. | HTC/dryout reference tests; tests that Part II refuses to run without required Part I inputs; diagnostic separation tests for HTC, dryout and hydrodynamic qcrit. |

## Closure rule

A question is closed only when all of the following are true:

1. The full source text or scan is available locally under `sources/primary`.
2. `docs/primary_source_inventory.md` records path, SHA256, citation,
   audited pages/equations and the audit decision.
3. `docs/formula_registry.md` records formulas, variables, applicability
   limits, units and code/test mapping.
4. `docs/source_gate_manifest.json` changes the affected entry only when the
   release evidence is complete.
5. Focused source-gate tests and the runtime/API preflight pass.
