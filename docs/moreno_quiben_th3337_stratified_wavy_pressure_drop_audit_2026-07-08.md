# Moreno Quiben TH3337 stratified-wavy pressure-drop audit 2026-07-08

Status: `candidate_only`. This document records a local dissertation audit
slice for Moreno Quiben TH3337, pages 121-122 and Eqs. (7.9)-(7.11). It is not
a released WUT Part I/II, Friedel, MSH, dryout, CHF, or HTC model.

Local source: `sources/primary/moreno_quiben_2005_epfl_th3337.pdf`.
Inventory cross-check: `docs/primary_source_inventory.md` records SHA256
`B3FD9477D189C7720836C222BFD927BED34AD9E99CB4D1C188102423E26D1A77`.

Extraction check: `pypdf` text extraction on 2026-07-08 found the
stratified-wavy pressure-drop text on pages 121-122. The text layer confirms
the dry-angle interpolation context, Eq. (7.9) for the two-phase friction
factor, Eq. (7.10) for the single-phase gas friction factor and gas Reynolds
number, and Eq. (7.11) for frictional pressure drop. The dry-angle and Biberg
void-fraction expression remain upstream inputs; this note locks only the
branch-level algebra used after those inputs are known.

## Page and equation map

| Pages | Evidence |
| --- | --- |
| 121 | The stratified-wavy section defines the dry angle as the structural parameter and records Eq. (7.9): the two-phase friction factor is a weighted combination of the gas friction factor and the annular interfacial friction factor. |
| 122 | The thesis defines the dry perimeter fraction from the dry angle, gives Eq. (7.10) for `f_G = 0.079/Re_G^0.25` with `Re_G = G*x*D/mu_G`, and gives Eq. (7.11) for the stratified-wavy frictional pressure drop. |

## Candidate formulas

The helper uses the source's dry perimeter fraction, denoted here as
`epsilon_dry`, as an input:

```text
f_tp,stratified-wavy =
    epsilon_dry * f_G
    + (1 - epsilon_dry) * (f_i)_annular
```

with the gas-side friction factor:

```text
f_G = 0.079 / Re_G^0.25

Re_G = G * x * D / mu_G
```

The per-length pressure-gradient form implemented for audit/regression is:

```text
Delta p_stratified-wavy / L =
    4 * f_tp,stratified-wavy / D * rho_G * u_G^2 / 2
```

This helper intentionally accepts `epsilon_dry` and `(f_i)_annular` as inputs.
It does not compute the Wojtan map, `G_wavy`, `G_strat`, the Biberg
`theta_strat` expression, liquid level geometry, or annular film thickness.

## Code-level candidate helpers

- `published_friction.moreno_quiben_th3337_candidate_gas_friction_factor`
- `published_friction.moreno_quiben_th3337_candidate_stratified_wavy_two_phase_friction_factor`
- `published_friction.moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m`

These helpers are regression/audit fixtures only. They are not called by
`CO2MathcadModel.run(...)`, `closure_state_from_model(...)`, `dryout_limit`, or
the guarded published MSH/Friedel functions.

## SI regression fixture

Inputs:

```text
x = 0.5
G = 200 kg/(m^2 s)
D = 0.01 m
mu_G = 1.0e-5 Pa*s
epsilon_dry = 0.25
(f_i)_annular = 0.03
rho_G = 20 kg/m^3
u_G = 10 m/s
```

Expected audit values:

```text
f_G = 0.0044424965
f_tp = 0.0236106241
Delta p / L = 9444.2496469004 Pa/m
```

## Release blockers

- Eq. (7.9)-(7.11) are one branch of Moreno Quiben's thesis flow-pattern
  pressure-drop model, not a standalone released MSH/Friedel/WUT runtime model.
- Runtime use would require released regime classification, the Wojtan map
  boundaries, dry-angle or dry perimeter fraction calculation, and the annular
  interfacial friction factor input.
- No pointwise experimental stratified-wavy pressure-drop reference case has
  been transcribed from TH3337 into project tests.
- Releasing this as runtime physics would require an explicit
  `release_basis="dissertation"` decision, `audited_source_ref`,
  `audited_equations`, source-scope limits, SI variable mapping for all required
  branches and reference tests.
