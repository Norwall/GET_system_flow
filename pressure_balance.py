from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PressureTerm:
    section_name: str
    term_kind: str
    value_pa: float
    source_formula_id: str
    description: str = ""

    def to_dict(self) -> dict[str, str | float]:
        return {
            "section_name": self.section_name,
            "term_kind": self.term_kind,
            "value_pa": self.value_pa,
            "source_formula_id": self.source_formula_id,
            "description": self.description,
        }


@dataclass(frozen=True)
class SectionPressureBalance:
    section_name: str
    section_kind: str
    orientation: str
    length_m: float
    dz_m: float
    hydraulic_diameter_m: float = 0.0
    roughness_m: float = 0.0
    relative_roughness: float = 0.0
    area_m2: float = 0.0
    heat_mode: str = ""
    delta_p_hydrostatic_pa: float = 0.0
    delta_p_friction_pa: float = 0.0
    delta_p_acceleration_pa: float = 0.0
    delta_p_local_pa: float = 0.0

    @property
    def delta_p_total_pa(self) -> float:
        return (
            self.delta_p_hydrostatic_pa
            + self.delta_p_friction_pa
            + self.delta_p_acceleration_pa
            + self.delta_p_local_pa
        )

    def terms(self) -> tuple[PressureTerm, ...]:
        return (
            PressureTerm(
                section_name=self.section_name,
                term_kind="hydrostatic",
                value_pa=self.delta_p_hydrostatic_pa,
                source_formula_id="PRESS-HYDROSTATIC-SECTION",
            ),
            PressureTerm(
                section_name=self.section_name,
                term_kind="friction",
                value_pa=self.delta_p_friction_pa,
                source_formula_id="FRIC-DARCY-MASS-FLUX",
            ),
            PressureTerm(
                section_name=self.section_name,
                term_kind="acceleration",
                value_pa=self.delta_p_acceleration_pa,
                source_formula_id="PRESS-ACCELERATION-MOMENTUM",
            ),
            PressureTerm(
                section_name=self.section_name,
                term_kind="local",
                value_pa=self.delta_p_local_pa,
                source_formula_id="PRESS-LOOP-BALANCE",
            ),
        )

    def to_dict(self) -> dict[str, str | float]:
        return {
            "section_name": self.section_name,
            "section_kind": self.section_kind,
            "orientation": self.orientation,
            "length_m": self.length_m,
            "dz_m": self.dz_m,
            "hydraulic_diameter_m": self.hydraulic_diameter_m,
            "roughness_m": self.roughness_m,
            "relative_roughness": self.relative_roughness,
            "area_m2": self.area_m2,
            "heat_mode": self.heat_mode,
            "delta_p_hydrostatic_pa": self.delta_p_hydrostatic_pa,
            "delta_p_friction_pa": self.delta_p_friction_pa,
            "delta_p_acceleration_pa": self.delta_p_acceleration_pa,
            "delta_p_local_pa": self.delta_p_local_pa,
            "delta_p_total_pa": self.delta_p_total_pa,
        }


@dataclass(frozen=True)
class LoopPressureBalance:
    sections: tuple[SectionPressureBalance, ...]
    driving_pressure_pa: float

    @property
    def total_hydrostatic_pa(self) -> float:
        return sum(section.delta_p_hydrostatic_pa for section in self.sections)

    @property
    def total_friction_pa(self) -> float:
        return sum(section.delta_p_friction_pa for section in self.sections)

    @property
    def total_acceleration_pa(self) -> float:
        return sum(section.delta_p_acceleration_pa for section in self.sections)

    @property
    def total_local_pa(self) -> float:
        return sum(section.delta_p_local_pa for section in self.sections)

    @property
    def total_resistance_pa(self) -> float:
        return self.total_friction_pa + self.total_acceleration_pa + self.total_local_pa

    @property
    def residual_pa(self) -> float:
        return self.total_resistance_pa + self.total_hydrostatic_pa

    def terms(self) -> tuple[PressureTerm, ...]:
        return tuple(term for section in self.sections for term in section.terms())

    def terms_as_dicts(self) -> tuple[dict[str, str | float], ...]:
        return tuple(term.to_dict() for term in self.terms())

    def sections_as_dicts(self) -> tuple[dict[str, str | float], ...]:
        return tuple(section.to_dict() for section in self.sections)

    def summary_string(self) -> str:
        return ";".join(
            (
                f"{section.section_name}:"
                f"hydro={section.delta_p_hydrostatic_pa:.6g},"
                f"friction={section.delta_p_friction_pa:.6g},"
                f"acceleration={section.delta_p_acceleration_pa:.6g},"
                f"local={section.delta_p_local_pa:.6g}"
            )
            for section in self.sections
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "sections": self.sections_as_dicts(),
            "terms": self.terms_as_dicts(),
            "driving_pressure_pa": self.driving_pressure_pa,
            "total_hydrostatic_pa": self.total_hydrostatic_pa,
            "total_friction_pa": self.total_friction_pa,
            "total_acceleration_pa": self.total_acceleration_pa,
            "total_local_pa": self.total_local_pa,
            "total_resistance_pa": self.total_resistance_pa,
            "residual_pa": self.residual_pa,
        }


def hydrostatic_pressure_pa(density_kg_m3: float, dz_m: float, gravity_m_s2: float = 9.81) -> float:
    return float(density_kg_m3) * float(gravity_m_s2) * float(dz_m)
