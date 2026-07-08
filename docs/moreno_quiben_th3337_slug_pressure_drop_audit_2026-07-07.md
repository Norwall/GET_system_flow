# Moreno Quiben TH3337 slug pressure-drop audit 2026-07-07

Status: `candidate_only`. This document records a local dissertation audit
slice for Moreno Quiben TH3337, pages 120-122 and Eqs. (7.6) and (7.12). It is
not a released WUT Part I/II, Friedel, MSH, dryout, CHF, or HTC model.

Local source: `sources/primary/moreno_quiben_2005_epfl_th3337.pdf`.
Inventory cross-check: `docs/primary_source_inventory.md` records SHA256
`B3FD9477D189C7720836C222BFD927BED34AD9E99CB4D1C188102423E26D1A77`.

Extraction check: `pypdf` text extraction on 2026-07-07 found the
slug/intermittent and slug+stratified-wavy interpolation formulas on pages
120-122. The text layer confirms that the same exponent `0.25` is used to
interpolate between the all-liquid pressure drop and the limiting branch
pressure drop while avoiding jumps at the intermittent-to-annular boundary.

## Page and equation map

| Pages | Evidence |
| --- | --- |
| 120-121 | Slug and intermittent regimes are treated together. Eq. (7.6) interpolates between the single-phase liquid pressure drop at `x = 0` and the annular-branch pressure drop evaluated at the actual vapor quality. |
| 122 | Slug+stratified-wavy flow uses the same interpolation structure in Eq. (7.12), replacing the annular limiting branch with the stratified-wavy branch. The thesis states that the `0.25` exponent again gives the best representation of the data. |

## Candidate formula

The helper uses the per-length pressure-gradient form:

```text
Delta p_slug / L =
    (Delta p_L0 / L) * (1 - alpha_IA)^0.25
    + (Delta p_branch / L) * alpha_IA^0.25
```

where:

```text
0 <= alpha_IA <= 1
```

`Delta p_branch / L` is the annular branch for Eq. (7.6) and the
stratified-wavy branch for Eq. (7.12). This helper intentionally accepts that
branch pressure gradient as an input. It does not compute the regime map,
`alpha_IA`, annular film thickness, dry angle, or stratified-wavy friction
factor.

## Code-level candidate helper

- `published_friction.moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m`

The helper is a regression/audit fixture only. It is not called by
`CO2MathcadModel.run(...)`, `closure_state_from_model(...)`, `dryout_limit`, or
the guarded published MSH/Friedel functions.

## SI regression fixture

Inputs:

```text
Delta p_L0 / L = 1000 Pa/m
Delta p_branch / L = 5000 Pa/m
alpha_IA = 0.5
```

Expected audit values:

```text
Delta p / L = 5045.3784915223 Pa/m
Delta p / L at alpha_IA = 0 = 1000.0 Pa/m
Delta p / L at alpha_IA = 1 = 5000.0 Pa/m
```

## Release blockers

- Eq. (7.6) and Eq. (7.12) are branches of Moreno Quiben's thesis
  flow-pattern pressure-drop model, not standalone released MSH/Friedel/WUT
  runtime models.
- Runtime use would require released regime classification, `alpha_IA`, and the
  limiting annular or stratified-wavy branch calculation.
- No pointwise experimental slug/intermittent pressure-drop reference case has
  been transcribed from TH3337 into project tests.
- Releasing this as runtime physics would require an explicit
  `release_basis="dissertation"` decision, `audited_source_ref`,
  `audited_equations`, source-scope limits, SI variable mapping for all required
  branches and reference tests.
