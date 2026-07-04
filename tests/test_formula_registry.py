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
SOURCE_AUDIT_PATH = PROJECT_ROOT / "docs" / "source_audit_checkpoint_5_6.md"
SOURCE_AUDIT_TEXT = SOURCE_AUDIT_PATH.read_text(encoding="utf-8")

EXPECTED_REGISTRY_IDS = (
    "PROP-MATHCAD-CO2-TABLE",
    "PROP-COOLPROP-CO2-HEOS",
    "PROP-COOLPROP-NH3-HEOS",
    "PROP-REFPROP-ADAPTER",
    "BAL-HEAT-INPUT",
    "HEAT-LINEAR-TO-WALL-FLUX",
    "BAL-VAPOR-GENERATION",
    "BAL-PREBOILING-FRACTION",
    "QCRIT-DISSERTATION-SCAN",
    "QCRIT-DISSERTATION-F-ZERO",
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
    "TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE",
    "TP-FRIEDEL-1979-SOURCE-GATE",
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
    "VOID-ZUBER-FINDLAY-1965-SOURCE-GATE",
    "REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE",
    "REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE",
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

SOURCE_REQUIRED_IDS = (
    "TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE",
    "TP-FRIEDEL-1979-SOURCE-GATE",
    "VOID-ZUBER-FINDLAY-1965-SOURCE-GATE",
    "REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE",
    "REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE",
)

SOURCE_REQUIRED_PRIMARY_RECORDS = {
    "TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE": "10.1016/0255-2701(86)80008-3",
    "TP-FRIEDEL-1979-SOURCE-GATE": "Friedel",
    "VOID-ZUBER-FINDLAY-1965-SOURCE-GATE": "10.1115/1.3689137",
    "REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE": "10.1016/j.ijheatmasstransfer.2004.12.012",
    "REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE": "10.1002/aic.690260304",
}

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


def test_published_closure_models_do_not_depend_on_experimental_registry_entries(
    registry_sections: dict[str, str],
) -> None:
    for model in CLOSURE_MODELS:
        if closure_model_scientific_status(model) != "published":
            continue
        registry_ids = closure_model_formula_registry_ids(model)
        assert not any(registry_id.startswith("EXP-") for registry_id in registry_ids)
        assert all("EXPERIMENTAL / NO PRIMARY SOURCE" not in registry_sections[registry_id] for registry_id in registry_ids)


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


@pytest.mark.parametrize("entry_id", SOURCE_REQUIRED_IDS)
def test_pending_published_correlations_are_marked_source_required(
    entry_id: str,
    registry_sections: dict[str, str],
) -> None:
    assert "- Статус: SOURCE_REQUIRED." in registry_sections[entry_id]


@pytest.mark.parametrize("entry_id", SOURCE_REQUIRED_IDS)
def test_source_required_entries_are_linked_to_primary_source_audit(
    entry_id: str,
    registry_sections: dict[str, str],
) -> None:
    section = registry_sections[entry_id]

    assert "docs/source_audit_checkpoint_5_6.md" in section
    assert entry_id in SOURCE_AUDIT_TEXT
    assert SOURCE_REQUIRED_PRIMARY_RECORDS[entry_id] in SOURCE_AUDIT_TEXT


def test_source_required_policy_is_primary_source_only() -> None:
    assert "primary-source-only" in REGISTRY_TEXT
    assert "полного первоисточника" in REGISTRY_TEXT
    assert "DOI landing page, abstract, Crossref" in REGISTRY_TEXT
    assert "Повторная проверка политики: 2026-07-04." in SOURCE_AUDIT_TEXT
    assert "Crossref, DOI landing page, abstract" in SOURCE_AUDIT_TEXT


def test_regime_classifier_registry_points_to_experimental_layer(
    registry_sections: dict[str, str],
) -> None:
    section = registry_sections["EXP-REGIME-AWARE-CLASSIFIERS"]

    assert "experimental_regimes.classify_horizontal_evaporator_regime_result" in section
    assert "compatibility wrappers in `two_phase_regimes.py`" in section
    assert "published_regimes.py` содержит только защитные source-gate заготовки" in REGISTRY_TEXT


def test_current_rough_friction_blend_is_not_claimed_as_colebrook_white(
    registry_sections: dict[str, str],
) -> None:
    rough_section = registry_sections["FRIC-LEGACY-BLENDED-DARCY"]
    assert "- Статус: MATHCAD_COMPATIBLE / REQUIRES_AUDIT." in rough_section
    assert "не является опубликованным уравнением Colebrook-White" in rough_section
