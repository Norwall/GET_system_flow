# Chen 1962 reference-value audit 2026-07-08

Status: candidate_only / source-gate blocker narrowed, not released.

This audit answers a narrow release question for
`HTC-CHEN-1962-SOURCE-CANDIDATE`: does the local Chen 1962 OSTI report itself
print pointwise heat-transfer-coefficient reference cases that can become
release tests?

## Source And Extraction

Primary file: `sources/primary/chen_1962_osti_4636495.pdf`.
Inventory record: `docs/primary_source_inventory.md`.

SHA256:
`5DDE91B1FE38B2CE6E4977AEE2A25A61BBEDC83C5A7214802496754E4989017E`.

Extraction methods:

- `pypdf.PdfReader` text-layer extraction over the 37-page local PDF.
- Rendered local review images under `.deps/chen_render/` for pages 21, 22,
  25, 31, 32 and 33.
- Existing candidate audits:
  `docs/chen_1962_formula_audit_2026-07-06.md`,
  `docs/chen_1962_validation_tables_2026-07-07.md`,
  `docs/chen_1962_graph_review_2026-07-08.md`, and
  `docs/chen_1962_hand_calculation_2026-07-08.md`.

## Checked Pages

| Pages | Finding |
| --- | --- |
| 4 | Abstract gives the additive micro/macro boiling structure, final equations, and states that the correlation was tested against available data. It does not print pointwise observed/predicted HTC values. |
| 6 | Applicability is saturated two-phase convective flow, vertical axial stable flow, no slug flow, no liquid deficiency, heat flux below CHF, usually annular or annular-mist, and about 1-70 percent quality. It does not print reference values. |
| 10-14 | Derivation and final correlation path. Eq. (9), Eq. (17), and Eq. (18) are formula evidence; `F` and `S` are empirically determined functions. No pointwise data table is printed. |
| 15-16 | Validation narrative reports dataset-level average deviations for Dengler/Addoms, Schrock/Grossman, Guerrieri/Talty, Bennett et al., and Sani data. These are aggregate deviations, not raw HTC cases. |
| 20 | Bibliography identifies the source data sets. It is useful for follow-up source acquisition but does not contain Chen-report reference values. |
| 21 | Table I gives data-set ranges for pressure, liquid flow velocity, quality and heat flux. It lacks the local variables needed for a reproducible HTC test and prints no observed or predicted `h`. |
| 22 | Table II gives average percent deviations by data set and correlation. It does not print the underlying observed/predicted HTC pairs. |
| 23-24 | Nomenclature defines variables and source units, including `h` as the two-phase heat-transfer coefficient. It does not provide pointwise values. |
| 25 | Figure captions show that Figs. 9 and 10 compare the correlation with experimental results, but no numeric values are printed in the text layer. |
| 32-33 | Figs. 7 and 8 are graphical `F` and `S` functions only. They support candidate graph digitization, not pointwise HTC reference cases. |
| 34-35 | Figs. 9 and 10 are comparison plots of predicted versus experimental HTC. The text layer exposes axis/caption fragments but no numeric table of cases. Any future use would be chart digitization, not a printed reference-value transcription. |

## Validation-Value Decision

No pointwise Chen-report HTC reference cases were found in the audited report
pages. The report provides:

- released-source formula evidence for candidate audit work;
- graphical `F` and `S` functions in Figs. 7 and 8;
- data-set condition ranges in Table I;
- average percent deviations in Table II and the validation narrative;
- comparison plots in Figs. 9 and 10 without printed numeric case tables.

Therefore Tables I/II and Figs. 9/10 cannot by themselves become release
reference tests for a runtime HTC adapter.

## Release Impact

This audit closes the question "is there an obvious printed pointwise reference
HTC value in the Chen report?" with "no, not in the audited pages."

It does not release `HTC-CHEN-1962-SOURCE-CANDIDATE`. Before release, the gate
still needs one of these:

- a primary-source pointwise HTC case from Chen's underlying cited data sources
  or another authorized primary source; or
- an explicitly approved release-grade hand calculation from the audited Chen
  formulas, reviewed `F/S` interpolation, source-unit/SI mapping, property
  conventions and geometry scope.

Dryout and CHF remain separate source gates.
