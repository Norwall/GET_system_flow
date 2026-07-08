# Chen 1962 formula audit 2026-07-06

This audit records page/equation evidence from the local OSTI PDF for
`HTC-CHEN-1962-SOURCE-CANDIDATE`. It is source-candidate evidence only and does not release a runtime heat-transfer correlation, dryout model, or CHF model.
Local file intake and SHA256 records remain governed by
`docs/primary_source_inventory.md`.

## Local candidate

| Candidate | Local file | SHA256 | Decision |
| --- | --- | --- | --- |
| `HTC-OSTI-1962-SOURCE-CANDIDATE` | `sources/primary/chen_1962_osti_4636495.pdf` | `5DDE91B1FE38B2CE6E4977AEE2A25A61BBEDC83C5A7214802496754E4989017E` | `candidate_only` |

Official record: `https://www.osti.gov/biblio/4636495`.
Full-text endpoint: `https://www.osti.gov/servlets/purl/4636495`.

## Page/equation map

| Pages | Audit finding |
| --- | --- |
| 4 | Abstract states the additive mechanism: total heat transfer is built from micro-convective and macro-convective contributions. It identifies the macro branch as Dittus-Boelter-type with an extra factor `F`, and the micro branch as using a suppression factor `S`. The scanned formula lines are partly degraded, so this page is structure evidence, not releasable transcription. |
| 6 | Applicability is explicitly limited to saturated, two-phase non-metallic fluids in vertical axial, stable convective flow, with no slug flow, no liquid deficiency, and heat flux below critical flux. The report says these conditions usually occur in annular or annular-mist flow at approximately 1-70 percent vapor quality. |
| 10-11 | Derivation starts with additive macro and micro mechanisms. The macro-convective branch is a modified Dittus-Boelter form. PyMuPDF page render visually verifies the Eq. (9) structure as a liquid-side Dittus-Boelter coefficient multiplied by `F`: `h_mac = 0.023 * Re_L^0.8 * Pr_L^0.4 * k_L/D * F`. The text describes `F` as the unknown Reynolds-number factor tied to the Martinelli parameter `X_tt`. |
| 12-14 | The micro-convective branch is based on the Forster-Zuber pool-boiling analysis. The text defines `S` from the effective-to-wall superheat ratio and states that `S` is represented as a function of local two-phase Reynolds number. PyMuPDF page render visually verifies Eq. (17), and Eq. (18) is the additive total coefficient `h = h_mic + h_mac`. |
| 14-15 | `F` and `S` are fitted iteratively from experimental data. The final correlation is stated to use Eqs. (9), (17), and (18), with `F` and `S` represented graphically in Figs. 7 and 8. |
| 15-18 | Validation discussion compares water and organic-fluid data. Reported average deviations include several individual datasets and the combined result; this supplies validation context but no standalone numeric reference point suitable for a runtime test yet. |
| 18-19 | Summary and recommendation repeat the annular/annular-mist scope and the 1-70 percent vapor-quality expectation for water and organics. The report explicitly excludes direct application to liquid metals without modification. |
| 20 | Bibliography records Forster and Zuber 1955 as the pool-boiling basis for the micro-convective branch and the experimental sources used for comparison. |
| 21-22 | Tables I and II summarize condition ranges and average percent deviations. Manual transcription is recorded in `docs/chen_1962_validation_tables_2026-07-07.md`; the tables are validation context only and do not contain pointwise HTC reference cases. |
| 23-24 | Nomenclature defines `F`, `S`, `Re`, `Re_L`, heat flux, quality `x`, Martinelli parameter `X_tt`, superheat terms, latent heat, viscosity, density, and surface tension. Several OCR lines are degraded and must be manually checked before SI mapping. |
| 25, 32-33 | Caption list and figures identify Fig. 7 as Reynolds-number factor `F` and Fig. 8 as suppression factor `S`. These curves are graphical; no authoritative numeric table is present in the extracted text. |
| 34-35 | Figs. 9 and 10 compare this correlation with experimental results graphically. `docs/chen_1962_reference_value_audit_2026-07-08.md` records that no printed pointwise HTC reference table is exposed by the audited report pages. |

## Text-layer equation extraction status

| Item | Status | Evidence and remaining work |
| --- | --- | --- |
| Eq. (9) macro-convective branch | `scan_verified_not_released` | The scan verifies the Dittus-Boelter liquid-side form multiplied by `F`: `h_mac = 0.023 * Re_L^0.8 * Pr_L^0.4 * k_L/D * F`. Runtime use still depends on released `F`, source-unit to SI mapping and reference tests. |
| Eq. (17) micro-convective branch | `scan_verified_not_released` | The scan verifies `h_mic = 0.00122 * (k_L^0.79 * Cp_L^0.45 * rho_L^0.49 * g_c^0.25) / (sigma^0.5 * mu_L^0.29 * lambda^0.24 * rho_v^0.24) * (DeltaT)^0.24 * (DeltaP)^0.75 * S`. Candidate source-unit to SI mapping and a code-level hand-calculation helper are recorded in `docs/chen_1962_si_mapping_2026-07-07.md`; runtime use still depends on released `S`, implementation decisions and source/reference tests. |
| Eq. (18) additive total HTC | `scan_verified_not_released` | The scan verifies `h = h_mic + h_mac`. Runtime use still depends on released `F/S` functions, reviewed geometry/scope and source/reference tests. |
| `F(X_tt)` | `candidate_reviewed_not_released` | The report states `F` is determined empirically and represented in Fig. 7. Candidate graph digitization is recorded in `docs/chen_1962_graph_digitization_2026-07-07.md` and rendered graph review is recorded in `docs/chen_1962_graph_review_2026-07-08.md`, but no authoritative numeric table is present in the extracted text and runtime release still needs an accepted uncertainty decision, SI mapping and reference tests. |
| `S(Re_tp)` | `candidate_reviewed_not_released` | The report states `S` is determined empirically and represented in Fig. 8. Candidate graph digitization is recorded in `docs/chen_1962_graph_digitization_2026-07-07.md` and rendered graph review is recorded in `docs/chen_1962_graph_review_2026-07-08.md`, but no authoritative numeric table is present in the extracted text and runtime release still needs an accepted uncertainty decision, SI mapping and reference tests. |

## Figure extraction attempt

Pages 10-14 and 32-33 were rendered from the local PDF with workspace-local
PyMuPDF 1.28.0 during the 2026-07-07 follow-up. This closes the visual
transcription question for Eqs. (9), (17), and (18). A candidate-only
digitization of Figs. 7 and 8 is recorded in
`docs/chen_1962_graph_digitization_2026-07-07.md`, with rendered overlay review
in `docs/chen_1962_graph_review_2026-07-08.md`, but it does not release a
runtime HTC model because the graph fit still needs an accepted uncertainty
decision or authoritative table, source-based reference values and
geometry/scope review. A candidate source-unit
helper now exists in
`boiling_heat_transfer.chen_1962_candidate_heat_transfer_coefficient_si`; it is a
transcription/unit-conversion check only. Candidate dimensionless helpers
`boiling_heat_transfer.chen_1962_candidate_inverse_martinelli_parameter` and
`boiling_heat_transfer.chen_1962_candidate_two_phase_reynolds` now lock the
Fig. 7 and Fig. 8 abscissa mappings from the nomenclature, but they are not
release-grade runtime inputs.
`boiling_heat_transfer.chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si`
now locks the candidate graph-to-SI composition path, but it is also not a
Chen report validation point or released runtime HTC. The helper now also
rejects vapor qualities outside the source's approximate `0.01 <= x <= 0.70`
scope before graph-to-SI composition. The next acceptable release artifact
is either:

- a reviewed digitized table/interpolation for the centerline `F(X_tt)` and
  `S(Re_tp)` curves with uncertainty notes tied to the rendered primary-source
  pages and the same plotted-domain guards now enforced by the candidate
  helpers; or
- an authoritative numeric table for `F(X_tt)` and `S(Re_tp)` tied to a primary
  source.

Tables I and II are now manually transcribed in
`docs/chen_1962_validation_tables_2026-07-07.md`. They support condition-range
and validation-context audit, but they cannot supply a source/reference HTC
test because they give aggregate ranges and deviations rather than pointwise
observed/predicted HTC values.

`docs/chen_1962_reference_value_audit_2026-07-08.md` extends the same release
finding to the audited pages and Figs. 9/10: the report gives graphical
comparisons, not a printed pointwise HTC table suitable for release tests.

## Runtime release blockers

- Accept the reviewed candidate `F(X_tt)` and `S(Re_tp)` digitization from
  `docs/chen_1962_graph_digitization_2026-07-07.md` and
  `docs/chen_1962_graph_review_2026-07-08.md`, or obtain authoritative numeric
  functions from Figs. 7 and 8. The candidate helpers now reject extrapolation
  outside the rendered Fig. 7/Fig. 8 ranges, but the centerline graph fit still
  needs a release decision.
- Review the candidate source-unit to SI mapping in
  `docs/chen_1962_si_mapping_2026-07-07.md`, including `g_c`, pressure units,
  superheat units, property-evaluation points and the pressure/superheat
  relationship used by Eq. (17), against the code helpers.
- Convert the original English-unit variables and nomenclature to project SI
  state variables in tested runtime code only after release decision.
- Add at least one primary-source numeric HTC reference calculation, or a
  release-grade documented hand calculation from the audited equations and
  digitized curves. The current helper test is not a Chen report validation
  point.
- Keep this candidate separate from dryout and CHF. Chen 1962 is HTC-only
  evidence and cannot release dryout/critical-heat-flux gates.
- Decide released geometry scope before using the vertical axial-flow
  correlation in horizontal evaporator scenarios, and keep the source
  vapor-quality guard `0.01 <= x <= 0.70` unless a release audit justifies a
  different range.
