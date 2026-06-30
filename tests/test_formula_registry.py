from __future__ import annotations

import re
from pathlib import Path

import pytest

from two_phase_closures import (
    closure_model_formula_registry_ids,
    closure_model_scientific_status,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "docs" / "formula_registry.md"
REGISTRY_TEXT = REGISTRY_PATH.read_text(encoding="utf-8")

EXPECTED_REGISTRY_IDS = (
    "PROP-MATHCAD-CO2-TABLE",
    "PROP-COOLPROP-CO2-HEOS",
    "PROP-COOLPROP-NH3-HEOS",
    "PROP-REFPROP-ADAPTER",
    "BAL-HEAT-INPUT",
    "BAL-VAPOR-GENERATION",
    "BAL-PREBOILING-FRACTION",
    "FRIC-REYNOLDS",
    "FRIC-DARCY-MASS-FLUX",
    "FRIC-LAMINAR-DARCY",
    "FRIC-BLASIUS-SMOOTH",
    "FRIC-LEGACY-BLENDED-DARCY",
    "FRIC-COLEBROOK-WHITE",
    "FRIC-CHURCHILL-1977",
    "FRIC-ZERO-TEST",
    "TP-LOCKHART-MARTINELLI",
    "TP-CHISHOLM-CONSTANT",
    "TP-CHISHOLM-MULTIPLIER",
    "FLOW-MASS-QUALITY",
    "VOID-GENERIC-SLIP",
    "VOID-WORKSHEET-PHI2L",
    "VOID-HOMOGENEOUS-EQUILIBRIUM",
    "VOID-ZIVI-1964",
    "FLOW-PHASE-VELOCITIES",
    "FLOW-SLIP-RATIO",
    "FLOW-MIXTURE-DENSITY",
    "PRESS-ACCELERATION-MOMENTUM",
    "PRESS-WORKSHEET-DRIVING-HEAD",
    "PRESS-DISTRIBUTED-RISER-GRADIENT",
    "PRESS-HYDROSTATIC-SECTION",
    "PRESS-LOOP-BALANCE",
    "EXP-REGIME-AWARE-CLASSIFIERS",
    "EXP-DRIFT-FLUX-LIKE-VOID",
    "EXP-ANNULAR-CORE-VOID",
    "EXP-REGIME-FRICTION-GRADIENTS",
)

REQUIRED_FIELDS = (
    "- Статус:",
    "- Математическая запись:",
    "- Переменные и размерности:",
    "- Область применимости:",
    "- Источник:",
    "- Код:",
    "- Тесты:",
)

EXPERIMENTAL_IDS = (
    "EXP-REGIME-AWARE-CLASSIFIERS",
    "EXP-DRIFT-FLUX-LIKE-VOID",
    "EXP-ANNULAR-CORE-VOID",
    "EXP-REGIME-FRICTION-GRADIENTS",
)

CLOSURE_MODELS = (
    "worksheet_compatible",
    "homogeneous_equilibrium",
    "zivi",
    "experimental_regime_aware",
    "regime_aware",
)


def _registry_sections() -> dict[str, str]:
    heading_matches = list(re.finditer(r"^## (.+)$", REGISTRY_TEXT, flags=re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(heading_matches):
        title = match.group(1).strip()
        if not re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", title):
            continue
        end = heading_matches[index + 1].start() if index + 1 < len(heading_matches) else len(REGISTRY_TEXT)
        sections[title] = REGISTRY_TEXT[match.start():end]
    return sections


@pytest.fixture(scope="module")
def registry_sections() -> dict[str, str]:
    return _registry_sections()


@pytest.mark.parametrize("entry_id", EXPECTED_REGISTRY_IDS)
def test_registry_entry_exists_exactly_once(entry_id: str, registry_sections: dict[str, str]) -> None:
    assert entry_id in registry_sections
    assert len(re.findall(rf"^## {re.escape(entry_id)}$", REGISTRY_TEXT, flags=re.MULTILINE)) == 1


@pytest.mark.parametrize("entry_id", EXPECTED_REGISTRY_IDS)
def test_implemented_entries_have_required_fields(entry_id: str, registry_sections: dict[str, str]) -> None:
    section = registry_sections[entry_id]
    missing_fields = [field for field in REQUIRED_FIELDS if field not in section]
    assert missing_fields == []


def test_closure_models_have_registry_ids(registry_sections: dict[str, str]) -> None:
    for model in CLOSURE_MODELS:
        status = closure_model_scientific_status(model)
        assert status in {"mathcad_compatible", "published", "experimental"}
        registry_ids = closure_model_formula_registry_ids(model)
        assert registry_ids
        assert all(registry_id in registry_sections for registry_id in registry_ids)


def test_regime_aware_alias_uses_experimental_registry_ids() -> None:
    assert closure_model_formula_registry_ids("regime_aware") == closure_model_formula_registry_ids(
        "experimental_regime_aware"
    )


@pytest.mark.parametrize("entry_id", EXPERIMENTAL_IDS)
def test_experimental_heuristics_are_marked_without_primary_source(
    entry_id: str,
    registry_sections: dict[str, str],
) -> None:
    assert "- Статус: EXPERIMENTAL / NO PRIMARY SOURCE." in registry_sections[entry_id]


def test_current_rough_friction_blend_is_not_claimed_as_colebrook_white(
    registry_sections: dict[str, str],
) -> None:
    rough_section = registry_sections["FRIC-LEGACY-BLENDED-DARCY"]
    assert "- Статус: MATHCAD_COMPATIBLE / REQUIRES_AUDIT." in rough_section
    assert "не является опубликованным уравнением Colebrook-White" in rough_section
