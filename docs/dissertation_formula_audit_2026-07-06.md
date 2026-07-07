# Dissertation formula audit 2026-07-06

This audit records local dissertation evidence found during the Checkpoint 5-6
source-gate work. It is page-level audit guidance only. It does not release
runtime physics, does not replace the journal primary articles, and does not
change any `SOURCE_REQUIRED` gate to `released`. Local file intake and SHA256
records remain governed by `docs/primary_source_inventory.md`.

## Local candidates

| Candidate | Local file | SHA256 | Decision |
| --- | --- | --- | --- |
| `DISS-MORENO-QUIBEN-2005-EPFL-TH3337` | `sources/primary/moreno_quiben_2005_epfl_th3337.pdf` | `B3FD9477D189C7720836C222BFD927BED34AD9E99CB4D1C188102423E26D1A77` | `candidate_only` |
| `DISS-WOJTAN-2004-EPFL-TH2978` | `sources/primary/wojtan_2004_epfl_th2978.pdf` | `0F17826CA107DD8744E8AFA914E11FB422D5BC551589ACE5492B04F5669075D5` | `candidate_only` |

## Moreno Quiben TH3337 page map

Repository record:
`https://infoscience.epfl.ch/handle/20.500.14299/215783`.
Openaccess bitstream:
`https://infoscience.epfl.ch/server/api/core/bitstreams/005ec5e9-6a5a-49e9-812b-e31d942503b2/content`.
Pages 53-66 are the pressure-drop review span used for this candidate audit.

| Pages | Audit finding |
| --- | --- |
| 1, 5 | Title, author, EPFL thesis no. 3337, abstract, 2543 measured pressure-drop values, and stated purpose: pressure drops during evaporation in horizontal tubes. |
| 20-25 | Chapter 2 defines vapor quality, thermodynamic-equilibrium quality, enthalpy increase with heat input, void fraction, true and superficial velocities, mass velocity, and Reynolds numbers. Key equation numbers: (2.1)-(2.26). |
| 53-54 | Chapter 4 starts the pressure-drop model review. It defines total pressure drop as static plus momentum plus frictional pressure drop, states that horizontal tubes have zero static head, and gives the momentum pressure-drop expression in Eq. (4.2). |
| 54-63 | Empirical-method baseline: Lockhart-Martinelli, Bankoff, Cicchitti, Thom, Pierre, Baroczy, Chawla, and Chisholm are summarized before the Friedel/MSH sections. |
| 64-65 | Friedel section, Eqs. (4.40)-(4.47): `Delta p_frict = Delta p_L0 * phi_f0^2`; multiplier uses `E + 3.24 F H / (Fr_H^0.045 We_L^0.035)` with definitions for `Fr_H`, `E`, `F`, `H`, `We_L`, and homogeneous density. This is candidate guidance only because the Friedel 1979 paper or archival scan is still missing. |
| 66 | Muller-Steinhagen and Heck section, Eqs. (4.53)-(4.56): `(dp/dz)_frict = F(1 - x)^(1/3) + B x^3`, `F = A + 2(B - A)x`, with `A` and `B` as all-liquid and all-vapor frictional pressure gradients. This is candidate guidance only because the MSH 1986 article is still required for release. |
| 109-110 | Chapter 7 compares the measured database to Friedel, Gronnerud, and Muller-Steinhagen-Heck. It records that MSH is best of the three overall but still only predicts about one-half of the database within +/-20%. |
| 113-115 | Figures 7.3-7.5 show full-database predicted-vs-experimental comparisons for Friedel, Gronnerud, and Muller-Steinhagen-Heck. |
| 116-118 | New model setup: the thesis uses the Wojtan-Ursenbacher-Thome flow pattern map for data segregation. Table 7.1 records 1745 selected experimental values by flow regime. |
| 119-125 | New flow-pattern pressure-drop model. Candidate equation map: annular (7.1)-(7.5), slug/intermittent (7.6), stratified-wavy (7.7)-(7.12), mist (7.13)-(7.17), dryout (7.18)-(7.20), stratified (7.21)-(7.23), and comparison table 7.2. |
| 146 | Bibliography entries for Friedel 1979 and Friedel 1980. |
| 149 | Bibliography entry for Muller-Steinhagen and Heck 1986, Chemical Engineering and Processing, 20, 297-308. |
| 152 | Bibliography entries for Wojtan thesis no. 2978 and WUT Part I/Part II journal articles. |

## Moreno Quiben TH3337 text-layer formula guidance

The TH3337 text layer is sufficiently readable for pressure-drop formula
guidance. These formulas remain dissertation/secondary guidance only: Friedel
and Muller-Steinhagen-Heck still require the target primary paper or archival
scan before runtime release.

| Scope | Candidate formulas extracted from TH3337 | Release limit |
| --- | --- | --- |
| Friedel pressure drop, pp. 64-65, Eqs. (4.40)-(4.47) | `Delta p_frict = Delta p_L0 * phi_f0^2`; `phi_f0^2 = E + 3.24 * F * H / (Fr_H^0.045 * We_L^0.035)`; `Fr_H = G^2/(g*D*rho_h^2)`; `E = (1-x)^2 + x^2*rho_L*f_G0/(rho_G*f_L0)`; `F = x^0.78*(1-x)^0.224`; `H = (rho_L/rho_G)^0.91*(mu_G/mu_L)^0.19*(1 - mu_G/mu_L)^0.7`; `We_L = G^2*D/(sigma*rho_h)`; `rho_h = (x/rho_G + (1-x)/rho_L)^-1`. TH3337 states applicability to vertical upflow and horizontal flow, `0 <= x < 1`, and good behavior when `mu_L/mu_G < 1000`. | Candidate guidance only. The Friedel 1979/1980 primary source must verify the exact exponents, multiplier naming, friction-factor convention, homogeneous density convention and applicability limits. |
| Muller-Steinhagen-Heck pressure drop, p. 66, Eqs. (4.53)-(4.56) | `(dp/dz)_frict = F*(1-x)^(1/3) + B*x^3`; `F = A + 2*(B-A)*x`; `A = (dp/dz)_L0 = f_L0*2*G^2/(D*rho_L)`; `B = (dp/dz)_G0 = f_G0*2*G^2/(D*rho_G)`. TH3337 says the friction factors come from Eqs. (4.32)-(4.33), i.e. all-liquid/all-gas Reynolds-number forms. | Candidate guidance only. The MSH 1986 article must verify the exact interpolation, all-liquid/all-gas definitions, friction-factor convention and mass-flux convention. |
| Flow-pattern pressure-drop model, pp. 119-125, Eqs. (7.1)-(7.23) | Annular region uses `Delta p/L = 4*tau_i/D`, `tau_i = f_i*rho_G*(u_G-u_L)^2/2 approx f_i*rho_G*u_G^2/2`, `(f_i)_annular = 0.67*(delta/(2R))^1.2*(((rho_L-rho_G)*g*delta^2)/sigma)^-0.4*(mu_G/mu_L)^0.08*We_L^-0.034`, and `(Delta p)_annular = 4*(f_i)_annular*(L/D)*rho_G*u_G^2/2`. Slug/intermittent and slug/stratified-wavy use void-fraction interpolation to the annular or stratified-wavy branch. Mist uses homogeneous density/void fraction and Cicchitti viscosity. Dryout uses linear interpolation between `xdi` and `xde`. Stratified uses `theta_strat`/`theta_dry`-weighted friction factors. | This is Moreno Quiben's thesis pressure-drop model, not a WUT Part I/II release. It is useful for identifying WUT map dependencies and test cases, but runtime release requires an explicit scope decision and reference tests. |
| Dryout boundaries cited in TH3337 pressure-drop model, p. 124, Eqs. (7.19)-(7.20) | `xdi = 0.58*exp(0.52 - 0.235*We_G^0.17*Fr_G^0.37*(rho_G/rho_L)^0.25*(q/qcrit)^0.70)`; `xde = 0.61*exp(0.57 - 5.8e-3*We_G^0.38*Fr_G^0.15*(rho_G/rho_L)^-0.09*(q/qcrit)^0.27)`. TH3337 states these are equivalent to Eqs. (3.54) and (3.55), proposed by Wojtan et al. | Candidate dryout-boundary guidance only. It does not release project dryout/CHF logic or WUT Part II heat-transfer logic without primary-source audit and tests. |

## Wojtan TH2978 page map

Repository record:
`https://infoscience.epfl.ch/handle/20.500.14299/212227`.
Openaccess bitstream:
`https://infoscience.epfl.ch/server/api/core/bitstreams/285f44f3-559e-4d9d-ada4-233895ecd47e/content`.

| Pages | Audit finding |
| --- | --- |
| 1 | Title page confirms EPFL thesis no. 2978, author Leszek Wojtan, advisor J. Thome, title, and 2004 date. |
| 9-13 | The table of contents indicates chapters for main terms, two-phase flow pattern maps, experimental void fraction, dynamic void fraction measurements, heat transfer in stratified-wavy flow, and dryout-zone heat transfer. The PDF text layer is partly custom-encoded, so extracted text is not reliable enough for formula release. |
| 172-183 | The text layer exposes dryout markers `xdi` and `xde` in figure captions, but surrounding formulas are not reliably extractable. These pages require OCR/manual audit before any WUT/HTC release decision. |

## Release decision

- `DISS-MORENO-QUIBEN-2005-EPFL-TH3337` is useful audit guidance for
  two-phase pressure-drop definitions, Friedel, Muller-Steinhagen-Heck, and a
  flow-pattern pressure-drop model. The text layer provides candidate formulas
  for Friedel Eqs. (4.40)-(4.47), Muller-Steinhagen-Heck Eqs. (4.53)-(4.56),
  and the thesis flow-pattern pressure-drop model Eqs. (7.1)-(7.23), but it
  does not release the Friedel, MSH, WUT, dryout or HTC gates.
- `DISS-WOJTAN-2004-EPFL-TH2978` is useful local context for WUT map/HTC/dryout
  work, but its current text extraction is not enough for page/equation release
  evidence and requires OCR/manual audit.
- Runtime release still requires either the full target primary article or an
  explicit dissertation-based release decision, exact page/equation references,
  SI convention mapping, applicability limits, and numerical reference tests.
