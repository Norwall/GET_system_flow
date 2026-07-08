# Chen 1962 SI mapping audit 2026-07-07

This audit records the source-unit to SI mapping for the scan-verified Chen
1962 Eqs. (9), (17), and (18). It is candidate-only evidence. It does not
release a runtime heat-transfer correlation because the Fig. 7/Fig. 8
digitization still needs a release uncertainty decision after the rendered
review in `docs/chen_1962_graph_review_2026-07-08.md`,
property-evaluation conventions need
implementation decisions, and no source-based HTC reference value from the
report has been added.

Local source: `sources/primary/chen_1962_osti_4636495.pdf`.
Inventory cross-check: `docs/primary_source_inventory.md` records the local
source path and SHA256 for the OSTI scan.

## Source-unit convention

The nomenclature pages rendered from the local OSTI scan define an English
engineering unit system:

| Quantity | Source definition | Project SI variable/unit |
| --- | --- | --- |
| `h` | two-phase heat-transfer coefficient, `Btu/(hr ft^2 degF)` | HTC, `W/(m^2 K)` |
| `D` | diameter, `ft` | hydraulic diameter, `m` |
| `k` | thermal conductivity, `Btu/(hr ft degF)` | `W/(m K)` |
| `Cp` | heat capacity, `Btu/(lb degF)` | `J/(kg K)` |
| `G` | mass flow velocity, `lb/(hr ft^2)` | mass flux, `kg/(m^2 s)` |
| `q/A` | heat flux, `Btu/(hr ft^2)` | heat flux, `W/m^2` |
| `P` | pressure, `psf` | pressure, `Pa` |
| `DeltaP` | difference in vapor pressure corresponding to `DeltaT`, `psf` | `p_sat(T_w)-p_sat(T_s)`, `Pa` |
| `DeltaT` | superheat, `T_w - T_s`, `degF` interval | wall superheat, `K` interval |
| `lambda` | latent heat of vaporization, `Btu/lb` | latent heat, `J/kg` |
| `mu` | viscosity, `lb/(ft hr)` | dynamic viscosity, `Pa s` |
| `rho` | density, `lb/ft^3` | density, `kg/m^3` |
| `sigma` | vapor-liquid surface tension, `lb/ft` | surface tension, `N/m` |
| `T` | absolute temperature, `degR` | absolute temperature, `K` |
| `g_c` | gravitational constant | `32.174 ft lbm/(lbf s^2)` or `4.1697567e8 ft lbm/(lbf hr^2)` |

Important distinction: source `DeltaP` in Eq. (17) is the vapor-pressure
difference corresponding to wall superheat. It is not the boiler pressure
gradient `dP/dL`.

## Conversion constants

The candidate implementation path should keep Chen's original coefficient
`0.00122` in source units, not invent a new SI coefficient. Convert SI inputs
to the source units below, evaluate the original equations, then convert the
source HTC back to SI.

| Conversion | Value |
| --- | ---: |
| `1 Btu/(hr ft^2 degF)` | `5.678263341 W/(m^2 K)` |
| `1 Btu/(hr ft degF)` | `1.730734666 W/(m K)` |
| `1 Btu/(lb degF)` | `4186.8 J/(kg K)` |
| `1 lb/ft^3` | `16.018463374 kg/m^3` |
| `1 lb/(ft hr)` | `4.133788732e-4 Pa s` |
| `1 Btu/lb` | `2326.0 J/kg` |
| `1 lbf/ft` | `14.593902937 N/m` |
| `1 psf` | `47.880258980 Pa` |
| `1 psi` | `6894.757293 Pa` |
| `1 lb/(hr ft^2)` | `1.356229899e-3 kg/(m^2 s)` |
| `1 Btu/(hr ft^2)` | `3.154590745 W/m^2` |
| `1 ft` | `0.3048 m` |

## Candidate evaluation path

Given SI inputs and already-reviewed candidate values for `F` and `S`:

```text
D_ft       = D_m / 0.3048
k_src      = k_si / 1.730734666
Cp_src     = cp_si / 4186.8
rho_l_src  = rho_l_si / 16.018463374
rho_v_src  = rho_v_si / 16.018463374
mu_l_src   = mu_l_si / 4.133788732e-4
sigma_src  = sigma_si / 14.593902937
lambda_src = lambda_si / 2326.0
DeltaT_F   = DeltaT_K * 9/5
DeltaP_psf = DeltaP_Pa / 47.880258980
g_c_hr     = 4.1697567e8
```

Eq. (9), evaluated in source units:

```text
h_mac_src = 0.023 * Re_L^0.8 * Pr_L^0.4 * (k_src / D_ft) * F
```

Eq. (17), evaluated in source units:

```text
h_mic_src = 0.00122
  * k_src^0.79 * Cp_src^0.45 * rho_l_src^0.49 * g_c_hr^0.25
  / (sigma_src^0.5 * mu_l_src^0.29 * lambda_src^0.24 * rho_v_src^0.24)
  * DeltaT_F^0.24 * DeltaP_psf^0.75 * S
```

Eq. (18), converted back to SI:

```text
h_total_src = h_mic_src + h_mac_src
h_total_si  = h_total_src * 5.678263341
```

## Candidate code helper and hand calculation

`boiling_heat_transfer.chen_1962_candidate_heat_transfer_coefficient_si` now
implements the source-unit evaluation path above as a candidate-only helper.
It is deliberately not wired to `heat_transfer_model="chen_1962"` as a
released runtime HTC correlation. The helper is used to lock down unit
conversion and equation transcription while graph digitization, property
evaluation points, geometry scope, and source/reference validation remain open.

The accompanying code test uses this documented hand-calculation fixture:

```text
Re_L = 10000
Pr_L = 2.0
D = 0.01 m
k_L = 0.6 W/(m K)
Cp_L = 4200 J/(kg K)
rho_L = 958 kg/m^3
rho_v = 0.6 kg/m^3
mu_L = 2.8e-4 Pa s
sigma = 0.0589 N/m
lambda = 2.257e6 J/kg
DeltaT = 5 K
DeltaP = 18000 Pa
F = 3.0
S = 0.4
```

Candidate source-unit result:

```text
h_mac_src = 1524.7435663341 Btu/(hr ft^2 degF)
h_mic_src = 241.6266815044 Btu/(hr ft^2 degF)
h_total_src = 1766.3702478385 Btu/(hr ft^2 degF)
h_total_si = 10029.9154249347 W/(m^2 K)
```

This is a deterministic transcription/unit-conversion check, not a Chen report
validation point.

## Dimensionless factors

`Re_L`, `Pr_L`, `F`, `S`, `X_tt`, `x`, `z`, and density/viscosity ratios remain
dimensionless. The nomenclature defines vapor weight fraction `x`, liquid
weight fraction `z`, and:

```text
X_tt = (z/x)^0.9 * (rho_v/rho_L)^0.5 * (mu_L/mu_v)^0.1
```

Fig. 7 uses the reciprocal:

```text
1/X_tt = (x/z)^0.9 * (rho_L/rho_v)^0.5 * (mu_v/mu_L)^0.1
```

This mapping is locked as candidate-only code by:

```text
boiling_heat_transfer.chen_1962_candidate_inverse_martinelli_parameter
```

The candidate `F` helper is intentionally limited to the rendered Fig. 7 axis
range `0.1 <= 1/X_tt <= 100`. Values outside that range are rejected rather
than extrapolated.

Fig. 8 uses:

```text
R = Re_L * F^1.25
```

This mapping is locked as candidate-only code by:

```text
boiling_heat_transfer.chen_1962_candidate_two_phase_reynolds
```

The candidate `S` helper is intentionally limited to the rendered Fig. 8 axis
range `1.5e4 <= Re_L*F^1.25 <= 7e5`. Values outside that range are rejected
rather than extrapolated.

The exact property-evaluation points for a released runtime adapter must still
be fixed explicitly: liquid/vapor saturation properties, wall/saturation
superheat, and the pressure difference from saturation-pressure slope.

## End-to-end candidate composition

`boiling_heat_transfer.chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si`
now composes the candidate graph-axis and source-unit helpers:

```text
1/X_tt -> F_candidate(1/X_tt) -> R=Re_L*F^1.25 -> S_candidate(R)
```

Then it evaluates Eqs. (9), (17), and (18) through
`chen_1962_candidate_heat_transfer_coefficient_si`.

Before evaluating the graph path, the helper applies the source-scope vapor
quality guard from Chen pages 6 and 18-19:

```text
0.01 <= x <= 0.70
```

This is a candidate audit guard only. It prevents accidental extrapolation of
the report's stated quality scope, but it does not release the runtime HTC
model.

The accompanying code test uses the same SI fixture as the source-unit helper,
with vapor quality and vapor viscosity added:

```text
x = 0.2
mu_v = 1.2e-5 Pa s
```

Candidate intermediate values:

```text
1/X_tt = 8.3744338927
F = 11.4390861217
R = 210372.5940296686
S = 0.2220058995
```

Candidate end-to-end result:

```text
h_mac_src = 5813.8909896245 Btu/(hr ft^2 degF)
h_mic_src = 134.1063719014 Btu/(hr ft^2 degF)
h_total_src = 5947.9973615260 Btu/(hr ft^2 degF)
h_total_si = 33774.2953703176 W/(m^2 K)
```

This is still not a Chen report validation point. It is a deterministic
graph-to-SI composition check for the candidate audit path.

## Remaining release blockers

- Candidate graph digitization from
  `docs/chen_1962_graph_digitization_2026-07-07.md` has rendered-page review in
  `docs/chen_1962_graph_review_2026-07-08.md`, but still needs explicit
  acceptance as release proof or replacement by an authoritative table; the
  code-level plotted-domain guards prevent extrapolation but do not make the
  digitization release-grade.
- The code has candidate hand-calculation and graph-to-SI composition helpers,
  but no selectable runtime Chen HTC adapter is released.
- No source-based Chen report reference HTC value has been added.
- Tables I and II are transcribed in
  `docs/chen_1962_validation_tables_2026-07-07.md`, but they provide only
  condition ranges and average deviations, not pointwise HTC reference values.
- Geometry/scope remains vertical axial stable flow; horizontal evaporator use
  must stay blocked or separately justified.
- Dryout and CHF remain separate gates.
