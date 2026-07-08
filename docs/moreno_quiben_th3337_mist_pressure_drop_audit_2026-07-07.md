# Moreno Quiben TH3337 mist pressure-drop audit 2026-07-07

Status: `candidate_only`. This document records a local dissertation audit
slice for Moreno Quiben TH3337, pages 122-123 and Eq. (7.13)-(7.17). It is not
a released WUT Part I/II, Friedel, MSH, dryout, CHF, or HTC model.

Local source: `sources/primary/moreno_quiben_2005_epfl_th3337.pdf`.
Inventory cross-check: `docs/primary_source_inventory.md` records SHA256
`B3FD9477D189C7720836C222BFD927BED34AD9E99CB4D1C188102423E26D1A77`.

Extraction check: `pypdf` text extraction on 2026-07-07 found the mist-region
text on pages 122-123. The text layer confirms the homogeneous-flow pressure
drop expression and mixture definitions in Eq. (7.13)-(7.17). This audit still
treats the helper as candidate-only because the full flow-pattern pressure-drop
model also depends on released regime classification, dryout interpolation,
transition-quality logic and reference tests.

## Page and equation map

| Pages | Evidence |
| --- | --- |
| 122 | The mist regime is defined as the case where all liquid is entrained in the gas core and the two phases are treated as a single phase with mean fluid properties. Eq. (7.13) gives the homogeneous frictional pressure drop. Eq. (7.14) defines homogeneous mixture density. |
| 123 | Eq. (7.15) defines homogeneous void fraction, Eq. (7.16) defines the mixture friction factor from mixture Reynolds number, and Eq. (7.17) uses the Cicchitti viscosity expression. The thesis states that Eq. (7.13) goes to the all-gas limit at `x = 1`. |

## Candidate formulas

The per-length form implemented for audit/regression is:

```text
Delta p / L = 2 * f_m * G^2 / (D * rho_m)
```

with homogeneous mixture definitions:

```text
rho_m = rho_L * (1 - alpha_H) + rho_G * alpha_H

alpha_H = 1 / (1 + ((1 - x) / x) * (rho_G / rho_L))

f_m = 0.079 / Re_m^0.25

Re_m = G * D / mu_m

mu_m = x * mu_G + (1 - x) * mu_L
```

The helper allows `0 < x <= 1` so the source-stated all-gas limit is testable.

## Code-level candidate helpers

- `published_friction.moreno_quiben_th3337_candidate_mist_homogeneous_void_fraction`
- `published_friction.moreno_quiben_th3337_candidate_mist_mixture_density_kg_m3`
- `published_friction.moreno_quiben_th3337_candidate_mist_mixture_viscosity_pa_s`
- `published_friction.moreno_quiben_th3337_candidate_mist_friction_factor`
- `published_friction.moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m`

These helpers are regression/audit fixtures only. They are not called by
`CO2MathcadModel.run(...)`, `closure_state_from_model(...)`, or the guarded
published MSH/Friedel functions.

## SI regression fixture

Inputs:

```text
x = 0.8
G = 200 kg/(m^2 s)
D = 0.01 m
rho_L = 900 kg/m^3
rho_G = 10 kg/m^3
mu_L = 1.0e-3 Pa*s
mu_G = 1.0e-5 Pa*s
```

Expected audit values:

```text
alpha_H = 0.9972299169
rho_m = 12.4653739612 kg/m^3
mu_m = 0.000208 Pa*s
f_m = 0.0079778419
Delta p / L = 5120.0016535769 Pa/m
```

All-gas limit check at `x = 1` with the same `G`, `D`, `rho_G`, and `mu_G`:

```text
Delta p / L = 2988.5434844500 Pa/m
```

## Release blockers

- The project has no released WUT/TH3337 mist-regime classifier.
- Eq. (7.13) is one branch of Moreno Quiben's thesis flow-pattern pressure-drop
  model, not a standalone released MSH/Friedel/WUT runtime model.
- The full model still requires annular, slug/intermittent, stratified-wavy,
  slug+stratified-wavy, dryout, stratified and bubbly handling plus transition
  rules.
- No pointwise experimental pressure-drop reference case has been transcribed
  from TH3337 into project tests.
- Releasing this as runtime physics would require an explicit
  `release_basis="dissertation"` decision, `audited_source_ref`,
  `audited_equations`, source-scope limits, SI variable mapping for all required
  branches and reference tests.
