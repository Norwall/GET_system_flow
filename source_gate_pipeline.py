from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MANIFEST_PATH = Path("docs") / "source_gate_manifest.json"
PRIMARY_SOURCE_INVENTORY_PATH = Path("docs") / "primary_source_inventory.md"


@dataclass(frozen=True)
class PrimarySourceInventoryRow:
    local_file: str
    sha256: str
    citation_or_model: str
    audited_pages_equations: str
    decision: str
    notes: str

    @property
    def has_local_file(self) -> bool:
        return bool(self.local_file and self.local_file != "_none_")


@dataclass(frozen=True)
class SourceGatePipelineItem:
    source_id: str
    model: str
    target_code: str
    decision: str
    evidence_status: str
    local_full_text_ref: str
    inventory_decision: str
    local_file_exists: bool
    local_sha256_status: str
    release_state: str
    next_action: str
    acquisition_hint: str
    audit_documents: tuple[str, ...]
    primary_record_urls: tuple[str, ...]
    required_audit_checks: tuple[str, ...]
    required_tests_before_release: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    action_pipeline: tuple[dict[str, str], ...]
    current_blocking_stage: str
    release_criteria: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "model": self.model,
            "target_code": self.target_code,
            "decision": self.decision,
            "evidence_status": self.evidence_status,
            "local_full_text_ref": self.local_full_text_ref,
            "inventory_decision": self.inventory_decision,
            "local_file_exists": self.local_file_exists,
            "local_sha256_status": self.local_sha256_status,
            "release_state": self.release_state,
            "next_action": self.next_action,
            "acquisition_hint": self.acquisition_hint,
            "audit_documents": list(self.audit_documents),
            "primary_record_urls": list(self.primary_record_urls),
            "required_audit_checks": list(self.required_audit_checks),
            "required_tests_before_release": list(self.required_tests_before_release),
            "blocking_reasons": list(self.blocking_reasons),
            "action_pipeline": [dict(action) for action in self.action_pipeline],
            "current_blocking_stage": self.current_blocking_stage,
            "release_criteria": [dict(criterion) for criterion in self.release_criteria],
        }


def load_manifest(project_root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((project_root / MANIFEST_PATH).read_text(encoding="utf-8"))


def load_primary_source_inventory(project_root: Path = Path(".")) -> tuple[PrimarySourceInventoryRow, ...]:
    path = project_root / PRIMARY_SOURCE_INVENTORY_PATH
    if not path.exists():
        return ()
    return tuple(_parse_inventory_rows(path.read_text(encoding="utf-8")))


def build_source_gate_pipeline(project_root: Path = Path(".")) -> tuple[SourceGatePipelineItem, ...]:
    manifest = load_manifest(project_root)
    inventory_rows = load_primary_source_inventory(project_root)
    return tuple(
        _pipeline_item_for_entry(project_root, entry, inventory_rows)
        for entry in manifest.get("entries", [])
    )


def source_gate_pipeline_as_dicts(project_root: Path = Path(".")) -> list[dict[str, Any]]:
    return [item.to_dict() for item in build_source_gate_pipeline(project_root)]


def source_gate_report(project_root: Path = Path(".")) -> dict[str, Any]:
    manifest = load_manifest(project_root)
    items = build_source_gate_pipeline(project_root)
    return {
        "summary": source_gate_summary(items),
        "policy_documents": _policy_documents(manifest),
        "source_gates": [item.to_dict() for item in items],
        "milestone_groups": _milestone_groups(items),
        "action_pipeline": _action_pipeline_summary(items),
        "next_priorities": _next_priorities(items),
    }


def source_gate_summary(items: Iterable[SourceGatePipelineItem]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for item in items:
        summary[item.release_state] = summary.get(item.release_state, 0) + 1
    return summary


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _pipeline_item_for_entry(
    project_root: Path,
    entry: dict[str, Any],
    inventory_rows: tuple[PrimarySourceInventoryRow, ...],
) -> SourceGatePipelineItem:
    source_id = str(entry.get("registry_id") or entry.get("candidate_id") or "")
    inventory_row = _matching_inventory_row(entry, inventory_rows)
    local_ref = str(entry.get("local_full_text_ref", ""))
    local_file = _local_file_from_ref(local_ref)
    if local_file is None and inventory_row is not None and inventory_row.has_local_file:
        local_file = inventory_row.local_file

    local_file_exists = False
    sha_status = "not_applicable"
    if local_file:
        local_path = project_root / local_file
        local_file_exists = local_path.exists()
        sha_status = _sha_status(local_path, inventory_row.sha256 if inventory_row is not None else "")

    release_state, next_action = _release_state_and_next_action(
        entry=entry,
        inventory_row=inventory_row,
        local_file=local_file,
        local_file_exists=local_file_exists,
        sha_status=sha_status,
    )

    action_pipeline = _action_pipeline_for_state(
        entry=entry,
        release_state=release_state,
        local_file=local_file,
        local_file_exists=local_file_exists,
        sha_status=sha_status,
        inventory_row=inventory_row,
    )

    return SourceGatePipelineItem(
        source_id=source_id,
        model=str(entry.get("model", "")),
        target_code=str(entry.get("target_code", "")),
        decision=str(entry.get("decision", "")),
        evidence_status=str(entry.get("evidence_status", "")),
        local_full_text_ref=local_ref,
        inventory_decision=inventory_row.decision if inventory_row is not None else "",
        local_file_exists=local_file_exists,
        local_sha256_status=sha_status,
        release_state=release_state,
        next_action=next_action,
        acquisition_hint=_acquisition_hint(entry),
        audit_documents=_audit_documents(entry),
        primary_record_urls=_primary_record_urls(entry),
        required_audit_checks=tuple(str(item) for item in entry.get("required_audit_checks", ())),
        required_tests_before_release=tuple(str(item) for item in entry.get("required_tests_before_release", ())),
        blocking_reasons=tuple(str(reason) for reason in entry.get("blocking_reasons", ())),
        action_pipeline=action_pipeline,
        current_blocking_stage=_current_blocking_stage(action_pipeline),
        release_criteria=_release_criteria(action_pipeline),
    )


def _release_state_and_next_action(
    *,
    entry: dict[str, Any],
    inventory_row: PrimarySourceInventoryRow | None,
    local_file: str | None,
    local_file_exists: bool,
    sha_status: str,
) -> tuple[str, str]:
    decision = str(entry.get("decision", ""))
    evidence_status = str(entry.get("evidence_status", ""))
    has_secondary = "secondary_formula_candidate" in entry
    has_dissertation_candidate = bool(entry.get("dissertation_candidates"))

    if decision == "released":
        if evidence_status != "audited":
            return "blocked_released_without_audited_evidence", "Set evidence_status='audited' only after source audit."
        if not local_file:
            return "blocked_released_without_local_source_ref", "Point local_full_text_ref to sources/primary/..."
        if not local_file_exists:
            return "blocked_released_local_source_missing", "Restore the audited local source file before release."
        if sha_status != "matches_inventory":
            return "blocked_released_sha256_mismatch", "Update or fix docs/primary_source_inventory.md SHA256."
        return "released_source_complete", "Keep registry, manifest, inventory and reference tests in sync."

    if decision == "source_candidate":
        if inventory_row is not None and inventory_row.decision == "candidate_only":
            if local_file_exists and sha_status == "matches_inventory":
                return "candidate_local_intake_ready", "Audit equations, limits and reference points before runtime release."
            return "candidate_inventory_recorded_local_file_missing", "Restore local candidate file for audit continuation."
        if evidence_status == "full_text_available":
            return "candidate_external_full_text_available", "Copy the full text into sources/primary and record SHA256."
        return "candidate_needs_full_text", "Obtain full primary source before formula transcription."

    if decision == "source_required":
        if has_secondary:
            return (
                "blocked_primary_source_required_secondary_available",
                "Use secondary formula only as audit guidance; obtain the full primary source.",
            )
        if has_dissertation_candidate:
            return (
                "blocked_primary_source_required_dissertation_candidate_available",
                "Use dissertation pages as audit guidance; obtain the target primary article or approve a dissertation-specific release path.",
            )
        return "blocked_primary_source_required", "Obtain full primary source and add inventory record."

    return "unknown_decision", "Normalize decision to source_required, source_candidate, or released."


def _parse_inventory_rows(text: str) -> Iterable[PrimarySourceInventoryRow]:
    in_table = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("| Local file |"):
            in_table = True
            continue
        if not in_table or not line.startswith("|"):
            continue
        if set(line.replace("|", "").strip()) <= {"-", " "}:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        yield PrimarySourceInventoryRow(
            local_file=_strip_markdown_code(cells[0]),
            sha256=_strip_markdown_code(cells[1]).upper(),
            citation_or_model=_strip_markdown_code(cells[2]),
            audited_pages_equations=_strip_markdown_code(cells[3]),
            decision=_strip_markdown_code(cells[4]),
            notes=_strip_markdown_code(cells[5]),
        )


def _matching_inventory_row(
    entry: dict[str, Any],
    inventory_rows: tuple[PrimarySourceInventoryRow, ...],
) -> PrimarySourceInventoryRow | None:
    candidates = [
        str(entry.get("registry_id") or ""),
        str(entry.get("candidate_id") or ""),
        str(entry.get("model") or ""),
        str(entry.get("primary_citation") or ""),
    ]
    for row in inventory_rows:
        haystack = " ".join((row.local_file, row.citation_or_model, row.notes)).lower()
        if any(candidate and candidate.lower() in haystack for candidate in candidates):
            return row
    return None


def _local_file_from_ref(ref: str) -> str | None:
    normalized = ref.replace("\\", "/")
    if normalized.startswith("sources/primary/"):
        return normalized
    return None


def _sha_status(path: Path, expected_sha256: str) -> str:
    if not expected_sha256 or expected_sha256 == "_NONE_":
        return "missing_inventory_sha256"
    if not path.exists():
        return "local_file_missing"
    actual = sha256_file(path)
    return "matches_inventory" if actual == expected_sha256.upper() else "mismatch"


def _strip_markdown_code(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == "`" and text[-1] == "`":
        return text[1:-1]
    return text


def _primary_record_urls(entry: dict[str, Any]) -> tuple[str, ...]:
    urls: list[str] = []
    primary_record = entry.get("primary_record", {})
    if isinstance(primary_record, dict):
        for value in primary_record.values():
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                urls.append(value)
    secondary = entry.get("secondary_formula_candidate", {})
    if isinstance(secondary, dict):
        value = secondary.get("secondary_source_url")
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            urls.append(value)
    dissertation_candidates = entry.get("dissertation_candidates", ())
    if isinstance(dissertation_candidates, list):
        for candidate in dissertation_candidates:
            if not isinstance(candidate, dict):
                continue
            for key in ("repository_record", "bitstream_content"):
                value = candidate.get(key)
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    urls.append(value)
    return tuple(dict.fromkeys(urls))


def _audit_documents(entry: dict[str, Any]) -> tuple[str, ...]:
    documents: list[str] = []
    candidate_audit = entry.get("source_candidate_audit_document")
    if isinstance(candidate_audit, str) and candidate_audit:
        documents.append(candidate_audit)
    for candidate in entry.get("dissertation_candidates", ()):
        if not isinstance(candidate, dict):
            continue
        audit_note = candidate.get("audit_note")
        if not isinstance(audit_note, str):
            continue
        for part in audit_note.replace(";", " ").split():
            if part.startswith("docs/") and part.endswith(".md"):
                documents.append(part.rstrip(".,"))
    return tuple(dict.fromkeys(documents))


def _acquisition_hint(entry: dict[str, Any]) -> str:
    source_id = str(entry.get("registry_id") or entry.get("candidate_id") or "")
    primary_record = entry.get("primary_record", {})
    if source_id == "TP-FRIEDEL-1979-SOURCE-GATE":
        return (
            "Search archival holdings for Friedel, 3R International 18(7), 485, 1979; "
            "MSH 1986 Crossref references this article title and venue. Use fluids docs only as secondary guidance."
        )
    if source_id == "HTC-CHEN-1962-SOURCE-CANDIDATE":
        return (
            "Local OSTI PDF is present; next work is equation/table/figure audit, digitizing graphical F/S functions, "
            "and reference HTC tests before runtime release."
        )
    if isinstance(primary_record, dict):
        endpoint = (
            primary_record.get("publisher_full_text_endpoint")
            or primary_record.get("repository_record")
            or primary_record.get("publisher_resource")
            or primary_record.get("doi")
        )
        if endpoint:
            return f"Obtain authorized full text from {endpoint}; then place the PDF/scan under sources/primary and record SHA256."
    return "Obtain full primary source, record SHA256, audited pages/equations, formula registry entries and reference tests."


def _action_pipeline_for_state(
    *,
    entry: dict[str, Any],
    release_state: str,
    local_file: str | None,
    local_file_exists: bool,
    sha_status: str,
    inventory_row: PrimarySourceInventoryRow | None,
) -> tuple[dict[str, str], ...]:
    source_id = str(entry.get("registry_id") or entry.get("candidate_id") or "")
    decision = str(entry.get("decision", ""))
    primary_urls = _primary_record_urls(entry)
    has_primary_record = bool(primary_urls or entry.get("primary_citation"))
    has_local_source = bool(local_file and local_file_exists and sha_status == "matches_inventory")
    has_inventory = inventory_row is not None
    is_released = release_state == "released_source_complete"
    is_candidate_ready = release_state == "candidate_local_intake_ready"
    source_blocked = decision == "source_required" and not has_local_source

    identify_status = "done" if has_primary_record else "blocked"
    obtain_status = "done" if has_local_source else ("blocked" if source_blocked else "pending")
    intake_status = "done" if has_local_source and has_inventory else ("blocked" if source_blocked else "pending")
    audit_status = "done" if is_released else ("in_progress" if is_candidate_ready else "blocked")
    implementation_status = "done" if is_released else "blocked"
    test_status = "done" if is_released else "blocked"
    release_status = "done" if is_released else "blocked"

    downstream_blocker = _downstream_blocker_text(
        release_state=release_state,
        source_id=source_id,
        has_local_source=has_local_source,
    )

    return (
        {
            "stage": "identify_primary_record",
            "status": identify_status,
            "action": "Maintain DOI/publisher/repository metadata and acquisition route.",
            "evidence": "primary_record/primary_citation present" if has_primary_record else "no primary record route",
        },
        {
            "stage": "obtain_full_text",
            "status": obtain_status,
            "action": "Acquire authorized full primary text under sources/primary.",
            "evidence": local_file or "no local full text",
        },
        {
            "stage": "local_intake",
            "status": intake_status,
            "action": "Record local path, SHA256, citation, audited pages/equations and decision.",
            "evidence": (
                f"inventory={inventory_row.decision}; sha={sha_status}"
                if inventory_row is not None
                else f"inventory missing; sha={sha_status}"
            ),
        },
        {
            "stage": "audit_formulas_and_limits",
            "status": audit_status,
            "action": "Transcribe formulas, variable definitions, applicability limits and unresolved ambiguities.",
            "evidence": "audit started from local candidate" if is_candidate_ready else downstream_blocker,
        },
        {
            "stage": "implement_runtime_adapter",
            "status": implementation_status,
            "action": "Implement only after audited formulas and applicability are recorded in docs/formula_registry.md.",
            "evidence": "released source complete" if is_released else downstream_blocker,
        },
        {
            "stage": "add_reference_tests",
            "status": test_status,
            "action": "Add reference-point, convention, domain and guard-removal tests.",
            "evidence": "released source complete" if is_released else downstream_blocker,
        },
        {
            "stage": "release_source_gate",
            "status": release_status,
            "action": "Change decision to released only after audit, implementation and tests pass.",
            "evidence": release_state,
        },
    )


def _current_blocking_stage(action_pipeline: tuple[dict[str, str], ...]) -> str:
    for action in action_pipeline:
        if action.get("status") != "done":
            return str(action.get("stage", ""))
    return ""


def _release_criteria(action_pipeline: tuple[dict[str, str], ...]) -> tuple[dict[str, str], ...]:
    actions_by_stage = {action["stage"]: action for action in action_pipeline}
    definitions = (
        (
            "primary_text_intake",
            "obtain_full_text",
            "Authorized full primary text or scan is present under sources/primary.",
        ),
        (
            "sha256_inventory",
            "local_intake",
            "docs/primary_source_inventory.md records local path, SHA256, citation, audited pages/equations and decision.",
        ),
        (
            "formula_scope_audit",
            "audit_formulas_and_limits",
            "docs/formula_registry.md and docs/source_gate_unresolved_questions.md record equations, definitions, limits and closed questions.",
        ),
        (
            "runtime_adapter",
            "implement_runtime_adapter",
            "Runtime implementation is wired only after the audited formula and applicability scope are recorded.",
        ),
        (
            "reference_tests",
            "add_reference_tests",
            "Source-based numerical, convention, domain and guard-removal tests are implemented and passing.",
        ),
        (
            "manifest_release",
            "release_source_gate",
            "docs/source_gate_manifest.json uses decision='released' and evidence_status='audited' only after all proof exists.",
        ),
    )
    criteria: list[dict[str, str]] = []
    for criterion_id, stage, required_proof in definitions:
        action = actions_by_stage[stage]
        criteria.append(
            {
                "criterion_id": criterion_id,
                "stage": stage,
                "status": action["status"],
                "required_proof": required_proof,
                "evidence": action["evidence"],
            }
        )
    return tuple(criteria)


def _downstream_blocker_text(
    *,
    release_state: str,
    source_id: str,
    has_local_source: bool,
) -> str:
    if release_state == "candidate_local_intake_ready":
        return "local source is available; formula audit and reference tests are not complete"
    if has_local_source:
        return "local source exists but release evidence is incomplete"
    if source_id == "TP-FRIEDEL-1979-SOURCE-GATE":
        return "archival primary paper/scan is still missing"
    if release_state == "blocked_primary_source_required_dissertation_candidate_available":
        return "local dissertation candidate exists, but target primary article release evidence is still missing"
    return "full primary source is still missing"


def _action_pipeline_summary(items: Iterable[SourceGatePipelineItem]) -> list[dict[str, Any]]:
    return [
        {
            "source_id": item.source_id,
            "release_state": item.release_state,
            "actions": [dict(action) for action in item.action_pipeline],
        }
        for item in items
    ]


def _policy_documents(manifest: dict[str, Any]) -> list[str]:
    policy = manifest.get("policy", {})
    documents: list[str] = []
    for key in (
        "audit_document",
        "checkpoint_audit_document",
        "local_source_inventory_document",
        "milestone_closure_pipeline_document",
        "unresolved_questions_document",
        "secondary_formula_candidate_document",
    ):
        value = policy.get(key)
        if isinstance(value, str) and value:
            documents.append(value)
    previous_documents = policy.get("previous_audit_documents", ())
    if isinstance(previous_documents, list):
        documents.extend(str(value) for value in previous_documents if value)
    return list(dict.fromkeys(documents))


def _milestone_groups(items: Iterable[SourceGatePipelineItem]) -> list[dict[str, Any]]:
    buckets: dict[str, list[SourceGatePipelineItem]] = {
        "local_candidate_audit": [],
        "secondary_guided_primary_required": [],
        "dissertation_guided_primary_required": [],
        "primary_acquisition_required": [],
        "released": [],
    }
    for item in items:
        if item.release_state == "candidate_local_intake_ready":
            buckets["local_candidate_audit"].append(item)
        elif item.release_state == "blocked_primary_source_required_secondary_available":
            buckets["secondary_guided_primary_required"].append(item)
        elif item.release_state == "blocked_primary_source_required_dissertation_candidate_available":
            buckets["dissertation_guided_primary_required"].append(item)
        elif item.release_state == "released_source_complete":
            buckets["released"].append(item)
        else:
            buckets["primary_acquisition_required"].append(item)

    definitions = (
        (
            "local_candidate_audit",
            "Local full text is available, but runtime release still needs formula audit, SI mapping and reference tests.",
            "Complete page/equation audit, digitize graphical data if present, add reference calculations, then update registry and guards.",
            "audited equations, applicability limits, SI mapping, reference tests and released manifest decision",
        ),
        (
            "secondary_guided_primary_required",
            "Secondary or review formula guidance exists, but primary-source release evidence is still missing.",
            "Use secondary formulas only to plan the audit; acquire the full primary text or archival scan before implementation.",
            "local primary full text, SHA256 inventory, convention audit and reference tests",
        ),
        (
            "dissertation_guided_primary_required",
            "A local dissertation candidate exists, but the target journal gate or release path is not complete.",
            "Use dissertation pages as audit guidance; obtain the target article or record a dissertation-specific release decision.",
            "explicit release decision, page/equation audit, applicability limits and reference tests",
        ),
        (
            "primary_acquisition_required",
            "No sufficient local full text has been recorded.",
            "Acquire authorized primary text, place it under sources/primary and record SHA256 before formula transcription.",
            "local primary full text and inventory row",
        ),
        (
            "released",
            "Released sources with complete audit evidence.",
            "Keep docs, manifest and tests synchronized.",
            "all release requirements satisfied",
        ),
    )
    groups: list[dict[str, Any]] = []
    for group_id, title, next_action, required_proof in definitions:
        group_items = sorted(buckets[group_id], key=lambda item: item.source_id)
        if not group_items and group_id != "released":
            continue
        groups.append(
            {
                "group_id": group_id,
                "title": title,
                "count": len(group_items),
                "source_ids": [item.source_id for item in group_items],
                "next_action": next_action,
                "required_proof": required_proof,
                "audit_documents": sorted(
                    {
                        audit_document
                        for item in group_items
                        for audit_document in item.audit_documents
                    }
                ),
            }
        )
    return groups


def _next_priorities(items: Iterable[SourceGatePipelineItem]) -> list[dict[str, Any]]:
    priority_order = {
        "candidate_local_intake_ready": 0,
        "candidate_external_full_text_available": 1,
        "blocked_primary_source_required_secondary_available": 2,
        "blocked_primary_source_required_dissertation_candidate_available": 3,
        "blocked_primary_source_required": 4,
    }
    ordered = sorted(
        items,
        key=lambda item: (
            priority_order.get(item.release_state, 99),
            item.source_id,
        ),
    )
    return [
        {
            "source_id": item.source_id,
            "release_state": item.release_state,
            "next_action": item.next_action,
            "acquisition_hint": item.acquisition_hint,
            "audit_documents": list(item.audit_documents),
        }
        for item in ordered
        if item.release_state != "released_source_complete"
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report source-gate release pipeline status.")
    parser.add_argument("--project-root", default=".", help="Project root containing docs/source_gate_manifest.json")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    data = source_gate_report(Path(args.project_root))
    print(json.dumps(data, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
