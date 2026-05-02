from __future__ import annotations

import re
from typing import Any

from .manuscript import block_plain_text, parse_markdown_blocks
from .references import build_citation_order, cited_source_ids, extract_citation_ids_from_text, source_index
from .word_count import count_words, manuscript_word_report, under_over_diagnostics, validate_target_policy


MARKDOWN_ARTIFACT_PATTERNS = [
    (re.compile(r"\[TODO:[^\]]+\]", re.IGNORECASE), "Unresolved evidence placeholder"),
    (re.compile(r"```"), "Fenced code block marker"),
    (re.compile(r"`[^`]+`"), "Inline code marker"),
    (re.compile(r"\bTODO\b"), "TODO marker"),
]
FIGURE_TOKEN_RE = re.compile(r"\[\[FIGURE:([^\]]+)\]\]")
TABLE_TOKEN_RE = re.compile(r"\[\[TABLE:([^\]]+)\]\]")
COVERAGE_KINDS = {"claim", "background", "transition", "method_note", "uncited_ok"}
COVERAGE_STATUSES = {"suggested", "confirmed"}
MIN_ARGUMENT_WORDS = 12
METHOD_NOTE_HINTS = (
    "method",
    "methods",
    "procedure",
    "protocol",
    "pipeline",
    "workflow",
    "data collection",
    "dataset",
    "experiment",
    "our approach",
    "we use",
    "we used",
    "we collected",
    "we measured",
    "we implemented",
)
TRANSITION_HINTS = (
    "however",
    "therefore",
    "thus",
    "overall",
    "together",
    "in summary",
    "finally",
    "for example",
    "for instance",
    "in contrast",
    "by contrast",
)


def artifact_findings(
    manuscript_state: dict[str, Any],
    evidence_state: dict[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    figure_ids = {figure.get("id", "") for figure in evidence_state.get("figures", [])}
    table_ids = {table.get("id", "") for table in evidence_state.get("tables", [])}

    def scan_text(location: str, text: str) -> None:
        for pattern, label in MARKDOWN_ARTIFACT_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "location": location,
                        "kind": "artifact",
                        "label": label,
                        "snippet": match.group(0),
                    }
                )
        for match in FIGURE_TOKEN_RE.finditer(text):
            figure_id = match.group(1)
            if figure_id not in figure_ids:
                findings.append(
                    {
                        "location": location,
                        "kind": "artifact",
                        "label": "Unresolved figure marker",
                        "snippet": match.group(0),
                    }
                )
        for match in TABLE_TOKEN_RE.finditer(text):
            table_id = match.group(1)
            if table_id not in table_ids:
                findings.append(
                    {
                        "location": location,
                        "kind": "artifact",
                        "label": "Unresolved table marker",
                        "snippet": match.group(0),
                    }
                )

    def walk_sections(sections: list[dict[str, Any]]) -> None:
        for section in sections:
            scan_text(section["id"], section.get("content", ""))
            walk_sections(section.get("subsections", []))

    scan_text("abstract", manuscript_state.get("abstract", ""))
    walk_sections(manuscript_state.get("sections", []))
    walk_sections(manuscript_state.get("appendices", []))

    return findings


def reference_findings(
    project_state: dict[str, Any],
    manuscript_state: dict[str, Any],
    sources_state: dict[str, Any],
    evidence_state: dict[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    sources_by_id = source_index(sources_state)
    cited_ids = cited_source_ids(manuscript_state, evidence_state)

    for source_id in cited_ids:
        if source_id not in sources_by_id:
            findings.append(
                {
                    "kind": "reference",
                    "location": source_id,
                    "label": "Citation references a missing source record",
                    "snippet": source_id,
                }
            )

    for source in sources_state.get("sources", []):
        if source.get("id") in cited_ids and not source.get("verified", False):
            findings.append(
                {
                    "kind": "reference",
                    "location": source["id"],
                    "label": "Cited source is not verified",
                    "snippet": source.get("title", source["id"]),
                }
            )

    claims = evidence_state.get("claims", [])
    if manuscript_state.get("sections") and not claims:
        findings.append(
            {
                "kind": "evidence",
                "location": "evidence",
                "label": "No claims are linked to evidence",
                "snippet": "",
            }
        )

    for claim in claims:
        if not claim.get("source_ids"):
            findings.append(
                {
                    "kind": "evidence",
                    "location": claim.get("id", "claim"),
                    "label": "Claim has no supporting source IDs",
                    "snippet": claim.get("claim_text", ""),
                }
            )
    return findings


def _prose_block_records(manuscript_state: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    def append_records(scope: str, location: str, text: str) -> None:
        prose_index = 0
        for block in parse_markdown_blocks(text):
            if block["kind"] not in {"paragraph", "bullet_list", "ordered_list"}:
                continue
            block_text = block_plain_text(block).strip()
            if not block_text:
                continue
            records.append(
                {
                    "block_id": f"{location}#block-{prose_index}",
                    "location": location,
                    "scope": scope,
                    "kind": block["kind"],
                    "text": block_text,
                    "word_count": count_words(block_text),
                    "has_inline_citation": bool(extract_citation_ids_from_text(block_text)),
                }
            )
            prose_index += 1

    def walk_sections(scope: str, sections: list[dict[str, Any]], path: list[str] | None = None) -> None:
        path = path or []
        for section in sections:
            section_path = path + [section["id"]]
            location = "/".join(section_path)
            append_records(scope, location, section.get("content", ""))
            walk_sections(scope, section.get("subsections", []), section_path)

    append_records("abstract", "abstract", manuscript_state.get("abstract", ""))
    walk_sections("section", manuscript_state.get("sections", []))
    walk_sections("appendix", manuscript_state.get("appendices", []))
    return records


def _coverage_status(record: dict[str, Any]) -> str:
    status = str(record.get("status", "confirmed")).strip().lower()
    return status or "confirmed"


def _block_needs_review(
    block: dict[str, Any],
    records: list[dict[str, Any]],
) -> bool:
    return (
        block["word_count"] >= MIN_ARGUMENT_WORDS
        or block["has_inline_citation"]
        or bool(records)
    )


def _coverage_record_satisfies(
    record: dict[str, Any],
    block: dict[str, Any],
) -> bool:
    kind = str(record.get("kind", "")).strip()
    note = str(record.get("note", "")).strip()
    claim_ids = record.get("claim_ids", [])
    source_ids = record.get("source_ids", [])

    if kind == "claim":
        return bool(claim_ids)
    if kind == "background":
        return bool(claim_ids or source_ids)
    if kind == "transition":
        return block["word_count"] < MIN_ARGUMENT_WORDS * 2 or bool(note)
    if kind == "method_note":
        return bool(claim_ids or source_ids or note)
    if kind == "uncited_ok":
        return bool(note)
    return False


def _suggested_coverage_record(block: dict[str, Any]) -> dict[str, Any]:
    text = block["text"].lower()
    if block["has_inline_citation"]:
        kind = "background"
        note = (
            "Suggested by `spw scaffold-coverage`: inline citation detected; "
            "confirm as background and add the relevant claim or source links."
        )
    elif any(hint in text for hint in METHOD_NOTE_HINTS):
        kind = "method_note"
        note = (
            "Suggested by `spw scaffold-coverage`: method/process language detected; "
            "confirm if this block documents workflow or procedure."
        )
    elif block["word_count"] < MIN_ARGUMENT_WORDS * 2 and any(
        hint in text for hint in TRANSITION_HINTS
    ):
        kind = "transition"
        note = (
            "Suggested by `spw scaffold-coverage`: short connective prose detected; "
            "confirm if this block mainly bridges surrounding sections."
        )
    else:
        kind = "claim"
        note = (
            "Suggested by `spw scaffold-coverage`: uncited argumentative prose detected; "
            "confirm and add supporting claim or source links."
        )

    return {
        "block_id": block["block_id"],
        "status": "suggested",
        "kind": kind,
        "claim_ids": [],
        "source_ids": [],
        "note": note,
    }


def scaffold_coverage_records(
    manuscript_state: dict[str, Any],
    evidence_state: dict[str, Any],
) -> dict[str, Any]:
    existing_records = list(evidence_state.get("coverage", []))
    records_by_block: dict[str, list[dict[str, Any]]] = {}
    for record in existing_records:
        block_id = str(record.get("block_id", "")).strip()
        if block_id:
            records_by_block.setdefault(block_id, []).append(record)

    created_records: list[dict[str, Any]] = []
    reviewable_blocks = 0
    existing_blocks = 0

    for block in _prose_block_records(manuscript_state):
        block_records = records_by_block.get(block["block_id"], [])
        if not _block_needs_review(block, block_records):
            continue

        reviewable_blocks += 1
        if block_records:
            existing_blocks += 1
            continue

        suggested_record = _suggested_coverage_record(block)
        created_records.append(suggested_record)
        records_by_block[block["block_id"]] = [suggested_record]

    return {
        "reviewable_blocks": reviewable_blocks,
        "existing_blocks": existing_blocks,
        "created_count": len(created_records),
        "created_records": created_records,
        "coverage_records": existing_records + created_records,
    }


def manuscript_coverage_report(
    manuscript_state: dict[str, Any],
    sources_state: dict[str, Any],
    evidence_state: dict[str, Any],
) -> dict[str, Any]:
    claims_by_id = {
        claim["id"]: claim for claim in evidence_state.get("claims", []) if claim.get("id")
    }
    sources_by_id = source_index(sources_state)
    coverage_records = evidence_state.get("coverage", [])
    coverage_by_block: dict[str, list[dict[str, Any]]] = {}
    normalized_coverage_records: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    prose_blocks = _prose_block_records(manuscript_state)
    prose_block_ids = {block["block_id"] for block in prose_blocks}

    for record in coverage_records:
        block_id = str(record.get("block_id", "")).strip()
        status = _coverage_status(record)
        kind = str(record.get("kind", "")).strip()
        claim_ids = [claim_id for claim_id in record.get("claim_ids", []) if claim_id]
        source_ids = [source_id for source_id in record.get("source_ids", []) if source_id]
        note = str(record.get("note", "")).strip()
        valid_claim_ids = [claim_id for claim_id in claim_ids if claim_id in claims_by_id]
        valid_source_ids = [source_id for source_id in source_ids if source_id in sources_by_id]

        if not block_id:
            findings.append(
                {
                    "kind": "coverage",
                    "location": "coverage",
                    "label": "Coverage record is missing a block ID",
                    "snippet": kind or "[unknown kind]",
                }
            )
            continue

        if block_id not in prose_block_ids:
            findings.append(
                {
                    "kind": "coverage",
                    "location": block_id,
                    "label": "Coverage record points at a missing manuscript block",
                    "snippet": block_id,
                }
            )

        if status not in COVERAGE_STATUSES:
            findings.append(
                {
                    "kind": "coverage",
                    "location": block_id,
                    "label": "Coverage record uses an unknown status",
                    "snippet": status,
                }
            )
            continue

        if kind not in COVERAGE_KINDS:
            findings.append(
                {
                    "kind": "coverage",
                    "location": block_id,
                    "label": "Coverage record uses an unknown classification",
                    "snippet": kind,
                }
            )
            continue

        missing_claim_ids = [claim_id for claim_id in claim_ids if claim_id not in claims_by_id]
        missing_source_ids = [source_id for source_id in source_ids if source_id not in sources_by_id]
        if missing_claim_ids:
            findings.append(
                {
                    "kind": "coverage",
                    "location": block_id,
                    "label": "Coverage record references missing claim IDs",
                    "snippet": ", ".join(missing_claim_ids),
                }
            )
        if missing_source_ids:
            findings.append(
                {
                    "kind": "coverage",
                    "location": block_id,
                    "label": "Coverage record references missing source IDs",
                    "snippet": ", ".join(missing_source_ids),
                }
            )

        if status == "confirmed" and kind == "claim" and not valid_claim_ids:
            findings.append(
                {
                    "kind": "coverage",
                    "location": block_id,
                    "label": "Claim coverage requires at least one linked claim ID",
                    "snippet": "",
                }
            )
        if status == "confirmed" and kind == "background" and not (valid_claim_ids or valid_source_ids):
            findings.append(
                {
                    "kind": "coverage",
                    "location": block_id,
                    "label": "Background coverage requires a claim ID or source ID",
                    "snippet": "",
                }
            )
        if status == "confirmed" and kind in {"method_note", "uncited_ok"} and not (claim_ids or source_ids or note):
            findings.append(
                {
                    "kind": "coverage",
                    "location": block_id,
                    "label": "This coverage category requires a note or supporting link",
                    "snippet": "",
                }
            )

        normalized_record = {
            **record,
            "status": status,
            "kind": kind,
            "claim_ids": valid_claim_ids,
            "source_ids": valid_source_ids,
            "note": note,
        }
        coverage_by_block.setdefault(block_id, []).append(normalized_record)
        normalized_coverage_records.append(
            normalized_record
        )

    block_reports: list[dict[str, Any]] = []
    uncovered_blocks: list[dict[str, Any]] = []
    reviewable_blocks = 0
    covered_blocks = 0

    for block in prose_blocks:
        records = coverage_by_block.get(block["block_id"], [])
        confirmed_records = [
            record for record in records if record.get("status") == "confirmed"
        ]
        suggested_records = [
            record for record in records if record.get("status") == "suggested"
        ]
        needs_review = _block_needs_review(block, records)
        classification = "short"
        covered = True

        if needs_review:
            reviewable_blocks += 1
            valid_record = next(
                (
                    record
                    for record in confirmed_records
                    if _coverage_record_satisfies(record, block)
                ),
                None,
            )
            if valid_record:
                classification = str(valid_record.get("kind"))
            elif block["has_inline_citation"]:
                classification = "inline_citation"
            else:
                covered = False
                classification = (
                    f"suggested_{suggested_records[0].get('kind', 'coverage')}"
                    if suggested_records
                    else "uncovered"
                )
                uncovered_blocks.append(
                    {
                        "block_id": block["block_id"],
                        "location": block["location"],
                        "word_count": block["word_count"],
                        "snippet": block["text"][:160],
                    }
                )

        if covered and needs_review:
            covered_blocks += 1

        block_reports.append(
            {
                **block,
                "classification": classification,
                "covered": covered,
                "coverage_records": records,
                "confirmed_coverage_records": confirmed_records,
                "suggested_coverage_records": suggested_records,
            }
        )

    for block in uncovered_blocks:
        findings.append(
            {
                "kind": "coverage",
                "location": block["location"],
                "label": "Substantial argumentative prose lacks evidence coverage classification",
                "snippet": block["snippet"],
            }
        )

    return {
        "minimum_argument_words": MIN_ARGUMENT_WORDS,
        "reviewable_blocks": reviewable_blocks,
        "covered_blocks": covered_blocks,
        "uncovered_blocks": uncovered_blocks,
        "coverage_records": normalized_coverage_records,
        "blocks": block_reports,
        "findings": findings,
    }


def stage_gate_findings(
    workflow_state: dict[str, Any],
    word_validation: dict[str, Any],
    artifact_issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not word_validation["passed"] and workflow_state.get("active_stage") in {"review", "export", "completed"}:
        findings.append(
            {
                "kind": "word_count",
                "location": workflow_state.get("active_stage", ""),
                "label": "Word-count policy is not satisfied",
                "snippet": word_validation["message"],
            }
        )
    if artifact_issues and workflow_state.get("active_stage") in {"export", "completed"}:
        findings.append(
            {
                "kind": "artifact",
                "location": workflow_state.get("active_stage", ""),
                "label": "Formatted export is blocked by unresolved authoring artifacts",
                "snippet": artifact_issues[0]["label"],
            }
        )
    return findings


def validate_project_state(
    project_state: dict[str, Any],
    workflow_state: dict[str, Any],
    manuscript_state: dict[str, Any],
    sources_state: dict[str, Any],
    evidence_state: dict[str, Any],
) -> dict[str, Any]:
    word_report = manuscript_word_report(
        project_state,
        manuscript_state,
        sources_state,
        evidence_state,
    )
    word_validation = validate_target_policy(project_state["word_target"], word_report["included_total"])
    diagnostics = under_over_diagnostics(manuscript_state, word_report, word_validation)
    artifact_issues = artifact_findings(manuscript_state, evidence_state)
    reference_issues = reference_findings(
        project_state, manuscript_state, sources_state, evidence_state
    )
    coverage_report = manuscript_coverage_report(
        manuscript_state,
        sources_state,
        evidence_state,
    )
    coverage_issues = coverage_report["findings"]
    stage_issues = stage_gate_findings(workflow_state, word_validation, artifact_issues)
    findings = artifact_issues + reference_issues + coverage_issues + stage_issues
    return {
        "valid": not findings and word_validation["passed"],
        "word_report": word_report,
        "word_validation": word_validation,
        "diagnostics": diagnostics,
        "coverage_report": coverage_report,
        "findings": findings,
    }
