# Wojtan / TH3337 dryout-boundary candidate audit 2026-07-07

This note records the candidate-only dryout-boundary transcription now locked
by tests in `boiling_heat_transfer.py`. It is not a release record for WUT
Part I, WUT Part II, dryout, CHF, or heat-transfer runtime logic.

## Evidence chain

- Local source: `sources/primary/moreno_quiben_2005_epfl_th3337.pdf`.
- Inventory: `docs/primary_source_inventory.md`, SHA256
  `B3FD9477D189C7720836C222BFD927BED34AD9E99CB4D1C188102423E26D1A77`.
- Formula map: `docs/dissertation_formula_audit_2026-07-06.md`.
- Page/equation scope: Moreno Quiben TH3337 p. 124, Eqs. (7.19)-(7.20).
- Source status: `candidate_only_not_runtime_released`.

TH3337 states that the formulas are equivalent to Eqs. (3.54) and (3.55)
proposed by Wojtan et al. The target WUT journal articles remain metadata-only
in `docs/source_gate_manifest.json`, so this candidate cannot release the
project WUT Part I/Part II source gates.

## Candidate formulas

```text
xdi = 0.58*exp(0.52 - 0.235*We_G^0.17*Fr_G^0.37*(rho_G/rho_L)^0.25*(q/qcrit)^0.70)
xde = 0.61*exp(0.57 - 5.8e-3*We_G^0.38*Fr_G^0.15*(rho_G/rho_L)^-0.09*(q/qcrit)^0.27)
```

where `xdi` is dryout inception quality, `xde` is dryout completion quality,
`We_G` is the gas Weber number, `Fr_G` is the gas Froude number, `rho_G/rho_L`
is the gas-to-liquid density ratio, and `q/qcrit` is the heat-flux ratio used
by the cited TH3337 expression.

## Code lock

The candidate helper functions are:

- `boiling_heat_transfer.wojtan_th3337_candidate_dryout_inception_quality`
- `boiling_heat_transfer.wojtan_th3337_candidate_dryout_completion_quality`
- `boiling_heat_transfer.wojtan_th3337_candidate_dryout_boundaries`

They are intentionally not connected to `CO2MathcadModel.run(...)`,
`RefrigerantLoopModel.run(...)`, `dryout_limit`, or `critical_loads.py`.

## Regression point

For `We_G=200`, `Fr_G=20`, `rho_G=20 kg/m^3`, `rho_L=1000 kg/m^3`, and
`q/qcrit=1`, the candidate helper returns:

```text
xdi = 0.5047352096
xde = 0.9791233757
```

The regression lives in `tests/test_boiling_diagnostics.py` and proves the
helper is a transcription/audit aid, while runtime dryout still reports
`not_evaluated_source_required`.

## Release blockers

Before any runtime dryout or WUT HTC release:

1. Obtain the target WUT Part I/Part II journal article full text, or formally
   accept a dissertation-specific release basis.
2. Audit all transition, dryout, mist and stratified-wavy equations with page
   and equation references.
3. Define the source variable mapping to project state variables, including
   `qcrit` coupling and Part I map dependencies.
4. Add source/reference dryout or HTC test points.
5. Keep hydrodynamic `critical_loads.py` qcrit separate from dryout/CHF until a
   source-specific dryout/CHF correlation is released.
