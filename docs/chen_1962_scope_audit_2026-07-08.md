# Chen 1962 applicability and geometry-scope audit 2026-07-08

Status: candidate_only / scope blocker narrowed, not released.

This audit answers the release-scope part of
`HTC-CHEN-1962-SOURCE-CANDIDATE`: can the Chen 1962 saturated convective
boiling HTC report be mapped to the current project geometry without an
unsupported extension?

## Source And Local Context

Primary file: `sources/primary/chen_1962_osti_4636495.pdf`.
Inventory record: `docs/primary_source_inventory.md`.

SHA256:
`5DDE91B1FE38B2CE6E4977AEE2A25A61BBEDC83C5A7214802496754E4989017E`.

Related candidate audits:

- `docs/chen_1962_formula_audit_2026-07-06.md`
- `docs/chen_1962_si_mapping_2026-07-07.md`
- `docs/chen_1962_validation_tables_2026-07-07.md`
- `docs/chen_1962_reference_value_audit_2026-07-08.md`
- `docs/chen_1962_hand_calculation_2026-07-08.md`

Project geometry evidence:

- `co2_geometry.FlowSection` records `kind`, `orientation`, `dz_m` and
  `heat_mode`.
- `LoopGeometry.evaporator_section(...)` defaults to a horizontal
  `evaporator` with `heat_mode="prescribed_qtr"`.
- `LoopGeometry.riser_section(...)` defaults to `orientation="vertical_up"`
  and `heat_mode="adiabatic"`.
- The current solver therefore has a heated horizontal evaporator and a
  separate vertical riser, not a single heated vertical axial test section.

## Source Applicability

The report's page 6 text-layer extraction defines the region of interest as:

- saturated two-phase fluid in convective flow;
- vertical, axial flow;
- stable flow;
- no slug flow;
- no liquid deficiency;
- heat flux less than critical flux.

The same page states that these conditions usually occur with annular or
annular-mist flow in an approximately 1-70 percent vapor-quality range.

Pages 18-19 repeat the annular/annular-mist basis and recommend the
correlation for saturated non-metallic fluids in convective flow. Page 19 says
water and organics are expected to be covered in approximately the same
1-70 percent vapor-quality range, while liquid metals would require
modification.

Table I includes mostly vertical tube/annulus data, with one downflow water
tube set. It is validation context only; it does not broaden the source into a
horizontal heated-evaporator correlation.

## Scope Decision

The maximum source-based release scope for this candidate is:

- saturated non-metallic fluid in convective boiling;
- heated vertical axial flow only (`vertical heated axial flow only`);
- stable annular or annular-mist style operation;
- no slug flow, no liquid deficiency and no CHF inference;
- vapor quality bounded by Chen's approximate source range
  `0.01 <= x <= 0.70`.

The project default heated evaporator is horizontal. Therefore a released
Chen 1962 adapter must not be silently applied to the default evaporator or to
a mixed horizontal/vertical loop. A future adapter may be released only if it
has an explicit vertical-heated-section mode or a geometry flag that refuses
horizontal and mixed-geometry use. Any broader horizontal use would be an
engineering extrapolation, not a primary-source release.

The existing candidate graph-to-SI helper already rejects vapor quality outside
`0.01 <= x <= 0.70`; that guard should be treated as the source maximum. A
project-specific release may narrow this range, but must not widen it without
new primary-source evidence.

## Release Impact

This audit closes the geometry/scope decision as follows:

- Chen 1962 is vertical-heated-flow HTC evidence only.
- The current horizontal evaporator remains unsupported for runtime Chen HTC;
  in release terms, the horizontal evaporator is unsupported by this source.
- The source quality guard is `0.01 <= x <= 0.70` unless narrowed.

It does not release `HTC-CHEN-1962-SOURCE-CANDIDATE`. Remaining release
blockers are reviewed `F/S` interpolation or authoritative tables, accepted
source-unit/SI and property-evaluation mapping, source/reference HTC tests or
accepted release-grade hand calculation, and regression tests proving dryout
and CHF are not inferred from this HTC source.
