# Moreno Quiben TH3337 dryout pressure-drop audit 2026-07-07

Status: `candidate_only`. This document records a local dissertation audit
slice for Moreno Quiben TH3337, pages 123-124 and Eq. (7.18). It is not a
released WUT Part I/II, Friedel, MSH, dryout, CHF, or HTC model.

Local source: `sources/primary/moreno_quiben_2005_epfl_th3337.pdf`.
Inventory cross-check: `docs/primary_source_inventory.md` records SHA256
`B3FD9477D189C7720836C222BFD927BED34AD9E99CB4D1C188102423E26D1A77`.

Extraction check: `pypdf` text extraction on 2026-07-07 found the dryout-zone
pressure-drop interpolation text on pages 123-124. The text layer confirms
Eq. (7.18) as a linear interpolation that avoids a jump in frictional pressure
gradient between the upstream two-phase branch at `xdi` and the mist branch at
`xde`. The separate `xdi`/`xde` boundary formulas from Eqs. (7.19)-(7.20) are
locked in `docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md`.

## Page and equation map

| Pages | Evidence |
| --- | --- |
| 123 | Figure 7.11 defines the dryout zone between dryout inception quality `xdi` and dryout completion quality `xde`. Eq. (7.18) gives a linear interpolation for the dryout-zone frictional pressure drop. |
| 124 | The thesis states that `(Delta p)_tp(xdi)` is calculated from annular or stratified-wavy flow, `(Delta p)_mist(xde)` is calculated with Eq. (7.13), and that the dryout zone disappears when `xde` intersects `xdi`. |

## Candidate formula

The per-length helper uses the same linear form for pressure gradient:

```text
Delta p_dryout / L =
    Delta p_tp(xdi) / L
    - (x - xdi) / (xde - xdi)
      * (Delta p_tp(xdi) / L - Delta p_mist(xde) / L)
```

with:

```text
xdi <= x <= xde
0 <= xdi < xde <= 1
```

This helper intentionally accepts the two bounding pressure gradients as inputs.
It does not decide whether the upstream branch is annular or stratified-wavy,
does not compute Eq. (7.13), and does not compute the WUT dryout boundaries.

## Code-level candidate helper

- `published_friction.moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m`

The helper is a regression/audit fixture only. It is not called by
`CO2MathcadModel.run(...)`, `closure_state_from_model(...)`, `dryout_limit`, or
the guarded published MSH/Friedel functions.

## SI regression fixture

Inputs:

```text
x = 0.7
xdi = 0.5
xde = 0.9
Delta p_tp(xdi) / L = 10000 Pa/m
Delta p_mist(xde) / L = 3000 Pa/m
```

Expected audit values:

```text
Delta p / L = 6500.0 Pa/m
Delta p / L at x = xdi = 10000.0 Pa/m
Delta p / L at x = xde = 3000.0 Pa/m
```

## Release blockers

- Eq. (7.18) is one branch of Moreno Quiben's thesis flow-pattern pressure-drop
  model, not a standalone released MSH/Friedel/WUT runtime model.
- Runtime use would require released branch selection for annular,
  stratified-wavy and mist flow plus the transition-quality logic that provides
  `xdi` and `xde`.
- No pointwise experimental dryout-zone pressure-drop reference case has been
  transcribed from TH3337 into project tests.
- Releasing this as runtime physics would require an explicit
  `release_basis="dissertation"` decision, `audited_source_ref`,
  `audited_equations`, source-scope limits, SI variable mapping for all required
  branches and reference tests.
