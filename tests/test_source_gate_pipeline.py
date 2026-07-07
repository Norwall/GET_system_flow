from __future__ import annotations

import json
from pathlib import Path

from source_gate_pipeline import build_source_gate_pipeline, sha256_file, source_gate_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_reports_current_source_gate_states() -> None:
    items = {item.source_id: item for item in build_source_gate_pipeline(PROJECT_ROOT)}

    msh = items["TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE"]
    assert msh.release_state == "blocked_primary_source_required_secondary_available"
    assert "primary source" in msh.next_action
    assert msh.primary_record_urls
    assert msh.required_audit_checks
    assert msh.required_tests_before_release
    assert msh.action_pipeline[0]["stage"] == "identify_primary_record"
    assert msh.action_pipeline[1]["stage"] == "obtain_full_text"
    assert msh.action_pipeline[1]["status"] == "blocked"
    assert msh.action_pipeline[-1]["stage"] == "release_source_gate"
    assert msh.action_pipeline[-1]["status"] == "blocked"
    assert msh.current_blocking_stage == "obtain_full_text"
    msh_criteria = {criterion["criterion_id"]: criterion for criterion in msh.release_criteria}
    assert msh_criteria["primary_text_intake"]["status"] == "blocked"
    assert msh_criteria["manifest_release"]["status"] == "blocked"

    wojtan = items["REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE"]
    assert wojtan.release_state == "blocked_primary_source_required_dissertation_candidate_available"
    assert "dissertation pages" in wojtan.next_action
    assert wojtan.inventory_decision == ""
    assert "docs/dissertation_formula_audit_2026-07-06.md" in wojtan.audit_documents
    assert any("285f44f3-559e-4d9d-ada4-233895ecd47e" in url for url in wojtan.primary_record_urls)

    chen = items["HTC-CHEN-1962-SOURCE-CANDIDATE"]
    assert chen.decision == "source_candidate"
    assert chen.inventory_decision == "candidate_only"
    assert chen.release_state.startswith("candidate_")
    assert chen.local_sha256_status in {"matches_inventory", "local_file_missing"}
    assert chen.audit_documents == ("docs/chen_1962_formula_audit_2026-07-06.md",)
    assert "digitizing graphical F/S" in chen.acquisition_hint
    chen_actions = {action["stage"]: action for action in chen.action_pipeline}
    assert chen_actions["obtain_full_text"]["status"] == "done"
    assert chen_actions["local_intake"]["status"] == "done"
    assert chen_actions["audit_formulas_and_limits"]["status"] == "in_progress"
    assert chen_actions["implement_runtime_adapter"]["status"] == "blocked"
    assert chen.current_blocking_stage == "audit_formulas_and_limits"
    chen_criteria = {criterion["criterion_id"]: criterion for criterion in chen.release_criteria}
    assert chen_criteria["primary_text_intake"]["status"] == "done"
    assert chen_criteria["sha256_inventory"]["status"] == "done"
    assert chen_criteria["formula_scope_audit"]["status"] == "in_progress"
    assert chen_criteria["reference_tests"]["status"] == "blocked"
    assert "docs/source_gate_unresolved_questions.md" in chen_criteria["formula_scope_audit"]["required_proof"]


def test_pipeline_report_prioritizes_local_candidate_before_closed_gates() -> None:
    report = source_gate_report(PROJECT_ROOT)
    priorities = report["next_priorities"]

    assert report["summary"]["candidate_local_intake_ready"] == 1
    assert "docs/source_gate_unresolved_questions.md" in report["policy_documents"]
    assert report["action_pipeline"]
    assert priorities[0]["source_id"] == "HTC-CHEN-1962-SOURCE-CANDIDATE"
    assert priorities[0]["release_state"] == "candidate_local_intake_ready"
    assert priorities[0]["audit_documents"] == ["docs/chen_1962_formula_audit_2026-07-06.md"]
    first_pipeline = report["action_pipeline"][0]
    assert {"source_id", "release_state", "actions"} <= set(first_pipeline)
    assert {action["stage"] for action in first_pipeline["actions"]} == {
        "identify_primary_record",
        "obtain_full_text",
        "local_intake",
        "audit_formulas_and_limits",
        "implement_runtime_adapter",
        "add_reference_tests",
        "release_source_gate",
    }


def test_pipeline_report_groups_open_milestones_by_release_path() -> None:
    report = source_gate_report(PROJECT_ROOT)
    groups = {group["group_id"]: group for group in report["milestone_groups"]}

    assert groups["local_candidate_audit"]["source_ids"] == [
        "HTC-CHEN-1962-SOURCE-CANDIDATE"
    ]
    assert groups["local_candidate_audit"]["audit_documents"] == [
        "docs/chen_1962_formula_audit_2026-07-06.md"
    ]
    assert set(groups["secondary_guided_primary_required"]["source_ids"]) == {
        "TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE",
        "TP-FRIEDEL-1979-SOURCE-GATE",
        "REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE",
    }
    assert set(groups["dissertation_guided_primary_required"]["source_ids"]) == {
        "REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE",
        "HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE",
    }
    assert groups["dissertation_guided_primary_required"]["audit_documents"] == [
        "docs/dissertation_formula_audit_2026-07-06.md"
    ]
    assert set(groups["primary_acquisition_required"]["source_ids"]) == {
        "VOID-ZUBER-FINDLAY-1965-SOURCE-GATE",
        "HTC-KANDLIKAR-1990-SOURCE-CANDIDATE",
        "HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE",
    }
    assert groups["released"]["count"] == 0

    grouped_source_ids = [
        source_id
        for group in report["milestone_groups"]
        for source_id in group["source_ids"]
    ]
    reported_source_ids = {item["source_id"] for item in report["source_gates"]}
    assert len(grouped_source_ids) == len(set(grouped_source_ids))
    assert set(grouped_source_ids) == reported_source_ids


def test_released_pipeline_requires_audited_local_source_with_matching_sha(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    primary = tmp_path / "sources" / "primary"
    docs.mkdir()
    primary.mkdir(parents=True)
    source_file = primary / "audited.pdf"
    source_file.write_bytes(b"audited source")
    source_hash = sha256_file(source_file)

    manifest = {
        "entries": [
            {
                "registry_id": "TEST-RELEASED-SOURCE",
                "candidate_id": None,
                "model": "Synthetic released source",
                "target_code": "synthetic.model",
                "primary_citation": "Synthetic citation",
                "primary_record": {},
                "evidence_status": "audited",
                "access_evidence": {},
                "local_full_text_ref": "sources/primary/audited.pdf",
                "decision": "released",
                "blocking_reasons": ["none"],
                "required_audit_checks": ["docs/formula_registry.md updated"],
                "required_tests_before_release": ["reference test"],
            }
        ]
    }
    (docs / "source_gate_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (docs / "primary_source_inventory.md").write_text(
        "\n".join(
            [
                "| Local file | SHA256 | Citation / model | Audited pages/equations | Decision | Notes |",
                "| --- | --- | --- | --- | --- | --- |",
                (
                    "| `sources/primary/audited.pdf` | "
                    f"`{source_hash}` | `TEST-RELEASED-SOURCE` | p. 1 eq. 1 | "
                    "`audited_release` | released |"
                ),
            ]
        ),
        encoding="utf-8",
    )

    (item,) = build_source_gate_pipeline(tmp_path)

    assert item.release_state == "released_source_complete"
    assert item.local_file_exists is True
    assert item.local_sha256_status == "matches_inventory"
    assert {action["status"] for action in item.action_pipeline} == {"done"}
