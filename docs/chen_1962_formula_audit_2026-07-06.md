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
| 10-11 | Derivation starts with additive macro and micro mechanisms. The macro-convective branch is a modified Dittus-Boelter form. The text-layer extraction verifies the Eq. (9) structure as a liquid-side Dittus-Boelter coefficient multiplied by `F`: `h_mac = 0.023 * Re_L^0.8 * Pr_L^0.4 * k_L/D * F`, subject to manual visual confirmation of the scan. The text describes `F` as the unknown Reynolds-number factor tied to the Martinelli parameter `X_tt`. |
| 12-14 | The micro-convective branch is based on the Forster-Zuber pool-boiling analysis. Eq. (12) is partly readable but not reliably machine-transcribed from the scan. The text defines `S` from the effective-to-wall superheat ratio and states that `S` is represented as a function of local two-phase Reynolds number. Eq. (18) is the additive total coefficient `h = h_mic + h_mac`. |
| 14-15 | `F` and `S` are fitted iteratively from experimental data. The final correlation is stated to use Eqs. (9), (17), and (18), with `F` and `S` represented graphically in Figs. 7 and 8. |
| 15-18 | Validation discussion compares water and organic-fluid data. Reported average deviations include several individual datasets and the combined result; this supplies validation context but no standalone numeric reference point suitable for a runtime test yet. |
| 18-19 | Summary and recommendation repeat the annular/annular-mist scope and the 1-70 percent vapor-quality expectation for water and organics. The report explicitly excludes direct application to liquid metals without modification. |
| 20 | Bibliography records Forster and Zuber 1955 as the pool-boiling basis for the micro-convective branch and the experimental sources used for comparison. |
| 21-22 | Tables I and II summarize condition ranges and average percent deviations. The scan is usable for audit context, but table extraction is not clean enough to create reference tests without manual transcription. |
| 23-24 | Nomenclature defines `F`, `S`, `Re`, `Re_L`, heat flux, quality `x`, Martinelli parameter `X_tt`, superheat terms, latent heat, viscosity, density, and surface tension. Several OCR lines are degraded and must be manually checked before SI mapping. |
| 25, 32-33 | Caption list and figures identify Fig. 7 as Reynolds-number factor `F` and Fig. 8 as suppression factor `S`. These curves are graphical; no authoritative numeric table is present in the extracted text. |

## Text-layer equation extraction status

| Item | Status | Evidence and remaining work |
| --- | --- | --- |
| Eq. (9) macro-convective branch | `text_layer_verified_manual_visual_check_required` | The OSTI text layer gives the Dittus-Boelter liquid-side form multiplied by `F`: `h_mac = 0.023 * Re_L^0.8 * Pr_L^0.4 * k_L/D * F`. This is strong audit evidence for the equation structure, but visual confirmation from the scan is still required before runtime use. |
| Eq. (17) micro-convective branch | `not_released_ocr_degraded` | The page text confirms the Forster-Zuber basis, suppression factor `S`, and dependence on total wall superheat, but OCR around the combined equation is not sufficient for reliable transcription of all constants, exponents and units. |
| Eq. (18) additive total HTC | `text_layer_verified_manual_visual_check_required` | The text layer verifies `h = h_mic + h_mac`. Runtime use still depends on released Eq. (17), released `F/S` functions and SI mapping. |
| `F(X_tt)` | `graphical_function_not_digitized` | The report states `F` is determined empirically and represented in Fig. 7. No numeric table is available in the extracted text. |
| `S(Re_tp)` | `graphical_function_not_digitized` | The report states `S` is determined empirically and represented in Fig. 8. No numeric table is available in the extracted text. |

## Figure extraction attempt

Pages 32-33 contain Figures 7 and 8 as JBIG2-encoded page imagery. `pypdf`
cannot decode those images without a `jbig2dec` binary. A workspace-local
Poppler download was attempted from the Chocolatey package, but that package
contains Poppler source rather than ready Windows `pdftoppm`/`pdfimages`
binaries. Therefore the current repository still lacks a reproducible local
renderer for digitizing Figs. 7 and 8. The next acceptable artifact is either:

- a reproducible renderer setup under `.deps` or documented external toolchain
  that produces page images from the local PDF; or
- an authoritative numeric table for `F(X_tt)` and `S(Re_tp)` tied to a primary
  source.

## Runtime release blockers

- Digitize or otherwise obtain authoritative numeric `F(X_tt)` and `S(Re_tp)`
  functions from Figs. 7 and 8.
- Manually visually confirm Eq. (9) and Eq. (18) from the scan, and fully
  transcribe Eq. (17), including constants, exponents, units and
  property-evaluation points.
- Convert the original English-unit variables and nomenclature to project SI
  state variables.
- Add at least one primary-source numeric HTC reference calculation, or a
  documented hand calculation from the audited equations and digitized curves.
- Keep this candidate separate from dryout and CHF. Chen 1962 is HTC-only
  evidence and cannot release dryout/critical-heat-flux gates.
- Decide released geometry scope before using the vertical axial-flow
  correlation in horizontal evaporator scenarios.
