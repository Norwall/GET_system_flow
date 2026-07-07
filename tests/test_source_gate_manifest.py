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
FOLLOWUP_AUDIT_PATH = PROJECT_ROOT / "docs" / "source_audit_followup_2026-07-06.md"
DISSERTATION_FORMULA_AUDIT_PATH = PROJECT_ROOT / "docs" / "dissertation_formula_audit_2026-07-06.md"
CHEN_1962_FORMULA_AUDIT_PATH = PROJECT_ROOT / "docs" / "chen_1962_formula_audit_2026-07-06.md"
CHECKPOINT_AUDIT_PATH = PROJECT_ROOT / "docs" / "source_audit_checkpoint_5_6.md"
PRIMARY_SOURCE_INVENTORY_PATH = PROJECT_ROOT / "docs" / "primary_source_inventory.md"
MILESTONE_CLOSURE_PIPELINE_PATH = PROJECT_ROOT / "docs" / "milestone_closure_pipeline.md"
UNRESOLVED_QUESTIONS_PATH = PROJECT_ROOT / "docs" / "source_gate_unresolved_questions.md"
SECONDARY_CANDIDATES_PATH = PROJECT_ROOT / "docs" / "secondary_formula_candidates.md"
PRIMARY_SOURCE_DROP_DIR = PROJECT_ROOT / "sources" / "primary"
PRIMARY_SOURCE_README_PATH = PRIMARY_SOURCE_DROP_DIR / "README.md"
README_PATH = PROJECT_ROOT / "README.md"
ACADEMIC_REFERENCE_PATH = PROJECT_ROOT / "docs" / "get_co2_academic_reference.md"
GITIGNORE_PATH = PROJECT_ROOT / ".gitignore"
PLAN_PATH = PROJECT_ROOT / "plan.md"

FORMULA_REGISTRY_TEXT = FORMULA_REGISTRY_PATH.read_text(encoding="utf-8")
OPEN_WEB_AUDIT_TEXT = OPEN_WEB_AUDIT_PATH.read_text(encoding="utf-8")
PREVIOUS_OPEN_WEB_AUDIT_TEXT = PREVIOUS_OPEN_WEB_AUDIT_PATH.read_text(encoding="utf-8")
FOLLOWUP_AUDIT_TEXT = FOLLOWUP_AUDIT_PATH.read_text(encoding="utf-8")
DISSERTATION_FORMULA_AUDIT_TEXT = DISSERTATION_FORMULA_AUDIT_PATH.read_text(encoding="utf-8")
CHEN_1962_FORMULA_AUDIT_TEXT = CHEN_1962_FORMULA_AUDIT_PATH.read_text(encoding="utf-8")
CHECKPOINT_AUDIT_TEXT = CHECKPOINT_AUDIT_PATH.read_text(encoding="utf-8")
PRIMARY_SOURCE_INVENTORY_TEXT = PRIMARY_SOURCE_INVENTORY_PATH.read_text(encoding="utf-8")
MILESTONE_CLOSURE_PIPELINE_TEXT = MILESTONE_CLOSURE_PIPELINE_PATH.read_text(encoding="utf-8")
UNRESOLVED_QUESTIONS_TEXT = UNRESOLVED_QUESTIONS_PATH.read_text(encoding="utf-8")
SECONDARY_CANDIDATES_TEXT = SECONDARY_CANDIDATES_PATH.read_text(encoding="utf-8")
PRIMARY_SOURCE_README_TEXT = PRIMARY_SOURCE_README_PATH.read_text(encoding="utf-8")
README_TEXT = README_PATH.read_text(encoding="utf-8")
ACADEMIC_REFERENCE_TEXT = ACADEMIC_REFERENCE_PATH.read_text(encoding="utf-8")
GITIGNORE_TEXT = GITIGNORE_PATH.read_text(encoding="utf-8")
PLAN_TEXT = PLAN_PATH.read_text(encoding="utf-8")

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
REQUIRED_SECONDARY_CANDIDATE_FIELDS = {
    "registry_id",
    "secondary_source_url",
    "secondary_formula_scope",
    "known_ambiguities",
    "release_blockers",
}
REQUIRED_DISSERTATION_CANDIDATE_FIELDS = {
    "candidate_id",
    "local_full_text_ref",
    "repository_record",
    "bitstream_content",
    "sha256",
    "scope",
    "audit_note",
    "release_rule",
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
    assert FOLLOWUP_AUDIT_PATH.exists()
    assert DISSERTATION_FORMULA_AUDIT_PATH.exists()
    assert CHEN_1962_FORMULA_AUDIT_PATH.exists()
    assert CHECKPOINT_AUDIT_PATH.exists()
    assert PRIMARY_SOURCE_INVENTORY_PATH.exists()
    assert MILESTONE_CLOSURE_PIPELINE_PATH.exists()
    assert UNRESOLVED_QUESTIONS_PATH.exists()
    assert SECONDARY_CANDIDATES_PATH.exists()
    assert PRIMARY_SOURCE_DROP_DIR.is_dir()
    assert PRIMARY_SOURCE_README_PATH.exists()

    policy = manifest["policy"]
    assert policy["primary_source_only"] is True
    assert manifest["manifest_version"] == "source-gate-primary-source-intake-2026-07-05"
    assert policy["audit_document"] == "docs/source_audit_open_web_2026-07-05.md"
    assert "docs/source_audit_open_web_2026-07-04.md" in policy["previous_audit_documents"]
    assert "docs/source_audit_followup_2026-07-06.md" in policy["previous_audit_documents"]
    assert "docs/dissertation_formula_audit_2026-07-06.md" in policy["previous_audit_documents"]
    assert "docs/chen_1962_formula_audit_2026-07-06.md" in policy["previous_audit_documents"]
    assert policy["checkpoint_audit_document"] == "docs/source_audit_checkpoint_5_6.md"
    assert policy["local_source_inventory_document"] == "docs/primary_source_inventory.md"
    assert policy["milestone_closure_pipeline_document"] == "docs/milestone_closure_pipeline.md"
    assert policy["unresolved_questions_document"] == "docs/source_gate_unresolved_questions.md"
    assert policy["source_drop_directory"] == "sources/primary"
    assert policy["secondary_formula_candidate_document"] == "docs/secondary_formula_candidates.md"
    assert "repository landing pages without an accessible full-text bitstream" in policy["source_gate_rule"]
    assert "do not release SOURCE_REQUIRED gates" in policy["secondary_formula_candidate_rule"]
    assert "published runtime physics" in policy["secondary_formula_candidate_rule"]
    assert "not committed" in policy["local_source_file_policy"]
    assert "SHA256" in policy["local_source_file_policy"]


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


def test_released_decision_requires_full_audit(manifest: dict, manifest_entries: list[dict]) -> None:
    source_drop_prefix = manifest["policy"]["source_drop_directory"] + "/"
    for entry in manifest_entries:
        if entry["decision"] != "released":
            continue
        assert entry["evidence_status"] == "audited"
        assert entry["local_full_text_ref"].startswith(source_drop_prefix)
        assert "docs/formula_registry.md" in " ".join(entry["required_audit_checks"])
        assert "docs/primary_source_inventory.md" in " ".join(manifest["policy"]["released_requirements"])
        assert entry["required_tests_before_release"]


def test_secondary_formula_candidate_blocks_are_not_release_evidence(manifest_entries: list[dict]) -> None:
    registry_sections = _registry_sections()
    candidate_entries = [entry for entry in manifest_entries if "secondary_formula_candidate" in entry]

    assert candidate_entries
    for entry in candidate_entries:
        candidate = entry["secondary_formula_candidate"]
        assert REQUIRED_SECONDARY_CANDIDATE_FIELDS <= set(candidate)
        assert candidate["registry_id"] in registry_sections
        assert candidate["registry_id"] in SECONDARY_CANDIDATES_TEXT
        assert candidate["secondary_source_url"].startswith("https://")
        assert isinstance(candidate["known_ambiguities"], list) and candidate["known_ambiguities"]
        assert isinstance(candidate["release_blockers"], list) and candidate["release_blockers"]
        assert entry["decision"] == "source_required"
        assert entry["local_full_text_ref"] == ""

    assert "SECONDARY_FORMULA_CANDIDATE / NOT_RELEASED" in SECONDARY_CANDIDATES_TEXT
    assert "не снимают `SOURCE_REQUIRED`" in SECONDARY_CANDIDATES_TEXT


def test_known_secondary_candidates_are_registered_in_manifest(manifest_entries: list[dict]) -> None:
    candidates = {
        entry["secondary_formula_candidate"]["registry_id"]
        for entry in manifest_entries
        if "secondary_formula_candidate" in entry
    }

    assert "TP-MULLER-STEINHAGEN-HECK-1986-SECONDARY-CANDIDATE" in candidates
    assert "TP-FRIEDEL-1979-SECONDARY-CANDIDATE" in candidates
    assert "REGIME-TAITEL-DUKLER-1976-HORIZONTAL-SECONDARY-CANDIDATE" in candidates


def test_dissertation_candidates_are_local_audit_guidance_not_release_evidence(
    manifest_entries: list[dict],
) -> None:
    entries_by_registry_id = _entries_by_registry_id(manifest_entries)
    candidate_entries = [entry for entry in manifest_entries if "dissertation_candidates" in entry]

    assert candidate_entries
    for entry in candidate_entries:
        assert entry["decision"] == "source_required"
        for candidate in entry["dissertation_candidates"]:
            assert REQUIRED_DISSERTATION_CANDIDATE_FIELDS <= set(candidate)
            assert candidate["local_full_text_ref"].startswith("sources/primary/")
            assert candidate["local_full_text_ref"] in PRIMARY_SOURCE_INVENTORY_TEXT
            assert candidate["sha256"] in PRIMARY_SOURCE_INVENTORY_TEXT
            assert candidate["repository_record"].startswith("https://infoscience.epfl.ch/handle/")
            assert candidate["bitstream_content"].startswith("https://infoscience.epfl.ch/server/api/core/bitstreams/")
            assert "docs/dissertation_formula_audit_2026-07-06.md" in candidate["audit_note"]
            assert "Does not release" in candidate["release_rule"]

    part_i_candidates = entries_by_registry_id["REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE"][
        "dissertation_candidates"
    ]
    part_ii_candidates = _entry_by_candidate_id(
        manifest_entries,
        "HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE",
    )["dissertation_candidates"]
    friedel_candidates = entries_by_registry_id["TP-FRIEDEL-1979-SOURCE-GATE"]["dissertation_candidates"]

    assert part_i_candidates[0]["candidate_id"] == "DISS-WOJTAN-2004-EPFL-TH2978"
    assert part_ii_candidates[0]["candidate_id"] == "DISS-WOJTAN-2004-EPFL-TH2978"
    assert friedel_candidates[0]["candidate_id"] == "DISS-MORENO-QUIBEN-2005-EPFL-TH3337"
    assert "DISS-WOJTAN-2004-EPFL-TH2978" in FOLLOWUP_AUDIT_TEXT
    assert "DISS-MORENO-QUIBEN-2005-EPFL-TH3337" in FOLLOWUP_AUDIT_TEXT
    assert "DISS-WOJTAN-2004-EPFL-TH2978" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "DISS-MORENO-QUIBEN-2005-EPFL-TH3337" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "candidate_only" in FOLLOWUP_AUDIT_TEXT


def test_dissertation_formula_audit_records_page_level_candidate_map() -> None:
    assert "Moreno Quiben TH3337 page map" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "53-66" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "Friedel section" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "Muller-Steinhagen and Heck section" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "Moreno Quiben TH3337 text-layer formula guidance" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "phi_f0^2 = E + 3.24 * F * H / (Fr_H^0.045 * We_L^0.035)" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "(dp/dz)_frict = F*(1-x)^(1/3) + B*x^3" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "(f_i)_annular = 0.67" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "xdi = 0.58*exp" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "xde = 0.61*exp" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "Wojtan TH2978 page map" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "requires OCR/manual audit" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "candidate_only" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "does not release" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "20-25, 53-66, 109-125, 146, 149, 152" in PRIMARY_SOURCE_INVENTORY_TEXT
    assert "docs/dissertation_formula_audit_2026-07-06.md" in FORMULA_REGISTRY_TEXT
    assert "TH3337 text layer gives candidate Eqs. (4.53)-(4.56)" in FORMULA_REGISTRY_TEXT
    assert "TH3337 text layer gives candidate Eqs. (4.40)-(4.47)" in FORMULA_REGISTRY_TEXT


def test_local_primary_source_intake_policy_is_documented_and_ignored(manifest: dict) -> None:
    policy = manifest["policy"]

    assert policy["source_drop_directory"] == "sources/primary"
    assert policy["local_source_inventory_document"] == "docs/primary_source_inventory.md"
    assert policy["secondary_formula_candidate_document"] == "docs/secondary_formula_candidates.md"
    assert "sources/primary/*" in GITIGNORE_TEXT
    assert "!sources/primary/README.md" in GITIGNORE_TEXT

    for text in (
        PRIMARY_SOURCE_README_TEXT,
        PRIMARY_SOURCE_INVENTORY_TEXT,
        README_TEXT,
        ACADEMIC_REFERENCE_TEXT,
        FORMULA_REGISTRY_TEXT,
        SECONDARY_CANDIDATES_TEXT,
        CHECKPOINT_AUDIT_TEXT,
        OPEN_WEB_AUDIT_TEXT,
        FOLLOWUP_AUDIT_TEXT,
        DISSERTATION_FORMULA_AUDIT_TEXT,
        CHEN_1962_FORMULA_AUDIT_TEXT,
        MILESTONE_CLOSURE_PIPELINE_TEXT,
        UNRESOLVED_QUESTIONS_TEXT,
        PLAN_TEXT,
    ):
        assert "sources/primary" in text
        assert "docs/primary_source_inventory.md" in text

    assert "SHA256" in PRIMARY_SOURCE_README_TEXT
    assert "SHA256" in PRIMARY_SOURCE_INVENTORY_TEXT
    assert "не коммит" in PRIMARY_SOURCE_INVENTORY_TEXT
    assert "source_required" in PRIMARY_SOURCE_INVENTORY_TEXT


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


def test_2026_07_06_endpoint_rechecks_are_recorded(manifest_entries: list[dict]) -> None:
    entries_by_registry_id = _entries_by_registry_id(manifest_entries)
    taitel = entries_by_registry_id["REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE"]
    zuber_findlay = entries_by_registry_id["VOID-ZUBER-FINDLAY-1965-SOURCE-GATE"]

    assert "2026-07-06 Crossref record" in taitel["access_evidence"]["crossref"]
    assert "41 references" in taitel["access_evidence"]["crossref"]
    assert "HTTP 403 Cloudflare challenge" in taitel["access_evidence"]["endpoint_check"]
    assert "followed 301 to HTTPS" in zuber_findlay["access_evidence"]["endpoint_check"]
    assert "HTTP 403 Cloudflare challenge" in zuber_findlay["access_evidence"]["endpoint_check"]
    assert "Повторная endpoint-проверка 2026-07-06" in FOLLOWUP_AUDIT_TEXT
    assert "41 references" in FOLLOWUP_AUDIT_TEXT
    assert "Cloudflare challenge" in FOLLOWUP_AUDIT_TEXT


def test_osti_full_text_is_candidate_not_active_model(manifest_entries: list[dict]) -> None:
    osti = _entry_by_candidate_id(manifest_entries, "HTC-OSTI-1962-SOURCE-CANDIDATE")

    assert osti["registry_id"] == "HTC-CHEN-1962-SOURCE-CANDIDATE"
    assert osti["evidence_status"] == "full_text_available"
    assert osti["decision"] == "source_candidate"
    assert osti["local_full_text_ref"] == "sources/primary/chen_1962_osti_4636495.pdf"
    assert osti["source_candidate_audit_document"] == "docs/chen_1962_formula_audit_2026-07-06.md"
    assert "Content-Length 1533908" in osti["access_evidence"]["endpoint_check"]
    assert "HTTP 200" in osti["access_evidence"]["endpoint_check"]
    assert "Figures 7 and 8" in " ".join(osti["blocking_reasons"])
    assert "Eq. (17)" in " ".join(osti["blocking_reasons"])
    assert "Visually confirm Eq. (9) and Eq. (18)" in " ".join(osti["required_audit_checks"])
    assert "dryout or CHF" in " ".join(osti["blocking_reasons"])
    assert "10.2172/4636495" in OPEN_WEB_AUDIT_TEXT
    assert "3R Int." in FOLLOWUP_AUDIT_TEXT
    assert "candidate_only" in FOLLOWUP_AUDIT_TEXT
    assert "10.2172/4636495" in FORMULA_REGISTRY_TEXT
    assert "SOURCE_CANDIDATE / NOT_RELEASED" in FORMULA_REGISTRY_TEXT
    assert "Chen 1962 formula audit" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Eqs. (9), (17), and (18)" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Text-layer equation extraction status" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "h_mac = 0.023 * Re_L^0.8 * Pr_L^0.4 * k_L/D * F" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "h = h_mic + h_mac" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Eq. (17) micro-convective branch" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Figure extraction attempt" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "JBIG2" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Figs. 7 and 8" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "does not release a runtime heat-transfer correlation" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Pages 4, 6, 10-19, 20-25, 32-33" in PRIMARY_SOURCE_INVENTORY_TEXT


def test_milestone_closure_pipeline_lists_all_source_gate_work_orders(
    manifest_entries: list[dict],
) -> None:
    source_ids = {
        entry["registry_id"] or entry["candidate_id"]
        for entry in manifest_entries
    }

    for source_id in source_ids:
        assert source_id in MILESTONE_CLOSURE_PIPELINE_TEXT

    for group_id in (
        "local_candidate_audit",
        "secondary_guided_primary_required",
        "dissertation_guided_primary_required",
        "primary_acquisition_required",
    ):
        assert group_id in MILESTONE_CLOSURE_PIPELINE_TEXT

    assert "python -m source_gate_pipeline --pretty" in MILESTONE_CLOSURE_PIPELINE_TEXT
    assert "/api/source-gates" in MILESTONE_CLOSURE_PIPELINE_TEXT
    assert "docs/primary_source_inventory.md" in MILESTONE_CLOSURE_PIPELINE_TEXT
    assert "docs/formula_registry.md" in MILESTONE_CLOSURE_PIPELINE_TEXT
    assert "docs/source_gate_manifest.json" in MILESTONE_CLOSURE_PIPELINE_TEXT
    assert 'pytest -q -m "not slow" --durations=10' in MILESTONE_CLOSURE_PIPELINE_TEXT


def test_unresolved_questions_register_covers_all_source_gate_release_questions(
    manifest_entries: list[dict],
) -> None:
    source_ids = {
        entry["registry_id"] or entry["candidate_id"]
        for entry in manifest_entries
    }

    for source_id in source_ids:
        assert source_id in UNRESOLVED_QUESTIONS_TEXT

    for required_text in (
        "10.2172/4636495",
        "10.1016/0255-2701(86)80008-3",
        "3R International",
        "10.1115/1.3689137",
        "10.1016/j.ijheatmasstransfer.2004.12.012",
        "10.1002/aic.690260304",
        "10.1115/1.2910348",
        "10.1016/0017-9310(86)90205-X",
        "10.1016/j.ijheatmasstransfer.2004.12.013",
        "docs/source_gate_manifest.json",
        "docs/formula_registry.md",
        "docs/primary_source_inventory.md",
    ):
        assert required_text in UNRESOLVED_QUESTIONS_TEXT

    assert "Crossref records" in UNRESOLVED_QUESTIONS_TEXT
    assert "Required test proof" in UNRESOLVED_QUESTIONS_TEXT
    assert "Closure rule" in UNRESOLVED_QUESTIONS_TEXT
    assert "Eq. (9) and Eq. (18) structures are text-layer verified" in UNRESOLVED_QUESTIONS_TEXT
    assert "What is the exact Eq. (17) transcription" in UNRESOLVED_QUESTIONS_TEXT
    assert "Moreno Quiben TH3337 provides candidate text-layer formulas in Eqs. (4.53)-(4.56)" in UNRESOLVED_QUESTIONS_TEXT
    assert "Moreno Quiben TH3337 provides candidate text-layer formulas in Eqs. (4.40)-(4.47)" in UNRESOLVED_QUESTIONS_TEXT
    assert "TH3337 gives candidate dryout boundary formulas for `xdi` and `xde`" in UNRESOLVED_QUESTIONS_TEXT


def test_user_and_academic_docs_reference_open_web_audit_context() -> None:
    for text in (README_TEXT, ACADEMIC_REFERENCE_TEXT):
        assert "docs/source_audit_open_web_2026-07-05.md" in text
        assert "docs/source_audit_open_web_2026-07-04.md" in text
        assert "docs/source_gate_manifest.json" in text
        assert "docs/primary_source_inventory.md" in text
        assert "docs/chen_1962_formula_audit_2026-07-06.md" in text
        assert "docs/dissertation_formula_audit_2026-07-06.md" in text
        assert "source_gate_pipeline.py" in text
        assert "current_blocking_stage" in text
        assert "release_criteria" in text
        assert "sources/primary" in text
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
    assert "Source-gate closure pipeline" in ACADEMIC_REFERENCE_TEXT
    assert "candidate_local_intake_ready" in ACADEMIC_REFERENCE_TEXT
    assert "DISS-MORENO-QUIBEN-2005-EPFL-TH3337" in ACADEMIC_REFERENCE_TEXT
    assert "DISS-WOJTAN-2004-EPFL-TH2978" in ACADEMIC_REFERENCE_TEXT


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
