from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Tuple


GeometrySource = Literal["mathcad_default", "designer", "manual_sections"]


@dataclass(frozen=True)
class FlowSection:
    id: str
    kind: str
    orientation: str
    length_m: float
    dz_m: float
    hydraulic_diameter_m: float
    roughness_m: float
    area_m2: float
    heat_mode: str = "adiabatic"

    @property
    def relative_roughness(self) -> float:
        return self.roughness_m / self.hydraulic_diameter_m

    @property
    def name(self) -> str:
        return self.id

    @property
    def section_kind(self) -> str:
        return self.kind

    @property
    def flow_area_m2(self) -> float:
        return self.area_m2


@dataclass(frozen=True)
class EvaporatorSection(FlowSection):
    pass


@dataclass(frozen=True)
class RiserSection(FlowSection):
    pass


@dataclass(frozen=True)
class CondenserSection(FlowSection):
    pass


@dataclass(frozen=True)
class DowncomerSection(FlowSection):
    pass


@dataclass(frozen=True)
class LoopGeometry:
    sections: Tuple[FlowSection, ...] = ()
    geometry_source: GeometrySource = "mathcad_default"
    inner_radius_m: float = 1.325e-2
    reference_diameter_1_m: float = 36.5e-3
    reference_diameter_2_m: float = 67e-3
    outlet_section_length_m: float = 6.5
    inlet_section_length_m: float = 10.5
    wall_roughness_m: float = 1e-4

    @property
    def hydraulic_diameter_m(self) -> float:
        if self.sections:
            return self._required_section("evaporator").hydraulic_diameter_m
        return 2.0 * self.inner_radius_m

    @property
    def flow_area_m2(self) -> float:
        if self.sections:
            return self._required_section("evaporator").area_m2
        return math.pi * self.inner_radius_m**2

    @property
    def relative_roughness(self) -> float:
        if self.sections:
            return self._required_section("evaporator").relative_roughness
        return self.wall_roughness_m / self.hydraulic_diameter_m

    @classmethod
    def from_sections(
        cls,
        sections: Tuple[FlowSection, ...],
        geometry_source: GeometrySource = "manual_sections",
    ) -> "LoopGeometry":
        geometry = cls(sections=tuple(sections), geometry_source=geometry_source)
        geometry.validate_current_solver_sections()
        evaporator = geometry._required_section("evaporator")
        condenser = geometry._required_section("condenser")
        downcomer = geometry._required_section("downcomer")
        return cls(
            sections=tuple(sections),
            geometry_source=geometry_source,
            inner_radius_m=0.5 * evaporator.hydraulic_diameter_m,
            outlet_section_length_m=condenser.length_m,
            inlet_section_length_m=downcomer.length_m,
            wall_roughness_m=evaporator.roughness_m,
        )

    def with_default_sections(self, evaporator_length_m: float, riser_height_m: float) -> "LoopGeometry":
        return LoopGeometry(
            sections=self.nominal_sections(
                evaporator_length_m=evaporator_length_m,
                riser_height_m=riser_height_m,
            ),
            geometry_source="mathcad_default",
            inner_radius_m=self.inner_radius_m,
            reference_diameter_1_m=self.reference_diameter_1_m,
            reference_diameter_2_m=self.reference_diameter_2_m,
            outlet_section_length_m=self.outlet_section_length_m,
            inlet_section_length_m=self.inlet_section_length_m,
            wall_roughness_m=self.wall_roughness_m,
        )

    def validate_current_solver_sections(self) -> None:
        if not self.sections:
            return
        required_kinds = {"evaporator", "riser", "condenser", "downcomer"}
        kinds = [section.kind for section in self.sections]
        unsupported = sorted(set(kinds) - required_kinds)
        if unsupported:
            raise ValueError(f"Unsupported geometry section kind for current solver: {unsupported!r}.")
        for kind in sorted(required_kinds):
            count = kinds.count(kind)
            if count != 1:
                raise ValueError(f"Current solver requires exactly one {kind!r} section, got {count}.")
        if self._required_section("riser").dz_m <= 0.0:
            raise ValueError("Riser section dz_m must be positive.")
        if self._required_section("downcomer").dz_m >= 0.0:
            raise ValueError("Downcomer section dz_m must be negative.")

    def _required_section(self, kind: str) -> FlowSection:
        matches = tuple(section for section in self.sections if section.kind == kind)
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {kind!r} section, got {len(matches)}.")
        return matches[0]

    def _section_or_default(self, kind: str, fallback: FlowSection) -> FlowSection:
        if not self.sections:
            return fallback
        return self._required_section(kind)

    def _section_like(
        self,
        base: FlowSection,
        *,
        length_m: float,
        dz_m: float,
        name: str,
    ) -> FlowSection:
        section_class = type(base)
        return section_class(
            id=name,
            kind=base.kind,
            orientation=base.orientation,
            length_m=length_m,
            dz_m=dz_m,
            hydraulic_diameter_m=base.hydraulic_diameter_m,
            roughness_m=base.roughness_m,
            area_m2=base.area_m2,
            heat_mode=base.heat_mode,
        )

    def evaporator_section(self, length_m: float, name: str = "evaporator") -> FlowSection:
        base = EvaporatorSection(
            id=name,
            kind="evaporator",
            orientation="horizontal",
            length_m=length_m,
            dz_m=0.0,
            hydraulic_diameter_m=self.hydraulic_diameter_m,
            roughness_m=self.wall_roughness_m,
            area_m2=self.flow_area_m2,
            heat_mode="prescribed_qtr",
        )
        section = self._section_or_default("evaporator", base)
        return self._section_like(section, length_m=length_m, dz_m=0.0, name=name)

    def riser_section(self, height_m: float, name: str = "riser") -> FlowSection:
        base = RiserSection(
            id=name,
            kind="riser",
            orientation="vertical_up",
            length_m=height_m,
            dz_m=height_m,
            hydraulic_diameter_m=self.hydraulic_diameter_m,
            roughness_m=self.wall_roughness_m,
            area_m2=self.flow_area_m2,
            heat_mode="adiabatic",
        )
        section = self._section_or_default("riser", base)
        if section.id == name:
            return section
        return self._section_like(section, length_m=section.length_m, dz_m=section.dz_m, name=name)

    def condenser_section(self, name: str = "condenser") -> FlowSection:
        base = CondenserSection(
            id=name,
            kind="condenser",
            orientation="horizontal",
            length_m=self.outlet_section_length_m,
            dz_m=0.0,
            hydraulic_diameter_m=self.hydraulic_diameter_m,
            roughness_m=self.wall_roughness_m,
            area_m2=self.flow_area_m2,
            heat_mode="saturation_boundary",
        )
        section = self._section_or_default("condenser", base)
        if section.id == name:
            return section
        return self._section_like(section, length_m=section.length_m, dz_m=section.dz_m, name=name)

    def downcomer_section(self, name: str = "downcomer") -> FlowSection:
        base = DowncomerSection(
            id=name,
            kind="downcomer",
            orientation="return_line",
            length_m=self.inlet_section_length_m,
            dz_m=0.0,
            hydraulic_diameter_m=self.hydraulic_diameter_m,
            roughness_m=self.wall_roughness_m,
            area_m2=self.flow_area_m2,
            heat_mode="adiabatic",
        )
        section = self._section_or_default("downcomer", base)
        if section.id == name:
            return section
        return self._section_like(section, length_m=section.length_m, dz_m=section.dz_m, name=name)

    def nominal_sections(self, evaporator_length_m: float, riser_height_m: float) -> Tuple[FlowSection, ...]:
        return (
            self.evaporator_section(length_m=evaporator_length_m),
            self.riser_section(height_m=riser_height_m),
            self.condenser_section(),
            DowncomerSection(
                id="downcomer",
                kind="downcomer",
                orientation="return_line",
                length_m=self.inlet_section_length_m,
                dz_m=-riser_height_m,
                hydraulic_diameter_m=self.hydraulic_diameter_m,
                roughness_m=self.wall_roughness_m,
                area_m2=self.flow_area_m2,
                heat_mode="adiabatic",
            ),
        )


def default_mathcad_geometry(evaporator_length_m: float, riser_height_m: float) -> LoopGeometry:
    return LoopGeometry().with_default_sections(
        evaporator_length_m=evaporator_length_m,
        riser_height_m=riser_height_m,
    )
