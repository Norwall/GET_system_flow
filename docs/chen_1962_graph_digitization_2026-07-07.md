# Chen 1962 graph digitization 2026-07-07

This candidate-only audit records a reproducible first-pass digitization of
Chen 1962 Figures 7 and 8 from the local OSTI scan
`sources/primary/chen_1962_osti_4636495.pdf`. It is not a runtime release:
the curves are graphical, scan quality is limited, the original source-unit to
SI mapping is only candidate-audited in `docs/chen_1962_si_mapping_2026-07-07.md`,
and no source-based HTC reference test has been implemented.

Follow-up rendered-page review is recorded in
`docs/chen_1962_graph_review_2026-07-08.md`. That review checks the overlays
against the rendered source pages, but it still does not make the graph fit a
released runtime interpolation.

## Rendered source pages

| Figure | Rendered page image | Plot frame in rendered image | Axis calibration |
| --- | --- | --- | --- |
| Fig. 7, Reynolds-number factor `F` | `.deps/chen_render/page_31.png`, 1841 x 2364 px | `x=382..1529`, `y=519..1669` | log-log; horizontal axis `Y=1/X_tt` from `10^-1` to `10^2`; vertical axis `F=(Re/Re_L)^0.8` from `10^-1` to `10^2` |
| Fig. 8, suppression factor `S` | `.deps/chen_render/page_32.png`, 2366 x 1834 px | `x=503..1907`, `y=510..1208` | semilog-x; horizontal axis `R=Re_L*F^1.25` from `10^4` to `10^6`; vertical axis `S=(Delta T_e/Delta T)^0.99` from `0` to `1.0` |

The frame coordinates were taken from the longest dark plot-border rows and
columns in the rendered PNGs. Local overlay checks were generated under
`.deps/chen_render/` and are intentionally not tracked.

## Fig. 7 candidate fit

Let `Y = 1/X_tt`. The following smooth candidate fit follows the Fig. 7
centerline over the plotted range:

```text
F_candidate(Y) = 2.35 * (Y + 0.213)^0.736
valid only for 0.1 <= Y <= 100
```

This expression is a graph-fit candidate, not a text equation printed in the
report. It should not be used outside the plotted axis range or promoted to a
released runtime formula without independent review.
The candidate helper `chen_1962_candidate_f_factor` now refuses extrapolation
outside `0.1 <= 1/X_tt <= 100`.

| `Y=1/X_tt` | `F_candidate` | source px `x` | source px `y` |
| ---: | ---: | ---: | ---: |
| 0.1 | 1.00 | 382 | 1286 |
| 0.2 | 1.23 | 497 | 1252 |
| 0.3 | 1.44 | 564 | 1225 |
| 0.5 | 1.83 | 649 | 1185 |
| 0.7 | 2.20 | 705 | 1155 |
| 1 | 2.71 | 764 | 1120 |
| 1.5 | 3.49 | 832 | 1077 |
| 2 | 4.22 | 879 | 1046 |
| 3 | 5.55 | 947 | 1000 |
| 5 | 7.92 | 1032 | 941 |
| 7 | 10.1 | 1087 | 901 |
| 10 | 13.0 | 1147 | 859 |
| 15 | 17.4 | 1214 | 810 |
| 20 | 21.5 | 1262 | 775 |
| 30 | 28.9 | 1329 | 726 |
| 50 | 42.0 | 1414 | 664 |
| 70 | 53.7 | 1470 | 622 |
| 100 | 69.8 | 1529 | 579 |

## Fig. 8 candidate points

Let `R = Re_L*F^1.25`. Fig. 8 has a visible central line and a hatched data
band. The points below are manual centerline samples from the rendered scan,
not an authoritative table from the report.

| `R=Re_L*F^1.25` | `S_digitized` | source px `x` | source px `y` |
| ---: | ---: | ---: | ---: |
| 1.5e4 | 0.83 | 627 | 629 |
| 2.0e4 | 0.77 | 714 | 671 |
| 3.0e4 | 0.68 | 838 | 733 |
| 5.0e4 | 0.55 | 994 | 824 |
| 7.0e4 | 0.46 | 1096 | 887 |
| 1.0e5 | 0.37 | 1205 | 950 |
| 1.5e5 | 0.29 | 1329 | 1006 |
| 2.0e5 | 0.23 | 1416 | 1047 |
| 3.0e5 | 0.16 | 1540 | 1096 |
| 5.0e5 | 0.10 | 1696 | 1138 |
| 7.0e5 | 0.085 | 1798 | 1149 |

Least-squares fit to these manual candidate points:

```text
S_candidate(R) = 1 / (1 + 1.024e-5 * R^1.0397)
valid only for approximately 1.5e4 <= R <= 7e5
```

The right tail is visually uncertain because the curve flattens near the lower
axis and the hatched band intersects the line. The fit should be treated as a
candidate interpolation aid, not a released formula.
The candidate helper `chen_1962_candidate_suppression_factor` now refuses
extrapolation outside `1.5e4 <= Re_L*F^1.25 <= 7e5`.

## Release impact

This audit closes the first "no digitization attempt exists" gap for Chen
Figures 7 and 8; `docs/chen_1962_graph_review_2026-07-08.md` closes the
narrower rendered-overlay review gap. Neither document closes the source gate.
Remaining release work:

- decide whether the reviewed candidate digitization uncertainty is acceptable
  for release, or replace it with an authoritative table;
- keep plotted-domain guards for Fig. 7 and Fig. 8 if any candidate path is
  used for audit calculations;
- map Eqs. (9), (17), and (18), including `g_c`, pressure and superheat units,
  into project SI variables;
- define the released geometry and quality range;
- add at least one source-based or fully documented hand-calculation HTC
  reference test;
- use `docs/chen_1962_validation_tables_2026-07-07.md` only as validation
  context unless pointwise HTC values are obtained;
- update `docs/primary_source_inventory.md`, `docs/formula_registry.md` and
  `docs/source_gate_manifest.json` only after release-grade review;
- prove that dryout and CHF remain separate gates.
