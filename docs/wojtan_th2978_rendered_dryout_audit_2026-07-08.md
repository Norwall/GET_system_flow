# Wojtan TH2978 rendered dryout audit 2026-07-08

Status: `candidate_only`. This note records a rendered-page audit of the local
EPFL TH2978 dissertation pages around the dryout and mist-flow chapter. It
extends `docs/wojtan_th2978_text_layer_audit_2026-07-08.md` by checking page
images instead of only the custom-encoded text layer.

Local source: `sources/primary/wojtan_2004_epfl_th2978.pdf`.
Inventory: `docs/primary_source_inventory.md`.
Render tool: PyMuPDF 1.28.0, workspace-local `.deps` install, page images
written under `.tmp/th2978_render` for manual inspection.

It does not release WUT Part I, WUT Part II, project dryout, project CHF, or a
runtime heat-transfer model. It locks a candidate transcription of TH2978
dryout-limit definitions and equations for audit/regression use only.

## Rendered Pages

| Human page | Rendered finding |
| ---: | --- |
| 172 | Figure 7.11 shows R-22 experimental heat-transfer coefficients in the 13.84 mm test section at `Tsat = 5 C`, `q = 57.5 kW/m^2`, and `G = 300..700 kg/(m^2 s)`, with plotted `xdi` and `xde` markers. |
| 173 | Figures 7.12 and 7.13 show R-22 plots for `q = 37.5` and `17.5 kW/m^2`; they are plotted data, not tabulated reference HTC values. |
| 174 | The prose is readable and defines the experimental selection logic: `xdi` is selected from the point after a heat-flux drop larger than 10 percent from the initial value, and `xde` is selected at the first mist-flow point. The page also states that adjacent experimental vapor-quality points are separated by about `0.03..0.05`. |
| 175-177 | Figures 7.14-7.18 show R-410A plotted heat-transfer coefficients for 13.84 mm and 8.00 mm test sections; these figures provide digitization candidates and operating-condition context only. |
| 178 | Figure 7.19 plots dryout inception/completion markers versus mass velocity; Section 7.4.2 defines dryout as a range between `xdi` and `xde`, not a single step transition. |
| 179 | Figure 7.20 shows the dryout-zone schematic. The page gives Mori predecessor regimes S1/S2 and Eqs. (7.33)-(7.36). |
| 180 | The page gives Mori S3 Eqs. (7.37)-(7.42), dimensionless definitions Eqs. (7.43)-(7.45), and the selection procedure Eq. (7.46). |
| 181 | Figure 7.21 compares the Mori predecessor procedure with the experimental dryout points and is validation context only. |
| 182 | The prose explains why the earlier procedure is extended with heat-flux effects before the final TH2978 dryout-limit equations. |
| 183 | The page gives the optimized TH2978 dryout-limit equations, Eqs. (7.47)-(7.48), used for the candidate helper documented below. |
| 184 | Section 7.4.3 begins the flow-pattern-map update and gives Eq. (7.49). This is a separate WUT map dependency and is not released by this dryout-limit audit. |

## Candidate Equations

Rendered page 183 gives the optimized dryout inception and completion limits:

```text
xdi = 0.58 * exp(
    0.52
    - 0.235 * We_V^0.17 * Fr_V^0.37 * (rho_V/rho_L)^0.25 * (q/qcrit)^0.70
)

xde = 0.61 * exp(
    0.57
    - 5.8e-3 * We_V^0.38 * Fr_V^0.15 * (rho_V/rho_L)^-0.09 * (q/qcrit)^0.27
)
```

Rendered page 180 gives the dimensionless groups for the Mori predecessor
equations:

```text
Fr_V = G^2 / (g * D * rho_V * (rho_L - rho_V))
Re_V = G * D / mu_V
We_V = G^2 * D / (rho_V * sigma)
```

The TH2978 final Eqs. (7.47)-(7.48) use `We_V`, `Fr_V`, `rho_V/rho_L`, and
`q/qcrit`. The candidate code helpers take these dimensionless groups directly
because project `qcrit` is a hydrodynamic diagnostic and is not the same as a
released CHF/dryout source.

## Code Fixture

Candidate helpers:

- `boiling_heat_transfer.wojtan_th2978_candidate_dryout_inception_quality`
- `boiling_heat_transfer.wojtan_th2978_candidate_dryout_completion_quality`
- `boiling_heat_transfer.wojtan_th2978_candidate_dryout_limits`

For the regression fixture
`We_V = 200`, `Fr_V = 20`, `rho_V/rho_L = 20/1000`, and `q/qcrit = 1`:

| Quantity | Candidate value |
| --- | ---: |
| `xdi` | `0.5047352096` |
| `xde` | `0.9791233757` |

The same formula family was previously available through Moreno Quiben TH3337
candidate guidance (`docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md`).
This rendered TH2978 audit provides the direct dissertation-page transcription
for Eqs. (7.47)-(7.48), but it still does not provide release-grade runtime
scope, source reference points, or a guard-removal decision.

## Remaining Blockers

- Digitized points from Figures 7.11-7.19 are not yet turned into reference
  tests.
- Eq. (7.49) and the wider flow-pattern-map update in Section 7.4.3 are not
  audited into a WUT Part I release.
- The Part II heat-transfer model for stratified-wavy, dryout and mist flow is
  not released.
- Project dryout/CHF diagnostics must remain separate from these candidate
  dryout-quality limits.
