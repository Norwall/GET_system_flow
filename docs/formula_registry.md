# Formula and Property Registry

This registry starts with the property-package entries implemented in Checkpoint 1.
The full hydraulic and two-phase formula inventory remains part of Checkpoint 2.

## Scope and Status

| ID | Status | Code | Tests |
| --- | --- | --- | --- |
| `PROP-MATHCAD-CO2-TABLE` | MATHCAD_COMPATIBLE | `MathcadCO2SaturationProperties` | `tests/test_refrigerant_properties.py`, `tests/test_co2_properties_baseline.py` |
| `PROP-COOLPROP-CO2-HEOS` | PUBLISHED | `CoolPropSaturationProperties(fluid="CO2")` | `tests/test_refrigerant_properties.py` |
| `PROP-COOLPROP-NH3-HEOS` | PUBLISHED | `CoolPropSaturationProperties(fluid="NH3")` | `tests/test_refrigerant_properties.py` |
| `PROP-REFPROP-ADAPTER` | OPTIONAL_ADAPTER | `RefpropSaturationProperties` | `tests/test_refrigerant_properties.py` |

## Property Interface

All Checkpoint 1 backends expose saturated liquid/vapor state through:

```python
SaturationState(
    fluid,
    temperature_c,
    pressure_pa,
    dp_sat_dT_pa_per_k,
    h_l_j_kg,
    h_g_j_kg,
    latent_heat_j_kg,
    rho_l_kg_m3,
    rho_g_kg_m3,
    v_l_m3_kg,
    v_g_m3_kg,
    mu_l_pa_s,
    mu_g_pa_s,
    cp_l_j_kgk,
    cp_g_j_kgk,
    k_l_w_mk,
    k_g_w_mk,
    surface_tension_n_m,
)
```

Compatibility aliases are retained for the previous solver field names:
`latent_heat_j_per_kg`, `v_l_m3_per_kg`, `v_g_m3_per_kg`, and
`cp_l_j_per_kgk`.

## PROP-MATHCAD-CO2-TABLE

- Mathematical form: tabulated saturation-property interpolation from the legacy worksheet.
- Variables: `T_sat` in deg C; `p_sat` in Pa; `h_g - h_l` in J/kg; `rho`, `v`, `mu`, and liquid `cp`.
- Applicability: CO2/R744 only; Mathcad-compatible baseline mode.
- Source: `CO2.xmcd`; project documentation traces the tables to the original Mathcad worksheet and Vargaftik-style CO2 reference data.
- Code: `refrigerant_properties.MathcadCO2SaturationProperties`; compatibility name `co2_properties.CO2SaturationProperties`.
- Range policy: no implicit extrapolation by default; `allow_property_extrapolation=True` is explicit compatibility mode.
- Known limitation: the Mathcad table backend does not provide independent vapor `cp`, thermal conductivity, surface tension, or absolute enthalpy reference. Missing non-legacy fields are returned as `nan` where the solver does not consume them.

## PROP-COOLPROP-CO2-HEOS

- Mathematical form: CoolProp HEOS saturated-state property calls via `PropsSI`.
- Variables: saturation temperature or pressure, phase quality `Q=0` for liquid and `Q=1` for vapor.
- Applicability: CO2/R744/CarbonDioxide aliases in the CoolProp saturation range below the critical point.
- Primary EOS/reference: Span and Wagner, "A New Equation of State for Carbon Dioxide Covering the Fluid Region from the Triple Point Temperature to 1100 K at Pressures up to 800 MPa", J. Phys. Chem. Ref. Data, 1996, DOI `10.1063/1.555991`.
- Code: `refrigerant_properties.CoolPropSaturationProperties(fluid="CO2")`.
- Tests: saturated-state consistency, monotonic pressure, positive transport/thermal properties, range rejection, and near-critical diagnostics in `tests/test_refrigerant_properties.py`.

## PROP-COOLPROP-NH3-HEOS

- Mathematical form: CoolProp HEOS saturated-state property calls via `PropsSI`.
- Variables: saturation temperature or pressure, phase quality `Q=0` for liquid and `Q=1` for vapor.
- Applicability: NH3/R717/Ammonia aliases in the CoolProp saturation range below the critical point.
- Primary EOS/reference: Gao, Wu, Bell, and Lemmon, "Thermodynamic Properties of Ammonia for Temperatures from the Melting Line to 725 K and Pressures to 1000 MPa", J. Phys. Chem. Ref. Data, 2020.
- Code: `refrigerant_properties.CoolPropSaturationProperties(fluid="NH3")`.
- Tests: saturated-state consistency, monotonic pressure, positive transport/thermal properties, and alias normalization in `tests/test_refrigerant_properties.py`.

## PROP-REFPROP-ADAPTER

- Mathematical form: same `RefrigerantSaturationProperties` interface, using the CoolProp `REFPROP::` backend string.
- Applicability: optional NIST REFPROP adapter for supported fluids when a licensed REFPROP installation is available.
- Source: NIST REFPROP, https://www.nist.gov/srd/refprop.
- Code: `refrigerant_properties.RefpropSaturationProperties`.
- Failure mode: unavailable REFPROP raises `BackendUnavailableError`; the default test suite checks this path without requiring REFPROP installation.

## Guardrails

- New `published` property or closure models must add a registry entry before being used in validated/academic modes.
- Experimental or heuristic closures without a primary source must be marked `EXPERIMENTAL / NO PRIMARY SOURCE`.
- Property calls outside the backend saturation range must raise a clear range error unless extrapolation is explicitly enabled.
