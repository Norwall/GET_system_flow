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
ENDPOINT_REFRESH_PATH = PROJECT_ROOT / "docs" / "source_endpoint_refresh_2026-07-07.md"
ENDPOINT_REFRESH_2026_07_08_PATH = PROJECT_ROOT / "docs" / "source_endpoint_refresh_2026-07-08.md"
DISSERTATION_FORMULA_AUDIT_PATH = PROJECT_ROOT / "docs" / "dissertation_formula_audit_2026-07-06.md"
CHEN_1962_FORMULA_AUDIT_PATH = PROJECT_ROOT / "docs" / "chen_1962_formula_audit_2026-07-06.md"
CHEN_1962_GRAPH_DIGITIZATION_PATH = PROJECT_ROOT / "docs" / "chen_1962_graph_digitization_2026-07-07.md"
CHEN_1962_GRAPH_REVIEW_PATH = PROJECT_ROOT / "docs" / "chen_1962_graph_review_2026-07-08.md"
CHEN_1962_SI_MAPPING_PATH = PROJECT_ROOT / "docs" / "chen_1962_si_mapping_2026-07-07.md"
CHEN_1962_VALIDATION_TABLES_PATH = (
    PROJECT_ROOT / "docs" / "chen_1962_validation_tables_2026-07-07.md"
)
CHEN_1962_REFERENCE_VALUE_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "chen_1962_reference_value_audit_2026-07-08.md"
)
CHEN_1962_SCOPE_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "chen_1962_scope_audit_2026-07-08.md"
)
CHEN_1962_HAND_CALCULATION_PATH = (
    PROJECT_ROOT / "docs" / "chen_1962_hand_calculation_2026-07-08.md"
)
WOJTAN_TH3337_DRYOUT_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "wojtan_th3337_dryout_boundary_audit_2026-07-07.md"
)
MORENO_TH3337_ANNULAR_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md"
)
MORENO_TH3337_MIST_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md"
)
MORENO_TH3337_DRYOUT_PRESSURE_DROP_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md"
)
MORENO_TH3337_SLUG_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md"
)
MORENO_TH3337_STRATIFIED_WAVY_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md"
)
WOJTAN_TH2978_TEXT_LAYER_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "wojtan_th2978_text_layer_audit_2026-07-08.md"
)
WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_PATH = (
    PROJECT_ROOT / "docs" / "wojtan_th2978_rendered_dryout_audit_2026-07-08.md"
)
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
ENDPOINT_REFRESH_TEXT = ENDPOINT_REFRESH_PATH.read_text(encoding="utf-8")
ENDPOINT_REFRESH_2026_07_08_TEXT = ENDPOINT_REFRESH_2026_07_08_PATH.read_text(
    encoding="utf-8"
)
DISSERTATION_FORMULA_AUDIT_TEXT = DISSERTATION_FORMULA_AUDIT_PATH.read_text(encoding="utf-8")
CHEN_1962_FORMULA_AUDIT_TEXT = CHEN_1962_FORMULA_AUDIT_PATH.read_text(encoding="utf-8")
CHEN_1962_GRAPH_DIGITIZATION_TEXT = CHEN_1962_GRAPH_DIGITIZATION_PATH.read_text(encoding="utf-8")
CHEN_1962_GRAPH_REVIEW_TEXT = CHEN_1962_GRAPH_REVIEW_PATH.read_text(encoding="utf-8")
CHEN_1962_SI_MAPPING_TEXT = CHEN_1962_SI_MAPPING_PATH.read_text(encoding="utf-8")
CHEN_1962_VALIDATION_TABLES_TEXT = CHEN_1962_VALIDATION_TABLES_PATH.read_text(encoding="utf-8")
CHEN_1962_REFERENCE_VALUE_AUDIT_TEXT = CHEN_1962_REFERENCE_VALUE_AUDIT_PATH.read_text(
    encoding="utf-8"
)
CHEN_1962_SCOPE_AUDIT_TEXT = CHEN_1962_SCOPE_AUDIT_PATH.read_text(encoding="utf-8")
CHEN_1962_HAND_CALCULATION_TEXT = CHEN_1962_HAND_CALCULATION_PATH.read_text(
    encoding="utf-8"
)
WOJTAN_TH3337_DRYOUT_AUDIT_TEXT = WOJTAN_TH3337_DRYOUT_AUDIT_PATH.read_text(encoding="utf-8")
MORENO_TH3337_ANNULAR_AUDIT_TEXT = MORENO_TH3337_ANNULAR_AUDIT_PATH.read_text(encoding="utf-8")
MORENO_TH3337_MIST_AUDIT_TEXT = MORENO_TH3337_MIST_AUDIT_PATH.read_text(encoding="utf-8")
MORENO_TH3337_DRYOUT_PRESSURE_DROP_AUDIT_TEXT = MORENO_TH3337_DRYOUT_PRESSURE_DROP_AUDIT_PATH.read_text(
    encoding="utf-8"
)
MORENO_TH3337_SLUG_AUDIT_TEXT = MORENO_TH3337_SLUG_AUDIT_PATH.read_text(encoding="utf-8")
MORENO_TH3337_STRATIFIED_WAVY_AUDIT_TEXT = MORENO_TH3337_STRATIFIED_WAVY_AUDIT_PATH.read_text(
    encoding="utf-8"
)
WOJTAN_TH2978_TEXT_LAYER_AUDIT_TEXT = WOJTAN_TH2978_TEXT_LAYER_AUDIT_PATH.read_text(
    encoding="utf-8"
)
WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_TEXT = WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_PATH.read_text(
    encoding="utf-8"
)
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
ALLOWED_RELEASE_BASES = {
    "journal_article",
    "conference_paper",
    "technical_report",
    "dissertation",
    "monograph",
    "handbook",
    "archival_scan",
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
    "release_basis",
    "allowed_release_bases",
    "audited_source_ref",
    "audited_equations",
    "source_scope",
    "source_limitations",
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
    assert ENDPOINT_REFRESH_PATH.exists()
    assert ENDPOINT_REFRESH_2026_07_08_PATH.exists()
    assert DISSERTATION_FORMULA_AUDIT_PATH.exists()
    assert CHEN_1962_FORMULA_AUDIT_PATH.exists()
    assert CHEN_1962_GRAPH_DIGITIZATION_PATH.exists()
    assert CHEN_1962_GRAPH_REVIEW_PATH.exists()
    assert CHEN_1962_SI_MAPPING_PATH.exists()
    assert CHEN_1962_VALIDATION_TABLES_PATH.exists()
    assert CHEN_1962_REFERENCE_VALUE_AUDIT_PATH.exists()
    assert CHEN_1962_SCOPE_AUDIT_PATH.exists()
    assert CHEN_1962_HAND_CALCULATION_PATH.exists()
    assert WOJTAN_TH3337_DRYOUT_AUDIT_PATH.exists()
    assert WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_PATH.exists()
    assert MORENO_TH3337_ANNULAR_AUDIT_PATH.exists()
    assert MORENO_TH3337_MIST_AUDIT_PATH.exists()
    assert MORENO_TH3337_DRYOUT_PRESSURE_DROP_AUDIT_PATH.exists()
    assert MORENO_TH3337_SLUG_AUDIT_PATH.exists()
    assert MORENO_TH3337_STRATIFIED_WAVY_AUDIT_PATH.exists()
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
    assert "docs/source_endpoint_refresh_2026-07-07.md" in policy["previous_audit_documents"]
    assert "docs/source_endpoint_refresh_2026-07-08.md" in policy["previous_audit_documents"]
    assert "docs/chen_1962_graph_digitization_2026-07-07.md" in policy["previous_audit_documents"]
    assert "docs/chen_1962_graph_review_2026-07-08.md" in policy["previous_audit_documents"]
    assert "docs/chen_1962_si_mapping_2026-07-07.md" in policy["previous_audit_documents"]
    assert "docs/chen_1962_validation_tables_2026-07-07.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/chen_1962_reference_value_audit_2026-07-08.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/chen_1962_scope_audit_2026-07-08.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/chen_1962_hand_calculation_2026-07-08.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/wojtan_th2978_text_layer_audit_2026-07-08.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md" in policy[
        "previous_audit_documents"
    ]
    assert "docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md" in policy[
        "previous_audit_documents"
    ]
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
    assert set(policy["accepted_full_text_source_types"]) == ALLOWED_RELEASE_BASES
    assert "dissertation" in policy["release_basis_rule"]
    assert "release_basis must name the audited source type" in policy["released_requirements"]
    assert "audited_equations must list the released page/equation references" in policy["released_requirements"]


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
        assert entry["release_basis"] in ALLOWED_RELEASE_BASES
        assert isinstance(entry["allowed_release_bases"], list) and entry["allowed_release_bases"]
        assert set(entry["allowed_release_bases"]) <= ALLOWED_RELEASE_BASES
        assert entry["release_basis"] in entry["allowed_release_bases"]
        assert isinstance(entry["audited_source_ref"], str)
        assert isinstance(entry["audited_equations"], list)
        assert isinstance(entry["source_scope"], str) and entry["source_scope"]
        assert isinstance(entry["source_limitations"], list) and entry["source_limitations"]

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
        assert entry["audited_source_ref"].startswith(source_drop_prefix)
        assert entry["audited_equations"]
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
    assert "docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md" in (
        part_i_candidates[0]["audit_note"]
    )
    assert "docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md" in (
        part_ii_candidates[0]["audit_note"]
    )
    assert "Eqs. (7.47)-(7.48)" in part_i_candidates[0]["audit_note"]
    assert "Eqs. (7.47)-(7.48)" in part_ii_candidates[0]["audit_note"]


def test_dissertation_formula_audit_records_page_level_candidate_map() -> None:
    assert "Moreno Quiben TH3337 page map" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "53-66" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "Friedel section" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "Muller-Steinhagen and Heck section" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "Moreno Quiben TH3337 text-layer formula guidance" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "phi_f0^2 = E + 3.24 * F * H / (Fr_H^0.045 * We_L^0.035)" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "(dp/dz)_frict = F*(1-x)^(1/3) + B*x^3" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "friedel_th3337_candidate_two_phase_multiplier" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "muller_steinhagen_heck_th3337_candidate_pressure_gradient_pa_per_m" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "(f_i)_annular = 0.67" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "xdi = 0.58*exp" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "xde = 0.61*exp" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "wojtan_th3337_candidate_dryout_boundaries" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "Wojtan / TH3337 dryout-boundary candidate audit 2026-07-07" in (
        WOJTAN_TH3337_DRYOUT_AUDIT_TEXT
    )
    assert "xdi = 0.5047352096" in WOJTAN_TH3337_DRYOUT_AUDIT_TEXT
    assert "xde = 0.9791233757" in WOJTAN_TH3337_DRYOUT_AUDIT_TEXT
    assert "not connected to `CO2MathcadModel.run(...)`" in WOJTAN_TH3337_DRYOUT_AUDIT_TEXT
    assert "Moreno Quiben TH3337 annular pressure-drop audit 2026-07-07" in (
        MORENO_TH3337_ANNULAR_AUDIT_TEXT
    )
    assert "Eq. (7.1)-(7.5)" in MORENO_TH3337_ANNULAR_AUDIT_TEXT
    assert "f_i = 0.0314880634" in MORENO_TH3337_ANNULAR_AUDIT_TEXT
    assert "Delta p / L = 12091.4163488975 Pa/m" in MORENO_TH3337_ANNULAR_AUDIT_TEXT
    assert "moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m" in (
        MORENO_TH3337_ANNULAR_AUDIT_TEXT
    )
    assert "Moreno Quiben TH3337 mist pressure-drop audit 2026-07-07" in (
        MORENO_TH3337_MIST_AUDIT_TEXT
    )
    assert "Eq. (7.13)-(7.17)" in MORENO_TH3337_MIST_AUDIT_TEXT
    assert "alpha_H = 0.9972299169" in MORENO_TH3337_MIST_AUDIT_TEXT
    assert "Delta p / L = 5120.0016535769 Pa/m" in MORENO_TH3337_MIST_AUDIT_TEXT
    assert "moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m" in (
        MORENO_TH3337_MIST_AUDIT_TEXT
    )
    assert "Moreno Quiben TH3337 dryout pressure-drop audit 2026-07-07" in (
        MORENO_TH3337_DRYOUT_PRESSURE_DROP_AUDIT_TEXT
    )
    assert "Eq. (7.18)" in MORENO_TH3337_DRYOUT_PRESSURE_DROP_AUDIT_TEXT
    assert "Delta p / L = 6500.0 Pa/m" in MORENO_TH3337_DRYOUT_PRESSURE_DROP_AUDIT_TEXT
    assert "moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m" in (
        MORENO_TH3337_DRYOUT_PRESSURE_DROP_AUDIT_TEXT
    )
    assert "Moreno Quiben TH3337 slug pressure-drop audit 2026-07-07" in (
        MORENO_TH3337_SLUG_AUDIT_TEXT
    )
    assert "Eqs. (7.6) and (7.12)" in MORENO_TH3337_SLUG_AUDIT_TEXT
    assert "Delta p / L = 5045.3784915223 Pa/m" in MORENO_TH3337_SLUG_AUDIT_TEXT
    assert "moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m" in (
        MORENO_TH3337_SLUG_AUDIT_TEXT
    )
    assert "Moreno Quiben TH3337 stratified-wavy pressure-drop audit 2026-07-08" in (
        MORENO_TH3337_STRATIFIED_WAVY_AUDIT_TEXT
    )
    assert "Eqs. (7.9)-(7.11)" in MORENO_TH3337_STRATIFIED_WAVY_AUDIT_TEXT
    assert "Delta p / L = 9444.2496469004 Pa/m" in MORENO_TH3337_STRATIFIED_WAVY_AUDIT_TEXT
    assert "moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m" in (
        MORENO_TH3337_STRATIFIED_WAVY_AUDIT_TEXT
    )
    assert "Wojtan TH2978 page map" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "Wojtan TH2978 text-layer audit 2026-07-08" in WOJTAN_TH2978_TEXT_LAYER_AUDIT_TEXT
    assert "pages 172-183" in WOJTAN_TH2978_TEXT_LAYER_AUDIT_TEXT
    assert "`hexp`, `xdi`, `xde`" in WOJTAN_TH2978_TEXT_LAYER_AUDIT_TEXT
    assert "not release a regime map" in WOJTAN_TH2978_TEXT_LAYER_AUDIT_TEXT
    assert "custom-encoded" in WOJTAN_TH2978_TEXT_LAYER_AUDIT_TEXT
    assert "Wojtan TH2978 rendered dryout audit 2026-07-08" in (
        WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_TEXT
    )
    assert "Eqs. (7.47)-(7.48)" in WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_TEXT
    assert "xdi = 0.58 * exp" in WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_TEXT
    assert "xde = 0.61 * exp" in WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_TEXT
    assert "wojtan_th2978_candidate_dryout_limits" in (
        WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_TEXT
    )
    assert "0.5047352096" in WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_TEXT
    assert "0.9791233757" in WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_TEXT
    assert "Eq. (7.49)" in WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_TEXT
    assert "requires OCR/manual audit" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "candidate_only" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "does not release" in DISSERTATION_FORMULA_AUDIT_TEXT
    assert "docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md" in (
        DISSERTATION_FORMULA_AUDIT_TEXT
    )
    assert "20-25, 53-66, 109-125, 146, 149, 152" in PRIMARY_SOURCE_INVENTORY_TEXT
    assert "172-184" in PRIMARY_SOURCE_INVENTORY_TEXT
    assert "docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md" in (
        PRIMARY_SOURCE_INVENTORY_TEXT
    )
    assert "docs/dissertation_formula_audit_2026-07-06.md" in FORMULA_REGISTRY_TEXT
    assert "TH3337 text layer gives candidate Eqs. (4.53)-(4.56)" in FORMULA_REGISTRY_TEXT
    assert "TH3337 text layer gives candidate Eqs. (4.40)-(4.47)" in FORMULA_REGISTRY_TEXT
    assert "friedel_th3337_candidate_pressure_gradient_pa_per_m" in FORMULA_REGISTRY_TEXT
    assert "muller_steinhagen_heck_th3337_candidate_pressure_gradient_pa_per_m" in FORMULA_REGISTRY_TEXT
    assert "moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m" in FORMULA_REGISTRY_TEXT
    assert "moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m" in FORMULA_REGISTRY_TEXT
    assert "moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m" in (
        FORMULA_REGISTRY_TEXT
    )
    assert "moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m" in (
        FORMULA_REGISTRY_TEXT
    )
    assert "moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m" in (
        FORMULA_REGISTRY_TEXT
    )
    assert "HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE" in FORMULA_REGISTRY_TEXT
    assert "wojtan_th2978_candidate_dryout_limits" in FORMULA_REGISTRY_TEXT
    assert "wojtan_th3337_candidate_dryout_inception_quality" in FORMULA_REGISTRY_TEXT
    assert "Runtime `dryout_limit` remains `not_evaluated_source_required`" in FORMULA_REGISTRY_TEXT


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
        ENDPOINT_REFRESH_TEXT,
        DISSERTATION_FORMULA_AUDIT_TEXT,
        CHEN_1962_FORMULA_AUDIT_TEXT,
        CHEN_1962_GRAPH_DIGITIZATION_TEXT,
        CHEN_1962_GRAPH_REVIEW_TEXT,
        CHEN_1962_SI_MAPPING_TEXT,
        CHEN_1962_VALIDATION_TABLES_TEXT,
        CHEN_1962_REFERENCE_VALUE_AUDIT_TEXT,
        CHEN_1962_SCOPE_AUDIT_TEXT,
        CHEN_1962_HAND_CALCULATION_TEXT,
        WOJTAN_TH3337_DRYOUT_AUDIT_TEXT,
        WOJTAN_TH2978_RENDERED_DRYOUT_AUDIT_TEXT,
        MORENO_TH3337_ANNULAR_AUDIT_TEXT,
        MORENO_TH3337_MIST_AUDIT_TEXT,
        MORENO_TH3337_DRYOUT_PRESSURE_DROP_AUDIT_TEXT,
        MORENO_TH3337_SLUG_AUDIT_TEXT,
        MORENO_TH3337_STRATIFIED_WAVY_AUDIT_TEXT,
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
        assert "docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md" in " ".join(
            entry["source_limitations"]
        )
        assert "docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md" in " ".join(
            entry["source_limitations"]
        )

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


def test_2026_07_07_endpoint_refresh_keeps_source_gates_closed(manifest_entries: list[dict]) -> None:
    entries_by_registry_id = _entries_by_registry_id(manifest_entries)
    msh = entries_by_registry_id["TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE"]
    friedel = entries_by_registry_id["TP-FRIEDEL-1979-SOURCE-GATE"]
    zuber_findlay = entries_by_registry_id["VOID-ZUBER-FINDLAY-1965-SOURCE-GATE"]
    part_i = entries_by_registry_id["REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE"]
    taitel = entries_by_registry_id["REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE"]
    kandlikar = _entry_by_candidate_id(manifest_entries, "HTC-KANDLIKAR-1990-SOURCE-CANDIDATE")
    gungor = _entry_by_candidate_id(manifest_entries, "HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE")
    part_ii = _entry_by_candidate_id(manifest_entries, "HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE")

    assert "Source endpoint refresh 2026-07-07" in ENDPOINT_REFRESH_TEXT
    assert "OpenAlex `oa_status=green` is not release evidence" in ENDPOINT_REFRESH_TEXT
    assert "sources/primary" in ENDPOINT_REFRESH_TEXT
    assert "docs/primary_source_inventory.md" in ENDPOINT_REFRESH_TEXT

    assert "2026-07-07 unauthenticated probe returned HTTP 400 text/xml" in msh["access_evidence"]["endpoint_check"]
    assert "2026-07-07 refresh still found no DOI" in friedel["access_evidence"]["endpoint_check"]
    assert "2026-07-07 ASME article/PDF endpoints returned HTTP 403" in zuber_findlay["access_evidence"]["endpoint_check"]
    assert "2026-07-07 Wiley article/PDF endpoints returned HTTP 403" in taitel["access_evidence"]["endpoint_check"]
    assert "2026-07-07 ASME article/PDF endpoints returned HTTP 403" in kandlikar["access_evidence"]["endpoint_check"]
    assert "2026-07-07 unauthenticated probe returned HTTP 400 text/xml" in gungor["access_evidence"]["endpoint_check"]

    for entry in (part_i, part_ii):
        assert "OpenAlex green landing route still had no pdf_url" in entry["access_evidence"]["endpoint_check"]
        assert "license.txt/JPEG only" in entry["access_evidence"]["endpoint_check"]
        assert entry["decision"] == "source_required"

    for source_id in (
        "TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE",
        "TP-FRIEDEL-1979-SOURCE-GATE",
        "VOID-ZUBER-FINDLAY-1965-SOURCE-GATE",
        "REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE",
        "REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE",
        "HTC-KANDLIKAR-1990-SOURCE-CANDIDATE",
        "HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE",
        "HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE",
    ):
        assert source_id in ENDPOINT_REFRESH_TEXT


def test_2026_07_08_endpoint_refresh_keeps_source_gates_closed(manifest_entries: list[dict]) -> None:
    entries_by_registry_id = _entries_by_registry_id(manifest_entries)
    msh = entries_by_registry_id["TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE"]
    friedel = entries_by_registry_id["TP-FRIEDEL-1979-SOURCE-GATE"]
    zuber_findlay = entries_by_registry_id["VOID-ZUBER-FINDLAY-1965-SOURCE-GATE"]
    part_i = entries_by_registry_id["REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE"]
    taitel = entries_by_registry_id["REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE"]
    kandlikar = _entry_by_candidate_id(manifest_entries, "HTC-KANDLIKAR-1990-SOURCE-CANDIDATE")
    gungor = _entry_by_candidate_id(manifest_entries, "HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE")
    part_ii = _entry_by_candidate_id(manifest_entries, "HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE")
    osti = _entry_by_candidate_id(manifest_entries, "HTC-OSTI-1962-SOURCE-CANDIDATE")

    assert "Source endpoint refresh 2026-07-08" in ENDPOINT_REFRESH_2026_07_08_TEXT
    assert "HTTP 400/403/429 responses" in ENDPOINT_REFRESH_2026_07_08_TEXT
    assert "OpenAlex remained `is_oa=false`, `oa_status=closed`" in ENDPOINT_REFRESH_2026_07_08_TEXT
    assert "Crossref bibliographic searches" in ENDPOINT_REFRESH_2026_07_08_TEXT
    assert "not release any `SOURCE_REQUIRED`" in ENDPOINT_REFRESH_2026_07_08_TEXT
    assert "No TDM Client Token was found in the request" in ENDPOINT_REFRESH_2026_07_08_TEXT
    assert "Modelling flow pattern transitions for steady upward gas-liquid flow in vertical tubes" in (
        ENDPOINT_REFRESH_2026_07_08_TEXT
    )
    assert "MSH Crossref reference list does identify Friedel" in (
        ENDPOINT_REFRESH_2026_07_08_TEXT
    )

    assert "2026-07-08 DOI redirected to Elsevier landing HTTP 200" in msh["access_evidence"][
        "endpoint_check"
    ]
    assert "MSH Crossref reference list identified Friedel, 3R Int. 18(7), page 485" in (
        friedel["access_evidence"]["endpoint_check"]
    )
    assert "2026-07-08 Crossref bibliographic searches still returned no reliable Friedel" in (
        friedel["access_evidence"]["endpoint_check"]
    )
    assert "2026-07-08 DOI route reached ASME landing with HTTP 403" in (
        zuber_findlay["access_evidence"]["endpoint_check"]
    )
    assert "2026-07-08 DOI route and Wiley PDF endpoint returned HTTP 403 text/html" in (
        taitel["access_evidence"]["endpoint_check"]
    )
    assert "no TDM Client Token was found" in taitel["access_evidence"]["endpoint_check"]
    assert "exact title 'Modelling flow pattern transitions" in taitel["access_evidence"][
        "crossref"
    ]
    assert "2026-07-08 DOI route reached ASME landing with HTTP 403" in (
        kandlikar["access_evidence"]["endpoint_check"]
    )
    assert "2026-07-08 DOI redirected to Elsevier landing HTTP 200" in (
        gungor["access_evidence"]["endpoint_check"]
    )
    assert "HTTP 429 application/json" in gungor["access_evidence"]["endpoint_check"]
    assert "follow-up Python HEAD returned HTTP 400 text/xml" in (
        gungor["access_evidence"]["endpoint_check"]
    )
    assert "2026-07-08 OSTI record returned HTTP 200 HTML" in osti["access_evidence"][
        "endpoint_check"
    ]

    for entry in (part_i, part_ii):
        assert "2026-07-08 OpenAlex remained green with EPFL landing" in entry[
            "access_evidence"
        ]["endpoint_check"]
        assert "HTTP 429" in entry["access_evidence"]["endpoint_check"]
        assert entry["decision"] == "source_required"

    for source_id in (
        "TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE",
        "TP-FRIEDEL-1979-SOURCE-GATE",
        "VOID-ZUBER-FINDLAY-1965-SOURCE-GATE",
        "REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE",
        "REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE",
        "HTC-KANDLIKAR-1990-SOURCE-CANDIDATE",
        "HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE",
        "HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE",
        "HTC-CHEN-1962-SOURCE-CANDIDATE",
    ):
        assert source_id in ENDPOINT_REFRESH_2026_07_08_TEXT


def test_osti_full_text_is_candidate_not_active_model(manifest_entries: list[dict]) -> None:
    osti = _entry_by_candidate_id(manifest_entries, "HTC-OSTI-1962-SOURCE-CANDIDATE")

    assert osti["registry_id"] == "HTC-CHEN-1962-SOURCE-CANDIDATE"
    assert osti["evidence_status"] == "full_text_available"
    assert osti["decision"] == "source_candidate"
    assert osti["local_full_text_ref"] == "sources/primary/chen_1962_osti_4636495.pdf"
    assert osti["source_candidate_audit_document"] == "docs/chen_1962_formula_audit_2026-07-06.md"
    assert "docs/chen_1962_graph_review_2026-07-08.md" in osti[
        "source_candidate_audit_documents"
    ]
    assert "docs/chen_1962_validation_tables_2026-07-07.md" in osti[
        "source_candidate_audit_documents"
    ]
    assert "docs/chen_1962_reference_value_audit_2026-07-08.md" in osti[
        "source_candidate_audit_documents"
    ]
    assert "docs/chen_1962_scope_audit_2026-07-08.md" in osti[
        "source_candidate_audit_documents"
    ]
    assert "docs/chen_1962_hand_calculation_2026-07-08.md" in osti[
        "source_candidate_audit_documents"
    ]
    assert "Content-Length 1533908" in osti["access_evidence"]["endpoint_check"]
    assert "HTTP 200" in osti["access_evidence"]["endpoint_check"]
    assert "Figures 7 and 8" in " ".join(osti["blocking_reasons"])
    assert "candidate digitization" in " ".join(osti["blocking_reasons"])
    assert "rendered review" in " ".join(osti["blocking_reasons"])
    assert "Eqs. (9), (17), and (18) are scan-verified" in " ".join(osti["blocking_reasons"])
    assert "candidate source-unit to SI, graph-axis, and graph-to-SI composition helpers" in " ".join(
        osti["required_audit_checks"]
    )
    assert "docs/chen_1962_graph_digitization_2026-07-07.md" in " ".join(osti["required_audit_checks"])
    assert "docs/chen_1962_graph_review_2026-07-08.md" in " ".join(
        osti["required_audit_checks"]
    )
    assert "docs/chen_1962_si_mapping_2026-07-07.md" in " ".join(osti["required_audit_checks"])
    assert "docs/chen_1962_reference_value_audit_2026-07-08.md" in " ".join(
        osti["required_audit_checks"]
    )
    assert "vertical-only geometry scope" in " ".join(osti["required_audit_checks"])
    assert "horizontal evaporator" in " ".join(osti["blocking_reasons"])
    assert "docs/chen_1962_hand_calculation_2026-07-08.md" in " ".join(
        osti["required_audit_checks"]
    )
    assert "another primary source" in " ".join(osti["required_tests_before_release"])
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
    assert "h_mic = 0.00122" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "h = h_mic + h_mac" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Eq. (17) micro-convective branch" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Figure extraction attempt" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "PyMuPDF 1.28.0" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "source-unit to SI mapping" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Figs. 7 and 8" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "candidate_reviewed_not_released" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Chen 1962 graph digitization 2026-07-07" in CHEN_1962_GRAPH_DIGITIZATION_TEXT
    assert "F_candidate(Y) = 2.35 * (Y + 0.213)^0.736" in CHEN_1962_GRAPH_DIGITIZATION_TEXT
    assert "S_candidate(R) = 1 / (1 + 1.024e-5 * R^1.0397)" in CHEN_1962_GRAPH_DIGITIZATION_TEXT
    assert "| 10 | 13.0 |" in CHEN_1962_GRAPH_DIGITIZATION_TEXT
    assert "| 1.0e5 | 0.37 |" in CHEN_1962_GRAPH_DIGITIZATION_TEXT
    assert "refuses extrapolation" in CHEN_1962_GRAPH_DIGITIZATION_TEXT
    assert "`0.1 <= 1/X_tt <= 100`" in CHEN_1962_GRAPH_DIGITIZATION_TEXT
    assert "`1.5e4 <= Re_L*F^1.25 <= 7e5`" in CHEN_1962_GRAPH_DIGITIZATION_TEXT
    assert "Neither document closes the source gate" in CHEN_1962_GRAPH_DIGITIZATION_TEXT
    assert "Chen 1962 rendered graph review 2026-07-08" in CHEN_1962_GRAPH_REVIEW_TEXT
    assert "F_candidate(Y) = 2.35 * (Y + 0.213)^0.736" in CHEN_1962_GRAPH_REVIEW_TEXT
    assert "S_candidate(R) = 1 / (1 + 1.024e-5 * R^1.0397)" in CHEN_1962_GRAPH_REVIEW_TEXT
    assert "0.0137" in CHEN_1962_GRAPH_REVIEW_TEXT
    assert "authoritative table" in CHEN_1962_GRAPH_REVIEW_TEXT
    assert "Chen 1962 SI mapping audit 2026-07-07" in CHEN_1962_SI_MAPPING_TEXT
    assert "1 Btu/(hr ft^2 degF)" in CHEN_1962_SI_MAPPING_TEXT
    assert "5.678263341 W/(m^2 K)" in CHEN_1962_SI_MAPPING_TEXT
    assert "g_c_hr     = 4.1697567e8" in CHEN_1962_SI_MAPPING_TEXT
    assert "DeltaP` in Eq. (17) is the vapor-pressure" in CHEN_1962_SI_MAPPING_TEXT
    assert "h_total_si  = h_total_src * 5.678263341" in CHEN_1962_SI_MAPPING_TEXT
    assert "chen_1962_candidate_heat_transfer_coefficient_si" in CHEN_1962_SI_MAPPING_TEXT
    assert "chen_1962_candidate_inverse_martinelli_parameter" in CHEN_1962_SI_MAPPING_TEXT
    assert "chen_1962_candidate_two_phase_reynolds" in CHEN_1962_SI_MAPPING_TEXT
    assert "chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si" in CHEN_1962_SI_MAPPING_TEXT
    assert "Values outside that range are rejected" in CHEN_1962_SI_MAPPING_TEXT
    assert "0.01 <= x <= 0.70" in CHEN_1962_SI_MAPPING_TEXT
    assert "source-scope vapor" in UNRESOLVED_QUESTIONS_TEXT
    assert "h_total_si = 33774.2953703176 W/(m^2 K)" in CHEN_1962_SI_MAPPING_TEXT
    assert "h_total_si = 10029.9154249347 W/(m^2 K)" in CHEN_1962_SI_MAPPING_TEXT
    assert "not a Chen report" in CHEN_1962_SI_MAPPING_TEXT
    assert "validation point" in CHEN_1962_SI_MAPPING_TEXT
    assert "Chen 1962 validation tables audit 2026-07-07" in CHEN_1962_VALIDATION_TABLES_TEXT
    assert "| 1 | water | tube | up | 8-40 | 0.2-4.8 | 15-71 | 2.8-20 |" in (
        CHEN_1962_VALIDATION_TABLES_TEXT
    )
    assert "| Combined average for all data | 38.1 | 42.6 | 32.6 | 31.7 | 11.0 |" in (
        CHEN_1962_VALIDATION_TABLES_TEXT
    )
    assert "no raw HTC measurements or pointwise predicted HTC values" in (
        CHEN_1962_VALIDATION_TABLES_TEXT
    )
    assert (
        "Chen 1962 reference-value audit 2026-07-08"
        in CHEN_1962_REFERENCE_VALUE_AUDIT_TEXT
    )
    assert "No pointwise Chen-report HTC reference cases" in (
        CHEN_1962_REFERENCE_VALUE_AUDIT_TEXT
    )
    assert "Table I" in CHEN_1962_REFERENCE_VALUE_AUDIT_TEXT
    assert "Table II" in CHEN_1962_REFERENCE_VALUE_AUDIT_TEXT
    assert "Figs. 9 and 10" in CHEN_1962_REFERENCE_VALUE_AUDIT_TEXT
    assert "release-grade hand calculation" in CHEN_1962_REFERENCE_VALUE_AUDIT_TEXT
    assert "Chen 1962 applicability and geometry-scope audit 2026-07-08" in (
        CHEN_1962_SCOPE_AUDIT_TEXT
    )
    assert "vertical heated axial flow only" in CHEN_1962_SCOPE_AUDIT_TEXT
    assert "horizontal evaporator is unsupported" in CHEN_1962_SCOPE_AUDIT_TEXT
    assert "`0.01 <= x <= 0.70`" in CHEN_1962_SCOPE_AUDIT_TEXT
    assert "not printed pointwise HTC references" in MILESTONE_CLOSURE_PIPELINE_TEXT
    assert "does not release a runtime heat-transfer correlation" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "code-level hand-calculation helper" in CHEN_1962_FORMULA_AUDIT_TEXT
    assert "Chen 1962 hand-calculation ledger 2026-07-08" in CHEN_1962_HAND_CALCULATION_TEXT
    assert "h_mac = 0.023 * Re_L^0.8 * Pr_L^0.4 * (k_L / D) * F" in (
        CHEN_1962_HAND_CALCULATION_TEXT
    )
    assert "h_mic = 0.00122" in CHEN_1962_HAND_CALCULATION_TEXT
    assert "`h_total` | `10029.9154249347 W/(m^2 K)`" in CHEN_1962_HAND_CALCULATION_TEXT
    assert "`1/X_tt` | `8.3744338927`" in CHEN_1962_HAND_CALCULATION_TEXT
    assert "`h_total` | `5947.9973615260` | `33774.2953703176 W/(m^2 K)`" in (
        CHEN_1962_HAND_CALCULATION_TEXT
    )
    assert "pointwise experimental value printed by the Chen report" in (
        CHEN_1962_HAND_CALCULATION_TEXT
    )
    assert "docs/chen_1962_graph_review_2026-07-08.md" in CHEN_1962_HAND_CALCULATION_TEXT
    assert "Pages 4, 6, 10-19, 20-25, 32-35" in PRIMARY_SOURCE_INVENTORY_TEXT


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
    assert "docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "docs/chen_1962_graph_review_2026-07-08.md" in MILESTONE_CLOSURE_PIPELINE_TEXT
    assert "Accepted `F/S` interpolation or authoritative table" in MILESTONE_CLOSURE_PIPELINE_TEXT
    assert "docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "wojtan_th2978_candidate_dryout_limits" in MILESTONE_CLOSURE_PIPELINE_TEXT
    assert "wojtan_th3337_candidate_dryout_boundaries" in MILESTONE_CLOSURE_PIPELINE_TEXT
    assert "docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )
    assert "moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m" in (
        MILESTONE_CLOSURE_PIPELINE_TEXT
    )


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
        "docs/chen_1962_graph_review_2026-07-08.md",
    ):
        assert required_text in UNRESOLVED_QUESTIONS_TEXT

    assert "Crossref records" in UNRESOLVED_QUESTIONS_TEXT
    assert "Required test proof" in UNRESOLVED_QUESTIONS_TEXT
    assert "Closure rule" in UNRESOLVED_QUESTIONS_TEXT
    assert "Eqs. (9), (17), and (18) are visually verified" in UNRESOLVED_QUESTIONS_TEXT
    assert "rendered graph review now checks candidate" in UNRESOLVED_QUESTIONS_TEXT
    assert "accepted release-grade hand calculation" in UNRESOLVED_QUESTIONS_TEXT
    assert "candidate SI mapping, dimensionless axis helpers" in UNRESOLVED_QUESTIONS_TEXT
    assert "chen_1962_candidate_inverse_martinelli_parameter" in UNRESOLVED_QUESTIONS_TEXT
    assert "chen_1962_candidate_two_phase_reynolds" in UNRESOLVED_QUESTIONS_TEXT
    assert "chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si" in UNRESOLVED_QUESTIONS_TEXT
    assert "Moreno Quiben TH3337 provides candidate text-layer formulas in Eqs. (4.53)-(4.56)" in UNRESOLVED_QUESTIONS_TEXT
    assert "Moreno Quiben TH3337 provides candidate text-layer formulas in Eqs. (4.40)-(4.47)" in UNRESOLVED_QUESTIONS_TEXT
    assert "friedel_th3337_candidate_two_phase_multiplier" in UNRESOLVED_QUESTIONS_TEXT
    assert "muller_steinhagen_heck_th3337_candidate_pressure_gradient_pa_per_m" in UNRESOLVED_QUESTIONS_TEXT
    assert "TH2978 rendered pages give candidate dryout-limit formulas for `xdi` and `xde`" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "TH3337 corroborates the same dryout-boundary family" in UNRESOLVED_QUESTIONS_TEXT
    assert "wojtan_th3337_candidate_dryout_boundaries" in UNRESOLVED_QUESTIONS_TEXT
    assert "docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md" in UNRESOLVED_QUESTIONS_TEXT
    assert "TH3337 annular pressure-drop branch gives Eq. (7.4)/(7.5)" in UNRESOLVED_QUESTIONS_TEXT
    assert "moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m" in UNRESOLVED_QUESTIONS_TEXT
    assert "docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "TH3337 mist pressure-drop branch gives Eq. (7.13)/(7.17)" in UNRESOLVED_QUESTIONS_TEXT
    assert "moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m" in UNRESOLVED_QUESTIONS_TEXT
    assert "docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "TH3337 dryout pressure-drop interpolation gives Eq. (7.18)" in UNRESOLVED_QUESTIONS_TEXT
    assert "moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "TH3337 slug/intermittent pressure-drop interpolation gives Eq. (7.6)/(7.12)" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "TH3337 stratified-wavy pressure-drop branch gives Eq. (7.9)/(7.11)" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "docs/wojtan_th2978_text_layer_audit_2026-07-08.md" in UNRESOLVED_QUESTIONS_TEXT
    assert "docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "wojtan_th2978_candidate_dryout_limits" in UNRESOLVED_QUESTIONS_TEXT
    assert "Eqs. (7.47)-(7.48)" in UNRESOLVED_QUESTIONS_TEXT
    assert "moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m" in (
        UNRESOLVED_QUESTIONS_TEXT
    )
    assert "docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md" in (
        UNRESOLVED_QUESTIONS_TEXT
    )


def test_user_and_academic_docs_reference_open_web_audit_context() -> None:
    for text in (README_TEXT, ACADEMIC_REFERENCE_TEXT):
        assert "docs/source_audit_open_web_2026-07-05.md" in text
        assert "docs/source_audit_open_web_2026-07-04.md" in text
        assert "docs/source_endpoint_refresh_2026-07-07.md" in text
        assert "docs/source_endpoint_refresh_2026-07-08.md" in text
        assert "docs/chen_1962_graph_digitization_2026-07-07.md" in text
        assert "docs/chen_1962_graph_review_2026-07-08.md" in text
        assert "docs/chen_1962_si_mapping_2026-07-07.md" in text
        assert "docs/chen_1962_validation_tables_2026-07-07.md" in text
        assert "docs/chen_1962_reference_value_audit_2026-07-08.md" in text
        assert "docs/chen_1962_scope_audit_2026-07-08.md" in text
        assert "docs/chen_1962_hand_calculation_2026-07-08.md" in text
        assert "docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md" in text
        assert "docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md" in text
        assert "docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md" in text
        assert "docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md" in text
        assert "docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md" in text
        assert "docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md" in text
        assert "docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md" in text
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
        assert "chen_1962_candidate_heat_transfer_coefficient_si" in text
        assert "chen_1962_candidate_inverse_martinelli_parameter" in text
        assert "chen_1962_candidate_two_phase_reynolds" in text
        assert "chen_1962_candidate_flow_boiling_heat_transfer_coefficient_si" in text
        assert "wojtan_th3337_candidate_dryout_boundaries" in text
        assert "wojtan_th2978_candidate_dryout_limits" in text
        assert "moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m" in text
        assert "moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m" in text
        assert "moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m" in text
        assert "moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m" in text
        assert "moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m" in text

    assert "EPFL" in README_TEXT
    assert "landing pages" in README_TEXT
    assert "ORIGINAL`/full-text bitstream" in README_TEXT
    assert "Академический контекст и source-gate" in README_TEXT
    assert "source_candidate` означает, что полный текст найден" in README_TEXT
    assert "EPFL landing page без доступного `ORIGINAL`/full-text bitstream" in ACADEMIC_REFERENCE_TEXT
    assert "Минимальная цепочка интерпретации" in ACADEMIC_REFERENCE_TEXT
    assert "OSTI `10.2172/4636495`" in ACADEMIC_REFERENCE_TEXT
    assert "source_candidate" in ACADEMIC_REFERENCE_TEXT
    assert "candidate helper" in ACADEMIC_REFERENCE_TEXT
    assert "source/reference HTC" in ACADEMIC_REFERENCE_TEXT
    assert "Source-gate closure pipeline" in ACADEMIC_REFERENCE_TEXT
    assert "candidate_local_intake_ready" in ACADEMIC_REFERENCE_TEXT
    assert "DISS-MORENO-QUIBEN-2005-EPFL-TH3337" in ACADEMIC_REFERENCE_TEXT
    assert "DISS-WOJTAN-2004-EPFL-TH2978" in ACADEMIC_REFERENCE_TEXT
    assert "friedel_th3337_candidate_pressure_gradient_pa_per_m" in ACADEMIC_REFERENCE_TEXT
    assert "wojtan_th2978_candidate_dryout_limits" in ACADEMIC_REFERENCE_TEXT
    assert "moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m" in ACADEMIC_REFERENCE_TEXT
    assert "moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m" in ACADEMIC_REFERENCE_TEXT
    assert "moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m" in (
        ACADEMIC_REFERENCE_TEXT
    )
    assert "moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m" in (
        ACADEMIC_REFERENCE_TEXT
    )
    assert "moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m" in (
        ACADEMIC_REFERENCE_TEXT
    )
    assert "muller_steinhagen_heck_th3337_candidate_pressure_gradient_pa_per_m" in README_TEXT


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
