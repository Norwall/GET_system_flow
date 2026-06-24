# Python port of GET CO2 Mathcad model

## What was reproduced
- Internal steady-state solver from the uploaded XMCD workbook for the CO2 case.
- Interpolated property tables and the nonlinear search for the circulation parameter f.
- Output quantities aligned with the worksheet/dissertation notation where possible: GG(0), GL(1), GL(0), chiG(1), phiG(1), DeltaP, etc.

## Cached workbook checks
- px_m10_Pa: expected=2647719.0, actual=2647719.0, rel_err=0.000e+00
- rx_m10_J_kg: expected=261716.868, actual=261716.868, rel_err=0.000e+00
- RV1_default: expected=8.008966711394417e-06, actual=8.008966711396668e-06, rel_err=2.811e-13
- R2x: expected=1.8356164383561646, actual=1.8356164383561646, rel_err=0.000e+00

## Scenario summary
| scenario                          |   qtr | converged   |       fff |    tav_C |    tmm_C |    tvih_C |   GG0_lph |   GL1_lph |   GL0_lph |   chiG1_mass |   phiG1_true |   deltaP_Pa |
|:----------------------------------|------:|:------------|----------:|---------:|---------:|----------:|----------:|----------:|----------:|-------------:|-------------:|------------:|
| xmcd_default                      | 76.68 | True        |  0.304814 | 0.158032 | 0.243746 | 0.0725632 | 253.254   |   77.1954 |   330.449 |    0.766393  |     0.969113 |    16031    |
| co2_lower_benchmark_qmin_table4_5 |  2.48 | True        | 67.6562   | 0.195579 | 0.236974 | 0.187403  |   8.19079 |  554.158  |   562.348 |    0.0145653 |     0.123854 |     5394.18 |
| co2_upper_benchmark_qmax_appG3    | 71.18 | True        |  0.390004 | 0.16005  | 0.24376  | 0.0766158 | 235.089   |   91.6857 |   326.774 |    0.719422  |     0.960819 |    15655.6  |
| moderate_regime_q20               | 20    | True        |  4.68445  | 0.182425 | 0.24331  | 0.12335   |  66.0547  |  309.43   |   375.485 |    0.175919  |     0.671231 |    11327.7  |
| hot_regime_q90                    | 90    | True        |  0.15508  | 0.153021 | 0.243692 | 0.0625369 | 297.246   |   46.097  |   343.343 |    0.865741  |     0.984044 |    16958.6  |

## Notes on validation
- The dissertation states that the working model takes evaporator length, condenser height, condenser temperature and heat load as inputs; the same input structure is used here.
- The dissertation chapter 4 / appendix G gives a CO2 benchmark for H=2.5 m, Li=200 m, tcon=0 C with qmax=71.18 W/m. In the Python port, this point is computable and some quantities are close (for example GG(0) ≈ 235.09 l/h), but the full critical-regime table is not reproduced exactly from the single XMCD workbook alone.
- The dissertation explicitly defines upper critical heat load through the special limiting condition f=0; that outer critical-load algorithm is not fully encoded in the uploaded workbook and therefore is not claimed as fully reproduced here.

## Files
- get_co2_model.py — model implementation
- get_co2_results.csv — scenario outputs
- get_co2_sweep.csv — load sweep outputs
- get_co2_checks.json — cached-value verification
- get_co2_sweep.png — sweep plot