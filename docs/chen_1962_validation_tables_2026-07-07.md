# Chen 1962 validation tables audit 2026-07-07

This candidate-only audit records manual transcription of Chen 1962 Tables I
and II from rendered pages 21 and 22 of the local OSTI scan
`sources/primary/chen_1962_osti_4636495.pdf`.
Local intake and SHA256 remain recorded in `docs/primary_source_inventory.md`.

It does not release `HTC-CHEN-1962-SOURCE-CANDIDATE` as runtime code. The
tables provide validation context, condition ranges and average percent
deviation comparisons, but they provide no raw HTC measurements or pointwise predicted HTC values and no fully specified reference cases suitable for release tests. The broader printed-reference audit is recorded in `docs/chen_1962_reference_value_audit_2026-07-08.md`.

## Source pages

| Source item | Rendered page | Finding |
| --- | --- | --- |
| Table I, "Range of Conditions for Data Used in Testing Correlation" | `.deps/chen_render/page_21.png` | Lists dataset-level ranges for pressure, liquid flow velocity, quality and heat flux. |
| Table II, "Comparison of Correlations" | `.deps/chen_render/page_22.png` | Lists dataset-level average percent deviations for several correlations, including "This Correlation". |

The rendered PNGs are workspace-local review artifacts and are not tracked.

## Table I transcription

The heat-flux column is headed `q/A x 10^-4` with units
`Btu/(hr)(ft^2)`. Values below are copied as the printed scaled ranges.

| Reference | Fluid | Geometry | Flow | Pressure, psia | Flow velocity, ft/s liquid | Quality, wt.% | `q/A x 10^-4`, Btu/(hr ft^2) |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | water | tube | up | 8-40 | 0.2-4.8 | 15-71 | 2.8-20 |
| 5 | water | tube | up | 42-505 | 0.8-14.7 | 3-50 | 6.5-76 |
| 4 | water | tube | down | 16-31 | 0.8-2.7 | 2-14 | 1.4-5.0 |
| 3 | water | annulus | up | 15-35 | 0.2-0.9 | 1-59 | 3.2-16 |
| 2 | methanol | tube | up | 15 | 1.0-2.5 | 1-4 | 0.7-1.7 |
| 2 | cyclohexane | tube | up | 15 | 1.3-2.8 | 2-10 | 0.3-1.3 |
| 2 | pentane | tube | up | 15 | 0.9-2.2 | 2-12 | 0.3-1.2 |
| 2 | heptane | tube | up | 15 | 1.0-2.4 | 2-10 | 0.2-0.9 |
| 2 | benzene | tube | up | 15 | 1.0-2.4 | 2-9 | 0.4-1.3 |

Release impact:

- Table I supports the applicability/context audit: mostly vertical tube data,
  one downward tube water set, one annulus water set, pressure and heat-flux
  ranges, and vapor-quality ranges.
- Table I does not give enough information for a pointwise HTC reference test:
  no pipe diameter, local saturation properties, wall superheat,
  vapor-pressure difference, `F`, `S`, observed HTC or predicted HTC is printed
  in the table.

## Table II transcription

Table II reports average percent deviations for correlations. The final column
is the Chen report's "This Correlation" result.

| Data | Dengler & Addoms | Guerrieri & Talty | Bennett et al. | Schrock & Grossman | This Correlation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dengler & Addoms (water) | 30.5 | 62.3 | 20.0 | 20.3 | 14.7 |
| Schrock & Grossman (water) | 89.5 | 16.4 | 24.9 | 20.0 | 15.1 |
| Sani (water) | 26.9 | 70.3 | 26.5 | 48.6 | 8.5 |
| Bennett et al. (water) | 17.9 | 61.8 | 11.9 | 14.6 | 10.8 |
| Guerrieri & Talty (methanol) | 42.5 | 9.5 | 64.8 | 62.5 | 11.3 |
| Guerrieri & Talty (cyclohexane) | 39.8 | 11.1 | 65.9 | 50.7 | 13.6 |
| Guerrieri & Talty (benzene) | 65.1 | 8.6 | 56.4 | 40.1 | 6.3 |
| Guerrieri & Talty (heptane) | 61.2 | 12.3 | 58.0 | 31.8 | 11.0 |
| Guerrieri & Talty (pentane) | 66.6 | 9.4 | 59.2 | 35.8 | 11.9 |
| Combined average for all data | 38.1 | 42.6 | 32.6 | 31.7 | 11.0 |

Release impact:

- Table II supports the validation-context statement that Chen's correlation
  was compared against water and organic-fluid data sets and reports an
  11.0 percent combined average deviation for "This Correlation".
- Table II still cannot be used as a release reference test because it gives
  aggregate deviations, not the underlying observed and predicted HTC values.

`docs/chen_1962_reference_value_audit_2026-07-08.md` reaches the same release
decision for the audited report pages and Figs. 9/10: no printed pointwise HTC
case table was found.

## Remaining release blocker

The candidate can move toward runtime release only after one of these artifacts
exists:

- primary-source pointwise data from another source with enough variables to
  reproduce an HTC value; or
- a release-grade documented hand calculation from audited Chen equations,
  reviewed `F/S` interpolation, source-unit/SI mapping, and explicit geometry
  scope.
