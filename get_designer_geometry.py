from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from co2_geometry import (
    CondenserSection,
    DowncomerSection,
    EvaporatorSection,
    FlowSection,
    LoopGeometry,
    RiserSection,
)


VALID_SEGMENT_KINDS = {
    "evaporator",
    "riser",
    "condenser",
    "downcomer",
    "connector",
}
VALID_THERMAL_MODES = {"prescribed_qtr"}
VALID_SOLVER_MODES = {"worksheet_compatible", "distributed_steady"}
VALID_CLOSURE_MODELS = {
    "worksheet_compatible",
    "homogeneous_equilibrium",
    "zivi",
    "regime_aware",
    "experimental_regime_aware",
}

DEFAULT_SCENARIO_DIR = Path("artifacts") / "scenarios"


class ScenarioValidationError(ValueError):
    """Raised when a designer scenario cannot be converted to solver inputs."""


@dataclass(frozen=True)
class DesignerNode:
    id: str
    x_m: float
    z_m: float


@dataclass(frozen=True)
class DesignerSegment:
    id: str
    start_node_id: str
    end_node_id: str
    kind: str
    diameter_m: float | None = None
    roughness_m: float | None = None


@dataclass(frozen=True)
class ThermalConfig:
    mode: str = "prescribed_qtr"
    qtr_W_m: float = 76.68


@dataclass(frozen=True)
class SoilLayer:
    name: str = "soil"
    top_z_m: float = 0.0
    bottom_z_m: float = -10.0
    thermal_conductivity_W_mK: float = 1.5
    volumetric_heat_capacity_J_m3K: float = 2.0e6
    latent_heat_J_m3: float = 8.0e7
    initial_temperature_C: float = -1.0


@dataclass(frozen=True)
class SoilConfig:
    mode: str = "dynamic_placeholder"
    surface_z_m: float = 0.0
    layers: tuple[SoilLayer, ...] = field(default_factory=lambda: (SoilLayer(),))


@dataclass(frozen=True)
class SolverConfig:
    tcon_C: float = 0.0
    mode: str = "worksheet_compatible"
    closure_model: str = "worksheet_compatible"
    H_override_m: float | None = None


@dataclass(frozen=True)
class GETScenario:
    scenario_id: str
    name: str
    nodes: tuple[DesignerNode, ...]
    segments: tuple[DesignerSegment, ...]
    thermal: ThermalConfig = field(default_factory=ThermalConfig)
    soil: SoilConfig = field(default_factory=SoilConfig)
    solver: SolverConfig = field(default_factory=SolverConfig)


@dataclass(frozen=True)
class DerivedSegment:
    id: str
    kind: str
    start_node_id: str
    end_node_id: str
    dx_m: float
    dz_m: float
    length_m: float
    angle_deg: float
    orientation: str
    hydraulic_diameter_m: float
    roughness_m: float
    area_m2: float
    relative_roughness: float
    heat_mode: str


@dataclass(frozen=True)
class DerivedGeometry:
    segments: tuple[DerivedSegment, ...]
    total_length_m: float
    evaporator_length_m: float
    evaporator_mean_z_m: float
    evaporator_depth_m: float
    top_z_m: float
    geometric_head_m: float
    H_m: float
    qtr_W_m: float
    heat_power_W: float

    def to_loop_geometry(self) -> LoopGeometry:
        sections: list[FlowSection] = []
        section_classes = {
            "evaporator": EvaporatorSection,
            "riser": RiserSection,
            "condenser": CondenserSection,
            "downcomer": DowncomerSection,
        }
        for segment in self.segments:
            if segment.kind not in section_classes:
                raise ScenarioValidationError(
                    f"Segment kind {segment.kind!r} cannot be used by the current CO2 solver."
                )
            section_class = section_classes[segment.kind]
            sections.append(
                section_class(
                    id=segment.id,
                    kind=segment.kind,
                    orientation=segment.orientation,
                    length_m=segment.length_m,
                    dz_m=segment.dz_m,
                    hydraulic_diameter_m=segment.hydraulic_diameter_m,
                    roughness_m=segment.roughness_m,
                    area_m2=segment.area_m2,
                    heat_mode=segment.heat_mode,
                )
            )
        try:
            return LoopGeometry.from_sections(tuple(sections), geometry_source="designer")
        except ValueError as exc:
            raise ScenarioValidationError(str(exc)) from exc

    def to_solver_inputs(self, scenario: GETScenario) -> dict[str, float | str | LoopGeometry]:
        if self.evaporator_length_m <= 0.0:
            raise ScenarioValidationError("Scenario must include at least one evaporator segment.")
        if self.H_m <= 0.0:
            raise ScenarioValidationError("Derived or overridden H must be positive before running the CO2 solver.")
        if self.qtr_W_m <= 0.0:
            raise ScenarioValidationError("qtr_W_m must be positive before running the CO2 solver.")
        return {
            "H": self.H_m,
            "qtr": self.qtr_W_m,
            "Li": self.evaporator_length_m,
            "tcon": scenario.solver.tcon_C,
            "mode": scenario.solver.mode,
            "closure_model": scenario.solver.closure_model,
            "geometry": self.to_loop_geometry(),
        }


def default_scenario() -> GETScenario:
    return GETScenario(
        scenario_id="demo-get-profile",
        name="Demo GET profile",
        nodes=(
            DesignerNode(id="n1", x_m=0.0, z_m=-2.0),
            DesignerNode(id="n2", x_m=200.0, z_m=-2.0),
            DesignerNode(id="n3", x_m=200.0, z_m=0.5),
            DesignerNode(id="n4", x_m=206.5, z_m=0.5),
            DesignerNode(id="n5", x_m=0.0, z_m=-2.0),
        ),
        segments=(
            DesignerSegment(id="s1", start_node_id="n1", end_node_id="n2", kind="evaporator"),
            DesignerSegment(id="s2", start_node_id="n2", end_node_id="n3", kind="riser"),
            DesignerSegment(id="s3", start_node_id="n3", end_node_id="n4", kind="condenser"),
            DesignerSegment(id="s4", start_node_id="n4", end_node_id="n5", kind="downcomer"),
        ),
        thermal=ThermalConfig(qtr_W_m=76.68),
        solver=SolverConfig(tcon_C=0.0, mode="distributed_steady", closure_model="worksheet_compatible"),
    )


def scenario_from_dict(data: Mapping[str, Any]) -> GETScenario:
    scenario_id = _optional_str(data, "scenario_id", "untitled")
    name = _optional_str(data, "name", scenario_id)
    nodes = tuple(_node_from_dict(item) for item in _required_list(data, "nodes"))
    segments = tuple(_segment_from_dict(item) for item in _required_list(data, "segments"))
    scenario = GETScenario(
        scenario_id=scenario_id,
        name=name,
        nodes=nodes,
        segments=segments,
        thermal=_thermal_from_dict(_optional_mapping(data, "thermal")),
        soil=_soil_from_dict(_optional_mapping(data, "soil")),
        solver=_solver_from_dict(_optional_mapping(data, "solver")),
    )
    validate_scenario(scenario)
    return scenario


def scenario_to_dict(scenario: GETScenario) -> dict[str, Any]:
    return {
        "scenario_id": scenario.scenario_id,
        "name": scenario.name,
        "nodes": [{"id": node.id, "x_m": node.x_m, "z_m": node.z_m} for node in scenario.nodes],
        "segments": [
            {
                "id": segment.id,
                "start_node_id": segment.start_node_id,
                "end_node_id": segment.end_node_id,
                "kind": segment.kind,
                "diameter_m": segment.diameter_m,
                "roughness_m": segment.roughness_m,
            }
            for segment in scenario.segments
        ],
        "thermal": {
            "mode": scenario.thermal.mode,
            "qtr_W_m": scenario.thermal.qtr_W_m,
        },
        "soil": {
            "mode": scenario.soil.mode,
            "surface_z_m": scenario.soil.surface_z_m,
            "layers": [
                {
                    "name": layer.name,
                    "top_z_m": layer.top_z_m,
                    "bottom_z_m": layer.bottom_z_m,
                    "thermal_conductivity_W_mK": layer.thermal_conductivity_W_mK,
                    "volumetric_heat_capacity_J_m3K": layer.volumetric_heat_capacity_J_m3K,
                    "latent_heat_J_m3": layer.latent_heat_J_m3,
                    "initial_temperature_C": layer.initial_temperature_C,
                }
                for layer in scenario.soil.layers
            ],
        },
        "solver": {
            "tcon_C": scenario.solver.tcon_C,
            "mode": scenario.solver.mode,
            "closure_model": scenario.solver.closure_model,
            "H_override_m": scenario.solver.H_override_m,
        },
    }


def derived_geometry_to_dict(geometry: DerivedGeometry) -> dict[str, Any]:
    return {
        "segments": [
            {
                "id": segment.id,
                "kind": segment.kind,
                "start_node_id": segment.start_node_id,
                "end_node_id": segment.end_node_id,
                "dx_m": segment.dx_m,
                "dz_m": segment.dz_m,
                "length_m": segment.length_m,
                "angle_deg": segment.angle_deg,
                "orientation": segment.orientation,
                "hydraulic_diameter_m": segment.hydraulic_diameter_m,
                "roughness_m": segment.roughness_m,
                "area_m2": segment.area_m2,
                "relative_roughness": segment.relative_roughness,
                "heat_mode": segment.heat_mode,
            }
            for segment in geometry.segments
        ],
        "total_length_m": geometry.total_length_m,
        "evaporator_length_m": geometry.evaporator_length_m,
        "evaporator_mean_z_m": geometry.evaporator_mean_z_m,
        "evaporator_depth_m": geometry.evaporator_depth_m,
        "top_z_m": geometry.top_z_m,
        "geometric_head_m": geometry.geometric_head_m,
        "H_m": geometry.H_m,
        "qtr_W_m": geometry.qtr_W_m,
        "heat_power_W": geometry.heat_power_W,
    }


def validate_scenario(scenario: GETScenario) -> None:
    if not scenario.scenario_id.strip():
        raise ScenarioValidationError("scenario_id must not be empty.")
    node_ids = [node.id for node in scenario.nodes]
    if len(node_ids) != len(set(node_ids)):
        raise ScenarioValidationError("Node ids must be unique.")
    segment_ids = [segment.id for segment in scenario.segments]
    if len(segment_ids) != len(set(segment_ids)):
        raise ScenarioValidationError("Segment ids must be unique.")
    node_id_set = set(node_ids)
    for segment in scenario.segments:
        if segment.kind not in VALID_SEGMENT_KINDS:
            raise ScenarioValidationError(f"Unsupported segment kind: {segment.kind!r}.")
        if segment.start_node_id not in node_id_set:
            raise ScenarioValidationError(f"Unknown start node {segment.start_node_id!r} in segment {segment.id!r}.")
        if segment.end_node_id not in node_id_set:
            raise ScenarioValidationError(f"Unknown end node {segment.end_node_id!r} in segment {segment.id!r}.")
        if segment.start_node_id == segment.end_node_id:
            raise ScenarioValidationError(f"Segment {segment.id!r} must connect two different nodes.")
        if segment.diameter_m is not None and segment.diameter_m <= 0.0:
            raise ScenarioValidationError(f"Segment {segment.id!r} diameter_m must be positive.")
        if segment.roughness_m is not None and segment.roughness_m < 0.0:
            raise ScenarioValidationError(f"Segment {segment.id!r} roughness_m must be non-negative.")
    if scenario.thermal.mode not in VALID_THERMAL_MODES:
        raise ScenarioValidationError(f"Unsupported thermal mode: {scenario.thermal.mode!r}.")
    if scenario.thermal.qtr_W_m < 0.0:
        raise ScenarioValidationError("qtr_W_m must be non-negative.")
    if scenario.solver.mode not in VALID_SOLVER_MODES:
        raise ScenarioValidationError(f"Unsupported solver mode: {scenario.solver.mode!r}.")
    if scenario.solver.closure_model not in VALID_CLOSURE_MODELS:
        raise ScenarioValidationError(f"Unsupported closure model: {scenario.solver.closure_model!r}.")
    if scenario.solver.H_override_m is not None and scenario.solver.H_override_m <= 0.0:
        raise ScenarioValidationError("H_override_m must be positive when provided.")
    for layer in scenario.soil.layers:
        if layer.bottom_z_m >= layer.top_z_m:
            raise ScenarioValidationError(f"Soil layer {layer.name!r} must have bottom_z_m below top_z_m.")
        if layer.thermal_conductivity_W_mK <= 0.0:
            raise ScenarioValidationError(f"Soil layer {layer.name!r} thermal conductivity must be positive.")
        if layer.volumetric_heat_capacity_J_m3K <= 0.0:
            raise ScenarioValidationError(f"Soil layer {layer.name!r} heat capacity must be positive.")
        if layer.latent_heat_J_m3 < 0.0:
            raise ScenarioValidationError(f"Soil layer {layer.name!r} latent heat must be non-negative.")


def derive_geometry(scenario: GETScenario) -> DerivedGeometry:
    validate_scenario(scenario)
    default_geometry = LoopGeometry()
    nodes_by_id = {node.id: node for node in scenario.nodes}
    derived_segments: list[DerivedSegment] = []
    total_length_m = 0.0
    evaporator_length_m = 0.0
    evaporator_weighted_mid_z = 0.0
    top_z_m = max(node.z_m for node in scenario.nodes)

    for segment in scenario.segments:
        start = nodes_by_id[segment.start_node_id]
        end = nodes_by_id[segment.end_node_id]
        dx_m = end.x_m - start.x_m
        dz_m = end.z_m - start.z_m
        length_m = math.hypot(dx_m, dz_m)
        if length_m <= 0.0:
            raise ScenarioValidationError(f"Segment {segment.id!r} has zero length.")
        angle_deg = math.degrees(math.atan2(dz_m, dx_m))
        hydraulic_diameter_m = (
            segment.diameter_m
            if segment.diameter_m is not None
            else default_geometry.hydraulic_diameter_m
        )
        roughness_m = (
            segment.roughness_m
            if segment.roughness_m is not None
            else default_geometry.wall_roughness_m
        )
        area_m2 = math.pi * (0.5 * hydraulic_diameter_m) ** 2
        orientation = _segment_orientation(segment.kind, dx_m, dz_m)
        derived_segments.append(
            DerivedSegment(
                id=segment.id,
                kind=segment.kind,
                start_node_id=segment.start_node_id,
                end_node_id=segment.end_node_id,
                dx_m=dx_m,
                dz_m=dz_m,
                length_m=length_m,
                angle_deg=angle_deg,
                orientation=orientation,
                hydraulic_diameter_m=hydraulic_diameter_m,
                roughness_m=roughness_m,
                area_m2=area_m2,
                relative_roughness=roughness_m / hydraulic_diameter_m,
                heat_mode=_heat_mode_for_kind(segment.kind),
            )
        )
        total_length_m += length_m
        if segment.kind == "evaporator":
            mid_z = 0.5 * (start.z_m + end.z_m)
            evaporator_length_m += length_m
            evaporator_weighted_mid_z += mid_z * length_m

    if evaporator_length_m <= 0.0:
        raise ScenarioValidationError("Scenario must include at least one evaporator segment.")

    evaporator_mean_z_m = evaporator_weighted_mid_z / evaporator_length_m
    evaporator_depth_m = -evaporator_mean_z_m
    geometric_head_m = top_z_m - evaporator_mean_z_m
    H_m = scenario.solver.H_override_m if scenario.solver.H_override_m is not None else geometric_head_m
    qtr_W_m = scenario.thermal.qtr_W_m

    return DerivedGeometry(
        segments=tuple(derived_segments),
        total_length_m=total_length_m,
        evaporator_length_m=evaporator_length_m,
        evaporator_mean_z_m=evaporator_mean_z_m,
        evaporator_depth_m=evaporator_depth_m,
        top_z_m=top_z_m,
        geometric_head_m=geometric_head_m,
        H_m=H_m,
        qtr_W_m=qtr_W_m,
        heat_power_W=qtr_W_m * evaporator_length_m,
    )


def _segment_orientation(kind: str, dx_m: float, dz_m: float) -> str:
    if kind == "riser":
        return "vertical_up"
    if kind == "downcomer":
        return "return_line"
    if abs(dz_m) <= 1e-9:
        return "horizontal"
    if dz_m > 0.0:
        return "inclined_up"
    return "inclined_down"


def _heat_mode_for_kind(kind: str) -> str:
    if kind == "evaporator":
        return "prescribed_qtr"
    if kind == "condenser":
        return "saturation_boundary"
    return "adiabatic"


def solver_inputs_from_scenario(scenario: GETScenario) -> dict[str, float | str | LoopGeometry]:
    return derive_geometry(scenario).to_solver_inputs(scenario)


def run_scenario(scenario: GETScenario) -> Any:
    from get_co2_model import CO2MathcadModel

    model = CO2MathcadModel()
    return model.run_result(**solver_inputs_from_scenario(scenario))


def save_scenario(scenario: GETScenario, directory: Path = DEFAULT_SCENARIO_DIR) -> Path:
    validate_scenario(scenario)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{safe_scenario_id(scenario.scenario_id)}.json"
    path.write_text(json.dumps(scenario_to_dict(scenario), indent=2), encoding="utf-8")
    return path


def load_scenario(path: Path) -> GETScenario:
    return scenario_from_dict(json.loads(path.read_text(encoding="utf-8")))


def list_scenario_files(directory: Path = DEFAULT_SCENARIO_DIR) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.glob("*.json") if path.is_file())


def safe_scenario_id(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-")
    return slug or "untitled"


def _node_from_dict(data: Mapping[str, Any]) -> DesignerNode:
    return DesignerNode(
        id=_required_str(data, "id"),
        x_m=_required_float(data, "x_m"),
        z_m=_required_float(data, "z_m"),
    )


def _segment_from_dict(data: Mapping[str, Any]) -> DesignerSegment:
    return DesignerSegment(
        id=_required_str(data, "id"),
        start_node_id=_required_str(data, "start_node_id"),
        end_node_id=_required_str(data, "end_node_id"),
        kind=_required_str(data, "kind"),
        diameter_m=_optional_float(data, "diameter_m"),
        roughness_m=_optional_float(data, "roughness_m"),
    )


def _thermal_from_dict(data: Mapping[str, Any]) -> ThermalConfig:
    return ThermalConfig(
        mode=_optional_str(data, "mode", "prescribed_qtr"),
        qtr_W_m=_float_or_default(_optional_float(data, "qtr_W_m", 76.68), 76.68),
    )


def _soil_from_dict(data: Mapping[str, Any]) -> SoilConfig:
    layers_data = data.get("layers", None)
    if layers_data is None:
        layers = (SoilLayer(),)
    else:
        if not isinstance(layers_data, list):
            raise ScenarioValidationError("soil.layers must be a list.")
        layers = tuple(_soil_layer_from_dict(item) for item in layers_data)
    return SoilConfig(
        mode=_optional_str(data, "mode", "dynamic_placeholder"),
        surface_z_m=_float_or_default(_optional_float(data, "surface_z_m", 0.0), 0.0),
        layers=layers,
    )


def _soil_layer_from_dict(data: Mapping[str, Any]) -> SoilLayer:
    return SoilLayer(
        name=_optional_str(data, "name", "soil"),
        top_z_m=_float_or_default(_optional_float(data, "top_z_m", 0.0), 0.0),
        bottom_z_m=_float_or_default(_optional_float(data, "bottom_z_m", -10.0), -10.0),
        thermal_conductivity_W_mK=_float_or_default(
            _optional_float(data, "thermal_conductivity_W_mK", 1.5),
            1.5,
        ),
        volumetric_heat_capacity_J_m3K=_float_or_default(
            _optional_float(data, "volumetric_heat_capacity_J_m3K", 2.0e6),
            2.0e6,
        ),
        latent_heat_J_m3=_float_or_default(_optional_float(data, "latent_heat_J_m3", 8.0e7), 8.0e7),
        initial_temperature_C=_float_or_default(_optional_float(data, "initial_temperature_C", -1.0), -1.0),
    )


def _solver_from_dict(data: Mapping[str, Any]) -> SolverConfig:
    return SolverConfig(
        tcon_C=_float_or_default(_optional_float(data, "tcon_C", 0.0), 0.0),
        mode=_optional_str(data, "mode", "worksheet_compatible"),
        closure_model=_optional_str(data, "closure_model", "worksheet_compatible"),
        H_override_m=_optional_float(data, "H_override_m"),
    )


def _required_list(data: Mapping[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ScenarioValidationError(f"{key} must be a list.")
    return value


def _optional_mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ScenarioValidationError(f"{key} must be an object.")
    return value


def _required_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ScenarioValidationError(f"{key} must be a non-empty string.")
    return value


def _optional_str(data: Mapping[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise ScenarioValidationError(f"{key} must be a non-empty string.")
    return value


def _required_float(data: Mapping[str, Any], key: str) -> float:
    if key not in data:
        raise ScenarioValidationError(f"{key} is required.")
    return _coerce_finite_float(data[key], key)


def _optional_float(data: Mapping[str, Any], key: str, default: float | None = None) -> float | None:
    if key not in data or data[key] is None:
        return default
    return _coerce_finite_float(data[key], key)


def _coerce_finite_float(value: Any, key: str) -> float:
    if isinstance(value, bool):
        raise ScenarioValidationError(f"{key} must be a finite number.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ScenarioValidationError(f"{key} must be a finite number.") from exc
    if not math.isfinite(number):
        raise ScenarioValidationError(f"{key} must be a finite number.")
    return number


def _float_or_default(value: float | None, default: float) -> float:
    return default if value is None else value
