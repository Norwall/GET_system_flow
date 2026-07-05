from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from published_friction import (
    SourceRequiredCorrelationError,
    friedel_1979_pressure_gradient_pa_per_m,
    muller_steinhagen_heck_1986_pressure_gradient_pa_per_m,
)
from published_regimes import (
    classify_horizontal_evaporator_regime_result,
    classify_vertical_riser_regime_result,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "docs" / "source_gate_manifest.json"
FORMULA_REGISTRY_PATH = PROJECT_ROOT / "docs" / "formula_registry.md"
OPEN_WEB_AUDIT_PATH = PROJECT_ROOT / "docs" / "source_audit_open_web_2026-07-05.md"
PREVIOUS_OPEN_WEB_AUDIT_PATH = PROJECT_ROOT / "docs" / "source_audit_open_web_2026-07-04.md"
CHECKPOINT_AUDIT_PATH = PROJECT_ROOT / "docs" / "source_audit_checkpoint_5_6.md"
README_PATH = PROJECT_ROOT / "README.md"
ACADEMIC_REFERENCE_PATH = PROJECT_ROOT / "docs" / "get_co2_academic_reference.md"

FORMULA_REGISTRY_TEXT = FORMULA_REGISTRY_PATH.read_text(encoding="utf-8")
OPEN_WEB_AUDIT_TEXT = OPEN_WEB_AUDIT_PATH.read_text(encoding="utf-8")
PREVIOUS_OPEN_WEB_AUDIT_TEXT = PREVIOUS_OPEN_WEB_AUDIT_PATH.read_text(encoding="utf-8")
CHECKPOINT_AUDIT_TEXT = CHECKPOINT_AUDIT_PATH.read_text(encoding="utf-8")
README_TEXT = README_PATH.read_text(encoding="utf-8")
ACADEMIC_REFERENCE_TEXT = ACADEMIC_REFERENCE_PATH.read_text(encoding="utf-8")

SOURCE_REQUIRED_REGISTRY_IDS = {
    "TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE",
    "TP-FRIEDEL-1979-SOURCE-GATE",
    "VOID-ZUBER-FINDLAY-1965-SOURCE-GATE",
    "REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE",
    "REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE",
}

ALLOWED_EVIDENCE_STATUSES = {
    "not_available",
    "metadata_only",
    "full_text_available",
    "audited",
}
ALLOWED_DECISIONS = {
    "source_required",
    "source_candidate",
    "released",
}
REQUIRED_ENTRY_FIELDS = {
    "registry_id",
    "candidate_id",
    "model",
    "target_code",
    "primary_citation",
    "primary_record",
    "evidence_status",
    "access_evidence",
    "local_full_text_ref",
    "decision",
    "blocking_reasons",
    "required_audit_checks",
    "required_tests_before_release",
}


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest_entries(manifest: dict) -> list[dict]:
    return manifest["entries"]


def _registry_sections() -> set[str]:
    return set(re.findall(r"^## ([A-Z0-9]+(?:-[A-Z0-9]+)+)$", FORMULA_REGISTRY_TEXT, flags=re.MULTILINE))


def _entries_by_registry_id(entries: list[dict]) -> dict[str, dict]:
    return {entry["registry_id"]: entry for entry in entries if entry["registry_id"] is not None}


def _entry_by_candidate_id(entries: list[dict], candidate_id: str) -> dict:
    matches = [entry for entry in entries if entry["candidate_id"] == candidate_id]
    assert len(matches) == 1
    return matches[0]


def test_manifest_points_to_existing_audit_documents(manifest: dict) -> None:
    assert MANIFEST_PATH.exists()
    assert OPEN_WEB_AUDIT_PATH.exists()
    assert PREVIOUS_OPEN_WEB_AUDIT_PATH.exists()
    assert CHECKPOINT_AUDIT_PATH.exists()

    policy = manifest["policy"]
    assert policy["primary_source_only"] is True
    assert manifest["manifest_version"] == "source-gate-open-web-2026-07-05"
    assert policy["audit_document"] == "docs/source_audit_open_web_2026-07-05.md"
    assert "docs/source_audit_open_web_2026-07-04.md" in policy["previous_audit_documents"]
    assert policy["checkpoint_audit_document"] == "docs/source_audit_checkpoint_5_6.md"
    assert "repository landing pages without an accessible full-text bitstream" in policy["source_gate_rule"]


def test_manifest_entries_have_required_shape(manifest_entries: list[dict]) -> None:
    registry_sections = _registry_sections()
    seen_registry_ids: set[str] = set()
    seen_candidate_ids: set[str] = set()

    for entry in manifest_entries:
        assert REQUIRED_ENTRY_FIELDS <= set(entry)
        assert entry["evidence_status"] in ALLOWED_EVIDENCE_STATUSES
        assert entry["decision"] in ALLOWED_DECISIONS
        assert entry["model"]
        assert entry["target_code"]
        assert entry["primary_citation"]
        assert isinstance(entry["blocking_reasons"], list) and entry["blocking_reasons"]
        assert isinstance(entry["required_audit_checks"], list) and entry["required_audit_checks"]
        assert isinstance(entry["required_tests_before_release"], list) and entry["required_tests_before_release"]

        registry_id = entry["registry_id"]
        candidate_id = entry["candidate_id"]
        if registry_id is not None:
            assert registry_id in registry_sections
            assert registry_id not in seen_registry_ids
            seen_registry_ids.add(registry_id)
        else:
            assert candidate_id
            assert candidate_id not in seen_candidate_ids
            seen_candidate_ids.add(candidate_id)


def test_all_active_source_required_registry_ids_are_manifested(manifest_entries: list[dict]) -> None:
    entries_by_registry_id = _entries_by_registry_id(manifest_entries)

    assert SOURCE_REQUIRED_REGISTRY_IDS <= set(entries_by_registry_id)
    for registry_id in SOURCE_REQUIRED_REGISTRY_IDS:
        entry = entries_by_registry_id[registry_id]
        assert entry["decision"] == "source_required"
        assert entry["evidence_status"] in {"not_available", "metadata_only"}
        assert entry["local_full_text_ref"] == ""
        assert registry_id in FORMULA_REGISTRY_TEXT
        assert registry_id in CHECKPOINT_AUDIT_TEXT


def test_released_decision_requires_full_audit(manifest_entries: list[dict]) -> None:
    for entry in manifest_entries:
        if entry["decision"] != "released":
            continue
        assert entry["evidence_status"] == "audited"
        assert entry["local_full_text_ref"]
        assert "docs/formula_registry.md" in " ".join(entry["required_audit_checks"])
        assert entry["required_tests_before_release"]


def test_epfl_landing_pages_do_not_release_wojtan_gates(manifest_entries: list[dict]) -> None:
    entries_by_registry_id = _entries_by_registry_id(manifest_entries)
    part_i = entries_by_registry_id["REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE"]
    part_ii = _entry_by_candidate_id(manifest_entries, "HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE")

    for entry in (part_i, part_ii):
        assert entry["decision"] == "source_required"
        assert entry["evidence_status"] == "metadata_only"
        assert "infoscience.epfl.ch" in entry["primary_record"]["repository_record"]
        assert "no ORIGINAL/full-text bitstream" in entry["access_evidence"]["endpoint_check"]

    assert "EPFL DSpace bundles" in OPEN_WEB_AUDIT_TEXT
    assert "EPFL repository landing page без `ORIGINAL`/full-text bitstream" in PREVIOUS_OPEN_WEB_AUDIT_TEXT
    assert "repository landing page без" in CHECKPOINT_AUDIT_TEXT
    assert "Repository landing page без доступного full-text" in FORMULA_REGISTRY_TEXT


def test_osti_full_text_is_candidate_not_active_model(manifest_entries: list[dict]) -> None:
    osti = _entry_by_candidate_id(manifest_entries, "HTC-OSTI-1962-SOURCE-CANDIDATE")

    assert osti["registry_id"] is None
    assert osti["evidence_status"] == "full_text_available"
    assert osti["decision"] == "source_candidate"
    assert osti["local_full_text_ref"] == "https://www.osti.gov/servlets/purl/4636495"
    assert "Content-Length 1533908" in osti["access_evidence"]["endpoint_check"]
    assert "HTTP 200" in osti["access_evidence"]["endpoint_check"]
    assert "10.2172/4636495" in OPEN_WEB_AUDIT_TEXT
    assert "10.2172/4636495" not in FORMULA_REGISTRY_TEXT


def test_user_and_academic_docs_reference_open_web_audit_context() -> None:
    for text in (README_TEXT, ACADEMIC_REFERENCE_TEXT):
        assert "docs/source_audit_open_web_2026-07-05.md" in text
        assert "docs/source_audit_open_web_2026-07-04.md" in text
        assert "docs/source_gate_manifest.json" in text
        assert "OSTI" in text
        assert "10.2172/4636495" in text

    assert "EPFL" in README_TEXT
    assert "landing pages" in README_TEXT
    assert "ORIGINAL`/full-text bitstream" in README_TEXT
    assert "Академический контекст и source-gate" in README_TEXT
    assert "source_candidate` означает, что полный текст найден" in README_TEXT
    assert "EPFL landing page без доступного `ORIGINAL`/full-text bitstream" in ACADEMIC_REFERENCE_TEXT
    assert "Минимальная цепочка интерпретации" in ACADEMIC_REFERENCE_TEXT
    assert "OSTI `10.2172/4636495`" in ACADEMIC_REFERENCE_TEXT
    assert "source_candidate" in ACADEMIC_REFERENCE_TEXT


def test_friction_source_gate_guards_remain_active() -> None:
    with pytest.raises(SourceRequiredCorrelationError):
        muller_steinhagen_heck_1986_pressure_gradient_pa_per_m()

    with pytest.raises(SourceRequiredCorrelationError):
        friedel_1979_pressure_gradient_pa_per_m()


def test_published_regime_placeholders_remain_source_required() -> None:
    horizontal = classify_horizontal_evaporator_regime_result(
        mass_quality=0.3,
        gas_volume_fraction=0.5,
        gas_superficial_velocity_m_s=1.0,
        liquid_superficial_velocity_m_s=0.1,
        slip_ratio=2.0,
    )
    vertical = classify_vertical_riser_regime_result(
        gas_volume_fraction=0.55,
        gas_superficial_velocity_m_s=2.0,
    )

    assert horizontal.name == "unknown_or_out_of_range"
    assert vertical.name == "unknown_or_out_of_range"
    assert horizontal.status == "source_required"
    assert vertical.status == "source_required"
