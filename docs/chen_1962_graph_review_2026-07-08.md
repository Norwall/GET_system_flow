# Chen 1962 rendered graph review 2026-07-08

Status: `candidate_only`. This note records a second-pass rendered-page review
of the Chen 1962 graphical `F` and `S` functions from the local OSTI scan. It
reviews the first-pass digitization in
`docs/chen_1962_graph_digitization_2026-07-07.md`; it does not convert the
digitization into released runtime HTC logic.

Local source: `sources/primary/chen_1962_osti_4636495.pdf`.
Inventory: `docs/primary_source_inventory.md`.
Formula audit: `docs/chen_1962_formula_audit_2026-07-06.md`.
SI mapping: `docs/chen_1962_si_mapping_2026-07-07.md`.
Hand-calculation ledger: `docs/chen_1962_hand_calculation_2026-07-08.md`.

Rendered review images were inspected under `.deps/chen_render/`:

- `page_31.png` and `fig7_fit_overlay.png` for Fig. 7.
- `page_32.png` and `fig8_manual_fit_overlay.png` for Fig. 8.

The rendered images are local scratch evidence and are not tracked.

## Fig. 7 Review

Fig. 7 is readable as a log-log plot. The rendered page shows the horizontal
axis as the reciprocal Martinelli parameter:

```text
1/X_tt = (x/z)^0.9 * (rho_L/rho_v)^0.5 * (mu_v/mu_L)^0.1
```

The vertical axis is:

```text
F = (Re/Re_L)^0.8
```

The plotted frame supports the digitization limits recorded earlier:

```text
0.1 <= 1/X_tt <= 100
0.1 <= F <= 100
```

The overlay of

```text
F_candidate(Y) = 2.35 * (Y + 0.213)^0.736
```

tracks the visible centerline from `Y = 0.1` through `Y = 100` and stays inside
the rendered data band. The scan still does not provide an authoritative
numeric table, so this is a reviewed graph-fit candidate, not a release-grade
formula.

## Fig. 8 Review

Fig. 8 is readable as a semilog-x plot. The rendered page shows the horizontal
axis as:

```text
R = Re_L * F^1.25
```

The vertical axis is:

```text
S = (DeltaT_e / DeltaT)^0.99
```

The reviewed plotted range used by the helper is:

```text
1.5e4 <= Re_L * F^1.25 <= 7e5
0 < S <= 1
```

The digitized centerline points from
`docs/chen_1962_graph_digitization_2026-07-07.md` were checked against the
overlay of:

```text
S_candidate(R) = 1 / (1 + 1.024e-5 * R^1.0397)
```

The maximum absolute residual against the manually sampled centerline points is
about `0.0137` in `S`. The largest visual uncertainty remains the right tail,
where the curve flattens near the lower axis and the hatched data band overlaps
the centerline. This is good enough for a candidate audit fixture and domain
guard, but not enough to release a production HTC adapter without accepting the
graph uncertainty or replacing the graph fit with an authoritative table.

## Release Impact

This review closes the narrower question "has the candidate Fig. 7/Fig. 8
digitization been checked against the rendered source pages?" It does not close
`HTC-CHEN-1962-SOURCE-CANDIDATE`.

Remaining blockers:

- decide whether the reviewed graph fit is acceptable as release proof or
  replace it with an authoritative table;
- define property-evaluation points for `DeltaP`, wall superheat, liquid/vapor
  saturation properties and geometry scope;
- decide whether the documented hand calculation can be promoted to release
  proof or add a pointwise HTC reference value from the report;
- keep dryout and CHF separate from this HTC-only candidate.
