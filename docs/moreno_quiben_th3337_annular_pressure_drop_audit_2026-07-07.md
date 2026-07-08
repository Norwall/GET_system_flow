# Moreno Quiben TH3337 annular pressure-drop audit 2026-07-07

Status: `candidate_only`. This document records a local dissertation audit
slice for Moreno Quiben TH3337, pages 119-120 and Eq. (7.1)-(7.5). It is not a
released WUT Part I/II, Friedel, MSH, dryout, CHF, or HTC model.

Local source: `sources/primary/moreno_quiben_2005_epfl_th3337.pdf`.
Inventory cross-check: `docs/primary_source_inventory.md` records SHA256
`B3FD9477D189C7720836C222BFD927BED34AD9E99CB4D1C188102423E26D1A77`.

Extraction check: `pypdf` text extraction on 2026-07-07 found the annular
region text on pages 119-120 and the model-comparison context on page 125.
The text layer confirms Eq. (7.1)-(7.5), but this audit still treats the helper
as candidate-only because the full flow-pattern pressure-drop model also
depends on regime classification, film thickness, void fraction and transition
logic that are not released in runtime.

## Page and equation map

| Pages | Evidence |
| --- | --- |
| 119 | Section 7.2.3 introduces the new two-phase pressure-drop model. For annular flow, the thesis assumes a simplified liquid film and gas core, neglects entrainment, and uses a uniform smooth film thickness. Eq. (7.1) gives `Delta p / L = 4*tau_i/(D - 2*delta)`. Eq. (7.2) uses the approximation `D >> delta`, giving `Delta p / L = 4*tau_i/D`. Eq. (7.3) defines the interfacial shear stress `tau_i = f_i*rho_G*(u_G-u_L)^2/2 approx f_i*rho_G*u_G^2/2` when `u_L << u_G`. |
| 120 | Eq. (7.4) gives the annular interfacial friction factor correlation. Eq. (7.5) gives the annular frictional pressure drop from `f_i`, tube length/diameter and gas velocity. |
| 125 | Table 7.2 records comparison context for the new method. It reports 82.30 percent of the database within 30 percent and 64.71 percent within 20 percent, but it does not provide pointwise reference cases for this helper. |

## Candidate formulas

With `D = 2R`, the annular interfacial friction factor is:

```text
f_i = 0.67
      * (delta / D)^1.2
      * (((rho_L - rho_G) * g * delta^2) / sigma)^(-0.4)
      * (mu_G / mu_L)^0.08
      * We_L^(-0.034)
```

The pressure-gradient form implemented for audit/regression is the Eq. (7.5)
per-length version:

```text
Delta p / L = 4 * f_i / D * rho_G * u_G^2 / 2
```

where the helper deliberately uses the approximate Eq. (7.3) branch
`u_L << u_G`; it does not implement a full two-velocity annular momentum
balance.

## Code-level candidate helpers

- `published_friction.moreno_quiben_th3337_candidate_annular_interfacial_friction_factor`
- `published_friction.moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m`

These helpers are regression/audit fixtures only. They are not called by
`CO2MathcadModel.run(...)`, `closure_state_from_model(...)`, or the guarded
published MSH/Friedel functions.

## SI regression fixture

Inputs:

```text
delta = 0.0005 m
D = 0.01 m
rho_L = 900 kg/m^3
rho_G = 30 kg/m^3
mu_L = 2.0e-4 Pa*s
mu_G = 1.2e-5 Pa*s
sigma = 0.02 N/m
We_L = 50
u_G = 8 m/s
g = 9.80665 m/s^2
```

Expected audit values:

```text
f_i = 0.0314880634
Delta p / L = 12091.4163488975 Pa/m
```

## Release blockers

- Film thickness `delta` is an input to the helper; the project has no released
  WUT/TH3337 annular film-thickness solver.
- Eq. (7.5) requires a released regime map and the annular-branch decision; the
  current published WUT Part I runtime remains `source_required`.
- The full TH3337 flow-pattern pressure-drop model includes slug/intermittent,
  stratified-wavy, slug+stratified-wavy, mist, dryout, stratified and bubbly
  handling. Only the annular branch is locked here.
- No pointwise experimental pressure-drop reference case has been transcribed
  from TH3337 into project tests.
- Releasing this as runtime physics would require an explicit
  `release_basis="dissertation"` decision, `audited_source_ref`,
  `audited_equations`, source-scope limits, SI variable mapping for all required
  branches and reference tests.
