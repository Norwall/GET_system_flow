# Wojtan TH2978 text-layer audit 2026-07-08

Status: `candidate_only`. This note records what can and cannot be extracted
from the local EPFL TH2978 dissertation text layer for WUT Part I/Part II work.
It does not release a regime map, heat-transfer model, dryout model, CHF model,
or any runtime adapter.

Local source: `sources/primary/wojtan_2004_epfl_th2978.pdf`.
Inventory cross-check: `docs/primary_source_inventory.md` records SHA256
`0F17826CA107DD8744E8AFA914E11FB422D5BC551589ACE5492B04F5669075D5`.

Extraction check: `pypdf` on 2026-07-08. The PDF has 221 pages. The text layer
is partially custom-encoded: many prose and equation spans are emitted as
tokens such as `/D8/CW/CT/...`, so the extracted text is not reliable enough
for formula transcription. The follow-up rendered-page audit is recorded in
`docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md`; it supersedes the
text-layer-only limitation for dryout-limit Eqs. (7.47)-(7.48), but not for WUT
Part I map transitions or Part II heat-transfer equations.

## Findings

| PDF index | Human page | Text-layer finding |
| ---: | ---: | --- |
| 8-12 | 9-13 | Table-of-contents pages are mostly custom-encoded. They confirm only the document structure already recorded in `docs/dissertation_formula_audit_2026-07-06.md`; they do not expose release-grade chapter titles or formulas. |
| 160-170 | 161-171 | Surrounding dryout/nonequilibrium prose is mostly custom-encoded. Some figure axes and labels are readable, but equations and variable definitions are not reliably extractable. |
| 171-176 | 172-177 | Heat-transfer plots are readable at caption/axis level. The text layer exposes `Vapor quality`, `Heat transfer coefficient [W/m2K]`, `hexp`, `xdi`, `xde`, refrigerants R-22/R-410A, mass fluxes such as 300-700 kg/m2s, `Tsat=5 C`, diameters 13.84 mm and 8.00 mm, and heat fluxes such as 57.5 and 37.5 kW/m2. These are plotted experimental/marker contexts, not tabulated HTC reference cases. |
| 177 | 178 | Dryout onset/end summary plots are readable at caption/axis level. The text layer exposes `Mass Velocity [kg/m2s]`, `Onset and end of dryout`, `xdi`, `xde`, R-22/R-410A, `Tsat=5 C`, diameters 13.84 mm and 8.00 mm, and heat-flux labels. No release-grade equations are extracted. |
| 178 | 179 | The dryout-zone schematic exposes labels such as `Dryout zone`, `xdi`, `xde`, A/B/C cross sections, and vapor/liquid flow labels. The explanatory prose and equations remain custom-encoded. |
| 180-182 | 181-183 | Comparison plots expose axis labels, `xdi`, `xde`, and comparison names such as Mori/new formulas at caption level. They do not provide pointwise numerical data or transcribed equations. |

## Closed Evidence

- TH2978 is a useful local dissertation candidate for WUT Part I/Part II audit
  guidance, and the relevant dryout/HTC figure span is confirmed around human
  pages 172-183.
- The text layer does expose figure-level variables and markers `hexp`, `xdi`,
  and `xde`, plus refrigerant/test-condition labels.
- These pages can guide future manual OCR, screenshot review, or figure
  digitization work.
- Rendered pages now confirm candidate dryout-limit Eqs. (7.47)-(7.48) in
  `docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md`.

## Remaining Blockers

- The WUT Part I transition equations and Part II stratified-wavy, dryout, and
  mist heat-transfer equations are not reliably extractable from the text layer.
  The rendered audit covers only dryout-limit Eqs. (7.47)-(7.48) as
  candidate-only evidence.
- The pages inspected here do not expose raw HTC tables, pointwise predicted HTC
  values, or enough variables for source/reference tests.
- A release path still requires either the target journal articles or a
  dissertation-specific release decision backed by rendered-page/OCR formula
  transcription, SI variable mapping, applicability limits, and reference tests.
- TH3337 pressure-drop and dryout-boundary helpers remain separate
  `candidate_only` guidance; they do not release TH2978 or WUT runtime physics.
