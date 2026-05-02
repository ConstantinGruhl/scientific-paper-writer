from __future__ import annotations

import re
from typing import Any

from .evidence_assets import figure_caption_text, lookup_figure, lookup_table, table_text_fragments
from .manuscript import block_plain_text, parse_markdown_blocks


WORD_RE = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)
SECTION_BUCKET_KEYS = ("headings", "body", "figure_captions", "tables")


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def default_counting_policy() -> dict[str, bool]:
    return {
        "include_title": True,
        "include_abstract": True,
        "include_headings": False,
        "include_figure_captions": False,
        "include_tables": False,
        "include_references": False,
        "include_appendices": False,
    }


def default_target_policy(target: int) -> dict[str, Any]:
    return {
        "mode": "target_tolerance",
        "target": target,
        "tolerance": max(100, int(target * 0.05)),
        "minimum": 0,
        "maximum": 0,
        "exact_target": 0,
    }


def _resolved_counting_policy(policy: dict[str, bool] | None) -> dict[str, bool]:
    resolved = default_counting_policy()
    if policy:
        resolved.update(policy)
    return resolved


def _empty_section_buckets() -> dict[str, int]:
    return {key: 0 for key in SECTION_BUCKET_KEYS}


def _figure_caption_word_count(evidence_state: dict[str, Any], figure_id: str) -> int:
    figure = lookup_figure(evidence_state, figure_id)
    if not figure:
        return 0
    return count_words(figure_caption_text(figure))


def _table_word_count(evidence_state: dict[str, Any], table_id: str) -> int:
    table = lookup_table(evidence_state, table_id)
    if not table:
        return 0
    return count_words(" ".join(table_text_fragments(table)))


def _included_and_excluded_words(
    bucket_counts: dict[str, int],
    counting_policy: dict[str, bool],
    *,
    is_appendix: bool,
) -> tuple[int, int]:
    total_words = sum(bucket_counts.values())
    if is_appendix and not counting_policy["include_appendices"]:
        return 0, total_words

    included = bucket_counts["body"]
    excluded = 0
    for key, policy_key in (
        ("headings", "include_headings"),
        ("figure_captions", "include_figure_captions"),
        ("tables", "include_tables"),
    ):
        if counting_policy[policy_key]:
            included += bucket_counts[key]
        else:
            excluded += bucket_counts[key]
    return included, excluded


def _section_rollup(
    section: dict[str, Any],
    counting_policy: dict[str, bool],
    evidence_state: dict[str, Any],
    *,
    is_appendix: bool = False,
) -> dict[str, Any]:
    local_bucket_counts = _empty_section_buckets()
    local_bucket_counts["headings"] = count_words(section["title"])

    for block in parse_markdown_blocks(section.get("content", "")):
        if block["kind"] == "figure":
            local_bucket_counts["figure_captions"] += _figure_caption_word_count(
                evidence_state, block["figure_id"]
            )
            continue
        if block["kind"] == "table":
            local_bucket_counts["tables"] += _table_word_count(evidence_state, block["table_id"])
            continue
        local_bucket_counts["body"] += count_words(block_plain_text(block))

    subsection_reports = [
        _section_rollup(subsection, counting_policy, evidence_state, is_appendix=is_appendix)
        for subsection in section.get("subsections", [])
    ]

    bucket_counts = dict(local_bucket_counts)
    for subsection in subsection_reports:
        for key in bucket_counts:
            bucket_counts[key] += subsection["bucket_counts"][key]

    included, excluded = _included_and_excluded_words(
        bucket_counts,
        counting_policy,
        is_appendix=is_appendix,
    )

    return {
        "id": section["id"],
        "title": section["title"],
        "target_words": section.get("target_words", 0),
        "is_appendix": is_appendix,
        "total_words": sum(bucket_counts.values()),
        "included_words": included,
        "excluded_words": excluded,
        "local_bucket_counts": local_bucket_counts,
        "bucket_counts": bucket_counts,
        "subsections": subsection_reports,
    }


def manuscript_word_report(
    project_state: dict[str, Any],
    manuscript_state: dict[str, Any],
    sources_state: dict[str, Any],
    evidence_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    counting_policy = _resolved_counting_policy(project_state.get("counting_policy"))
    evidence_state = evidence_state or {}
    bucket_counts = {
        "title": 0,
        "abstract": 0,
        "headings": 0,
        "body": 0,
        "figure_captions": 0,
        "tables": 0,
        "references": 0,
        "appendices": 0,
    }

    bucket_counts["title"] = count_words(manuscript_state.get("title", ""))

    for block in parse_markdown_blocks(manuscript_state.get("abstract", "")):
        bucket_counts["abstract"] += count_words(block_plain_text(block))

    section_reports = [
        _section_rollup(section, counting_policy, evidence_state)
        for section in manuscript_state.get("sections", [])
    ]
    appendix_reports = [
        _section_rollup(section, counting_policy, evidence_state, is_appendix=True)
        for section in manuscript_state.get("appendices", [])
    ]

    all_reports = section_reports + appendix_reports
    for key in SECTION_BUCKET_KEYS:
        bucket_counts[key] = sum(report["bucket_counts"][key] for report in all_reports)
    bucket_counts["appendices"] = sum(report["total_words"] for report in appendix_reports)

    from .references import build_citation_order, bibliography_entries

    citation_style = project_state["profiles"]["citation"]
    citation_order = build_citation_order(manuscript_state, evidence_state)
    references = bibliography_entries(sources_state, citation_style, citation_order)
    bucket_counts["references"] = sum(count_words(entry) for entry in references)

    included_total = 0
    excluded_total = 0
    for key, policy_key in (
        ("title", "include_title"),
        ("abstract", "include_abstract"),
        ("references", "include_references"),
    ):
        if counting_policy[policy_key]:
            included_total += bucket_counts[key]
        else:
            excluded_total += bucket_counts[key]

    included_total += sum(report["included_words"] for report in section_reports)
    included_total += sum(report["included_words"] for report in appendix_reports)
    excluded_total += sum(report["excluded_words"] for report in section_reports)
    excluded_total += sum(report["excluded_words"] for report in appendix_reports)

    section_summaries: list[dict[str, Any]] = section_reports + appendix_reports
    return {
        "policy": counting_policy,
        "bucket_counts": bucket_counts,
        "included_total": included_total,
        "excluded_total": excluded_total,
        "sections": section_summaries,
    }


def validate_target_policy(word_target: dict[str, Any], included_total: int) -> dict[str, Any]:
    mode = word_target.get("mode", "target_tolerance")
    if mode == "exact":
        exact_target = int(word_target.get("exact_target", 0))
        passed = included_total == exact_target
        return {
            "passed": passed,
            "message": f"Expected exactly {exact_target}, got {included_total}.",
            "delta": included_total - exact_target,
        }
    if mode == "minimum_maximum":
        minimum = int(word_target.get("minimum", 0))
        maximum = int(word_target.get("maximum", 0))
        passed = minimum <= included_total <= maximum
        return {
            "passed": passed,
            "message": f"Expected between {minimum} and {maximum}, got {included_total}.",
            "delta": 0 if passed else (included_total - maximum if included_total > maximum else included_total - minimum),
        }
    target = int(word_target.get("target", 0))
    tolerance = int(word_target.get("tolerance", 0))
    minimum = target - tolerance
    maximum = target + tolerance
    passed = minimum <= included_total <= maximum
    return {
        "passed": passed,
        "message": f"Expected {target} +/- {tolerance}, got {included_total}.",
        "delta": included_total - target,
    }


def section_budget_report(
    manuscript_state: dict[str, Any],
    word_report: dict[str, Any],
) -> list[dict[str, Any]]:
    def walk_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        walked: list[dict[str, Any]] = []
        for section in sections:
            walked.append(section)
            walked.extend(walk_sections(section.get("subsections", [])))
        return walked

    def walk_summaries(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        walked: list[dict[str, Any]] = []
        for section in sections:
            walked.append(section)
            walked.extend(walk_summaries(section.get("subsections", [])))
        return walked

    section_map = {section["id"]: section for section in walk_sections(manuscript_state.get("sections", []))}
    section_map.update({section["id"]: section for section in walk_sections(manuscript_state.get("appendices", []))})

    report: list[dict[str, Any]] = []
    for section_summary in walk_summaries(word_report["sections"]):
        section = section_map.get(section_summary["id"], {})
        target_words = int(section.get("target_words", 0) or 0)
        actual = int(section_summary["included_words"])
        variance = actual - target_words
        ratio = round((actual / target_words), 2) if target_words else None
        report.append(
            {
                "id": section_summary["id"],
                "title": section_summary["title"],
                "target_words": target_words,
                "actual_words": actual,
                "variance": variance,
                "ratio": ratio,
            }
        )
    return report


def under_over_diagnostics(
    manuscript_state: dict[str, Any],
    word_report: dict[str, Any],
    target_validation: dict[str, Any],
) -> dict[str, Any]:
    def walk_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        walked: list[dict[str, Any]] = []
        for section in sections:
            walked.append(section)
            walked.extend(walk_sections(section.get("subsections", [])))
        return walked

    section_map = {section["id"]: section for section in walk_sections(manuscript_state.get("sections", []))}
    section_map.update({section["id"]: section for section in walk_sections(manuscript_state.get("appendices", []))})

    budget_rows = section_budget_report(manuscript_state, word_report)
    missing_sections = [
        row["title"]
        for row in budget_rows
        if row["actual_words"] == 0 and section_map.get(row["id"], {}).get("required", False)
    ]
    thinnest_sections = sorted(
        [row for row in budget_rows if row["target_words"] and row["actual_words"] < row["target_words"]],
        key=lambda row: (row["ratio"] if row["ratio"] is not None else 0.0),
    )
    longest_sections = sorted(
        [row for row in budget_rows if row["target_words"] and row["actual_words"] > row["target_words"]],
        key=lambda row: row["variance"],
        reverse=True,
    )

    status = "on_target"
    if target_validation["delta"] < 0:
        status = "under_target"
    elif target_validation["delta"] > 0:
        status = "over_target"

    return {
        "status": status,
        "missing_sections": missing_sections,
        "underdeveloped_sections": thinnest_sections[:5],
        "overlong_sections": longest_sections[:5],
        "budget_rows": budget_rows,
    }
