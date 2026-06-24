from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class FlowSection:
    name: str
    section_kind: str
    orientation: str
    length_m: float
    hydraulic_diameter_m: float
    flow_area_m2: float
    relative_roughness: float


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
    inner_radius_m: float = 1.325e-2
    reference_diameter_1_m: float = 36.5e-3
    reference_diameter_2_m: float = 67e-3
    outlet_section_length_m: float = 6.5
    inlet_section_length_m: float = 10.5
    wall_roughness_m: float = 1e-4

    @property
    def hydraulic_diameter_m(self) -> float:
        return 2.0 * self.inner_radius_m

    @property
    def flow_area_m2(self) -> float:
        return math.pi * self.inner_radius_m**2

    @property
    def relative_roughness(self) -> float:
        return self.wall_roughness_m / self.hydraulic_diameter_m

    def evaporator_section(self, length_m: float, name: str = "evaporator") -> EvaporatorSection:
        return EvaporatorSection(
            name=name,
            section_kind="evaporator",
            orientation="horizontal",
            length_m=length_m,
            hydraulic_diameter_m=self.hydraulic_diameter_m,
            flow_area_m2=self.flow_area_m2,
            relative_roughness=self.relative_roughness,
        )

    def riser_section(self, height_m: float, name: str = "riser") -> RiserSection:
        return RiserSection(
            name=name,
            section_kind="riser",
            orientation="vertical_up",
            length_m=height_m,
            hydraulic_diameter_m=self.hydraulic_diameter_m,
            flow_area_m2=self.flow_area_m2,
            relative_roughness=self.relative_roughness,
        )

    def condenser_section(self, name: str = "condenser") -> CondenserSection:
        return CondenserSection(
            name=name,
            section_kind="condenser",
            orientation="horizontal",
            length_m=self.outlet_section_length_m,
            hydraulic_diameter_m=self.hydraulic_diameter_m,
            flow_area_m2=self.flow_area_m2,
            relative_roughness=self.relative_roughness,
        )

    def downcomer_section(self, name: str = "downcomer") -> DowncomerSection:
        return DowncomerSection(
            name=name,
            section_kind="downcomer",
            orientation="return_line",
            length_m=self.inlet_section_length_m,
            hydraulic_diameter_m=self.hydraulic_diameter_m,
            flow_area_m2=self.flow_area_m2,
            relative_roughness=self.relative_roughness,
        )

    def nominal_sections(self, evaporator_length_m: float, riser_height_m: float) -> Tuple[FlowSection, ...]:
        return (
            self.evaporator_section(length_m=evaporator_length_m),
            self.riser_section(height_m=riser_height_m),
            self.condenser_section(),
            self.downcomer_section(),
        )
