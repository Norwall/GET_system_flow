# Chen 1962 hand-calculation ledger 2026-07-08

This candidate-only ledger turns the existing Chen 1962 SI helper fixture into
an explicit arithmetic audit artifact. It checks that the code evaluates the
scan-verified Eqs. (9), (17), and (18) using Chen's source-unit coefficient and
the source-unit to SI conversions recorded in
`docs/chen_1962_si_mapping_2026-07-07.md`.

It does not release `HTC-CHEN-1962-SOURCE-CANDIDATE` as runtime HTC. The `F`
and `S` curves are still candidate digitizations with rendered review in
`docs/chen_1962_graph_review_2026-07-08.md`, the property-evaluation and
geometry scope decisions are not release-grade, and this fixture is not a
pointwise experimental value printed by the Chen report.

Local source: `sources/primary/chen_1962_osti_4636495.pdf`.
Inventory: `docs/primary_source_inventory.md`.
Source audit: `docs/chen_1962_formula_audit_2026-07-06.md`.
Graph audit: `docs/chen_1962_graph_digitization_2026-07-07.md`.
Graph review: `docs/chen_1962_graph_review_2026-07-08.md`.
Validation-context audit: `docs/chen_1962_validation_tables_2026-07-07.md`.
Printed reference-value audit: `docs/chen_1962_reference_value_audit_2026-07-08.md`.
Code fixture: `tests/test_boiling_diagnostics.py::test_chen_1962_candidate_si_helper_matches_documented_hand_calculation`.

## Equations Used

Eq. (9), source units:

```text
h_mac = 0.023 * Re_L^0.8 * Pr_L^0.4 * (k_L / D) * F
```

Eq. (17), source units:

```text
h_mic = 0.00122
  * k_L^0.79 * Cp_L^0.45 * rho_L^0.49 * g_c^0.25
  / (sigma^0.5 * mu_L^0.29 * lambda^0.24 * rho_v^0.24)
  * DeltaT^0.24 * DeltaP^0.75 * S
```

Eq. (18):

```text
h = h_mic + h_mac
```

The fixture keeps Chen's source-unit coefficient `0.00122`, converts SI inputs
into the source units, evaluates the equations, and converts the resulting HTC
back to `W/(m^2 K)`.

## Direct Eqs. (9)/(17)/(18) Fixture

SI inputs:

| Quantity | Value |
| --- | ---: |
| `Re_L` | `10000` |
| `Pr_L` | `2.0` |
| `D` | `0.01 m` |
| `k_L` | `0.6 W/(m K)` |
| `Cp_L` | `4200 J/(kg K)` |
| `rho_L` | `958 kg/m^3` |
| `rho_v` | `0.6 kg/m^3` |
| `mu_L` | `2.8e-4 Pa s` |
| `sigma` | `0.0589 N/m` |
| `lambda` | `2.257e6 J/kg` |
| `DeltaT` | `5 K` |
| `DeltaP` | `18000 Pa` |
| `F` | `3.0` |
| `S` | `0.4` |

Converted source-unit inputs:

| Quantity | Source-unit value |
| --- | ---: |
| `D` | `0.0328083989501 ft` |
| `k_L` | `0.346673590000 Btu/(hr ft degF)` |
| `Cp_L` | `1.003152765835 Btu/(lb degF)` |
| `rho_L` | `59.805986231798 lb/ft^3` |
| `rho_v` | `0.037456776346 lb/ft^3` |
| `mu_L` | `0.677344726963 lb/(ft hr)` |
| `sigma` | `0.004035932009 lbf/ft` |
| `lambda` | `970.335339638865 Btu/lb` |
| `DeltaT` | `9.0 degF` |
| `DeltaP` | `375.937816199339 psf` |
| `g_c` | `4.1697567e8 ft lbm/(lbf hr^2)` |

Computed source-unit HTC:

| Term | Value |
| --- | ---: |
| `h_mac` | `1524.7435663341 Btu/(hr ft^2 degF)` |
| `h_mic` | `241.6266815044 Btu/(hr ft^2 degF)` |
| `h_total` | `1766.3702478385 Btu/(hr ft^2 degF)` |

Converted SI HTC:

| Term | Value |
| --- | ---: |
| `h_mac` | `8657.8954971406 W/(m^2 K)` |
| `h_mic` | `1372.0199277941 W/(m^2 K)` |
| `h_total` | `10029.9154249347 W/(m^2 K)` |

## Candidate Graph-To-SI Fixture

The end-to-end candidate path uses the same physical fixture, adds
`x = 0.2` and `mu_v = 1.2e-5 Pa s`, then computes the Fig. 7 and Fig. 8
candidate coordinates before evaluating Eqs. (9), (17), and (18).

Candidate intermediate values:

| Quantity | Value |
| --- | ---: |
| `1/X_tt` | `8.3744338927` |
| `F_candidate` | `11.4390861217` |
| `R = Re_L * F^1.25` | `210372.5940296686` |
| `S_candidate` | `0.2220058995` |

Candidate graph-to-SI result:

| Term | Source-unit value | SI value |
| --- | ---: | ---: |
| `h_mac` | `5813.8909896245` | `33012.8040749551 W/(m^2 K)` |
| `h_mic` | `134.1063719014` | `761.4912953625 W/(m^2 K)` |
| `h_total` | `5947.9973615260` | `33774.2953703176 W/(m^2 K)` |

## Release Impact

This ledger closes the "undocumented arithmetic fixture" gap for the candidate
Chen SI helper and graph-to-SI composition tests. It does not close the source
gate. Remaining blockers:

- accept the rendered Fig. 7/Fig. 8 graph review as release-grade interpolation
  proof or replace it with an authoritative table;
- define property-evaluation points and the allowed geometry scope before any
  selectable runtime adapter;
- approve a documented hand-calculation release basis or obtain a pointwise
  source/reference HTC value from another primary source, since
  `docs/chen_1962_reference_value_audit_2026-07-08.md` found no printed
  pointwise HTC cases in the audited Chen report pages;
- keep dryout and CHF as separate source gates.
