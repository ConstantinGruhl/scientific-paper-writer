from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .profiles import resolve_profiles
from .references import bibliography_entries, build_citation_order, claim_support_summary
from .workflow import default_workflow_state, visible_task_rows
from .word_count import default_counting_policy, default_target_policy


ROLE_NOTE_FILES = [
    "manager",
    "researcher",
    "scientist",
    "source_checker",
    "outliner",
    "drafter",
    "reviewer",
    "style_proofreader",
    "progress_auditor",
]

STATE_FILES = [
    "project.json",
    "workflow.json",
    "manuscript.json",
    "sources.json",
    "evidence.json",
    "reviews.json",
    "exports.json",
]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "paper-project"


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def workspace_dir(root: Path) -> Path:
    return root / ".paper_writer"


def state_dir(root: Path) -> Path:
    return workspace_dir(root) / "state"


def trace_path(root: Path) -> Path:
    return state_dir(root) / "trace.jsonl"


def ensure_layout(root: Path) -> None:
    workspace_dir(root).mkdir(parents=True, exist_ok=True)
    state_dir(root).mkdir(parents=True, exist_ok=True)
    (root / "notes").mkdir(exist_ok=True)
    (root / "sources").mkdir(exist_ok=True)
    (root / "deliverables").mkdir(exist_ok=True)


def default_project_state(
    *,
    root: Path,
    title: str,
    paper_type: str,
    output_mode: str,
    citation_style: str | None,
    formatting_profile: str | None,
    figure_mode: str,
    discipline: str,
    deadline: str,
    run_mode: str,
    institution_override_path: str | None,
    word_target: dict[str, Any] | None,
    counting_policy: dict[str, bool] | None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    project_slug = slugify(root.name if root.name else title)
    profiles = resolve_profiles(
        paper_type,
        formatting_profile_id=formatting_profile,
        citation_profile_id=citation_style,
        institution_override_path=institution_override_path,
    )
    target_policy = word_target or default_target_policy(
        profiles["paper_type"].get("default_word_target", 5000)
    )
    project_state = {
        "schema_version": 2,
        "project": {
            "title": title,
            "slug": project_slug,
            "created_on": date.today().isoformat(),
            "updated_on": date.today().isoformat(),
            "discipline": discipline,
            "deadline": deadline,
        },
        "run_mode": run_mode,
        "output_mode": output_mode,
        "formatted_outputs": ["docx", "pdf"],
        "figure_mode": figure_mode,
        "profiles": {
            "paper_type": paper_type,
            "formatting": profiles["formatting"]["id"],
            "citation": profiles["citation"]["id"],
            "institution_override_path": institution_override_path or "",
        },
        "profile_resolution": {
            "paper_type_label": profiles["paper_type"]["label"],
            "formatting_label": profiles["formatting"]["label"],
            "citation_label": profiles["citation"]["label"],
            "default_reason": (
                "Institution override merged"
                if institution_override_path
                else "Paper-type defaults selected"
            ),
            "effective_formatting": profiles["formatting"],
        },
        "word_target": target_policy,
        "counting_policy": counting_policy or default_counting_policy(),
    }
    return project_state, profiles


def _section_record(section_template: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": section_template["id"],
        "title": section_template["title"],
        "role": section_template.get("role", "section"),
        "required": bool(section_template.get("required", False)),
        "target_words": int(section_template.get("target_words", 0) or 0),
        "content": section_template.get("starter_text", ""),
        "subsections": [_section_record(subsection) for subsection in section_template.get("subsections", [])],
    }


def default_manuscript_state(
    project_state: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    paper_type = profiles["paper_type"]
    return {
        "schema_version": 2,
        "title": project_state["project"]["title"],
        "abstract": paper_type.get("abstract_starter_text", ""),
        "keywords": [],
        "sections": [_section_record(section) for section in paper_type.get("sections", [])],
        "appendices": [],
    }


def default_sources_state() -> dict[str, Any]:
    return {"schema_version": 2, "sources": [], "notes": []}


def default_evidence_state() -> dict[str, Any]:
    return {"schema_version": 2, "claims": [], "figures": [], "tables": [], "coverage": []}


def default_reviews_state(profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "findings": [],
        "checklist": profiles["paper_type"].get("default_review_checklist", []),
    }


def default_exports_state(project_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "output_mode": project_state["output_mode"],
        "raw_text": {"path": "deliverables/final_paper.txt", "status": "not_started"},
        "docx": {"path": "deliverables/final_paper.docx", "status": "not_started"},
        "pdf": {"path": "deliverables/final_paper.pdf", "status": "not_started"},
        "last_validation": {},
    }


def save_state(root: Path, file_name: str, payload: dict[str, Any]) -> None:
    (state_dir(root) / file_name).write_text(_json_dumps(payload), encoding="utf-8")


def load_state(root: Path, file_name: str) -> dict[str, Any]:
    path = state_dir(root) / file_name
    return json.loads(path.read_text(encoding="utf-8"))


def load_all_states(root: Path) -> dict[str, dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    for file_name in STATE_FILES:
        states[file_name[:-5]] = load_state(root, file_name)
    return states


def append_trace(root: Path, event: dict[str, Any]) -> None:
    with trace_path(root).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")


def init_workspace(
    root: Path,
    *,
    title: str,
    paper_type: str,
    output_mode: str,
    citation_style: str | None,
    formatting_profile: str | None,
    figure_mode: str,
    discipline: str,
    deadline: str,
    run_mode: str,
    institution_override_path: str | None,
    word_target: dict[str, Any] | None,
    counting_policy: dict[str, bool] | None,
    force: bool = False,
) -> Path:
    ensure_layout(root)
    if state_dir(root).exists():
        existing_files = list(state_dir(root).glob("*.json"))
        if existing_files and not force:
            raise FileExistsError(f"Workspace already exists at {state_dir(root)}")

    project_state, profiles = default_project_state(
        root=root,
        title=title,
        paper_type=paper_type,
        output_mode=output_mode,
        citation_style=citation_style,
        formatting_profile=formatting_profile,
        figure_mode=figure_mode,
        discipline=discipline,
        deadline=deadline,
        run_mode=run_mode,
        institution_override_path=institution_override_path,
        word_target=word_target,
        counting_policy=counting_policy,
    )
    workflow_state = default_workflow_state(run_mode=run_mode)
    manuscript_state = default_manuscript_state(project_state, profiles)
    sources_state = default_sources_state()
    evidence_state = default_evidence_state()
    reviews_state = default_reviews_state(profiles)
    exports_state = default_exports_state(project_state)

    save_state(root, "project.json", project_state)
    save_state(root, "workflow.json", workflow_state)
    save_state(root, "manuscript.json", manuscript_state)
    save_state(root, "sources.json", sources_state)
    save_state(root, "evidence.json", evidence_state)
    save_state(root, "reviews.json", reviews_state)
    save_state(root, "exports.json", exports_state)

    append_trace(
        root,
        {
            "event": "workspace_initialized",
            "title": title,
            "paper_type": paper_type,
            "output_mode": output_mode,
            "run_mode": run_mode,
            "date": date.today().isoformat(),
        },
    )
    ensure_note_files(root)
    render_views(root)
    return root


def ensure_note_files(root: Path) -> None:
    readme_path = root / "notes" / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            "# Notes\n\nThis folder contains human-readable coordination notes. Canonical machine state lives in `.paper_writer/state/`.\n",
            encoding="utf-8",
        )

    handoffs_path = root / "notes" / "handoffs.md"
    if not handoffs_path.exists():
        handoffs_path.write_text(
            "# Handoffs\n\n| From | To | Request | Related Files | Unresolved Risk |\n| --- | --- | --- | --- | --- |\n",
            encoding="utf-8",
        )

    for role in ROLE_NOTE_FILES:
        note_path = root / "notes" / f"{role}.md"
        if note_path.exists():
            continue
        note_path.write_text(
            f"# {role.replace('_', ' ').title()} Notes\n\n"
            "- Current goal:\n"
            "- Current plan:\n"
            "- Decisions made:\n"
            "- Evidence needed next:\n"
            "- Handoff request:\n",
            encoding="utf-8",
        )

    sources_readme = root / "sources" / "README.md"
    if not sources_readme.exists():
        sources_readme.write_text(
            "# Sources\n\nCanonical source metadata lives in `.paper_writer/state/sources.json`. Use this folder for richer human-readable notes or imported PDFs.\n",
            encoding="utf-8",
        )


def _project_brief_markdown(project_state: dict[str, Any]) -> str:
    target = project_state["word_target"]
    target_summary = ""
    if target["mode"] == "exact":
        target_summary = f"Exact {target['exact_target']} words"
    elif target["mode"] == "minimum_maximum":
        target_summary = f"{target['minimum']} to {target['maximum']} words"
    else:
        target_summary = f"{target['target']} +/- {target['tolerance']} words"

    lines = [
        "# Project Brief",
        "",
        "## Project Identity",
        "",
        f"- Working title: {project_state['project']['title']}",
        f"- Project slug: {project_state['project']['slug']}",
        f"- Discipline: {project_state['project']['discipline'] or '[Not set]'}",
        f"- Deadline: {project_state['project']['deadline'] or '[Not set]'}",
        "",
        "## Run Settings",
        "",
        f"- Run mode: {project_state['run_mode']}",
        f"- Output mode: {project_state['output_mode']}",
        f"- Figure mode: {project_state['figure_mode']}",
        "",
        "## Profile Selection",
        "",
        f"- Paper type: {project_state['profiles']['paper_type']}",
        f"- Formatting profile: {project_state['profiles']['formatting']}",
        f"- Citation style: {project_state['profiles']['citation']}",
        f"- Institution override: {project_state['profiles']['institution_override_path'] or '[None]'}",
        "",
        "## Word Count Policy",
        "",
        f"- Target: {target_summary}",
        f"- Include title: {project_state['counting_policy']['include_title']}",
        f"- Include abstract: {project_state['counting_policy']['include_abstract']}",
        f"- Include headings: {project_state['counting_policy']['include_headings']}",
        f"- Include figure captions: {project_state['counting_policy']['include_figure_captions']}",
        f"- Include tables: {project_state['counting_policy']['include_tables']}",
        f"- Include references: {project_state['counting_policy']['include_references']}",
        f"- Include appendices: {project_state['counting_policy']['include_appendices']}",
        "",
        "## Notes",
        "",
        "- Canonical workflow state lives in `.paper_writer/state/`.",
        "- This file is a rendered human-readable view.",
        "",
    ]
    return "\n".join(lines)


def _project_context_markdown(
    project_state: dict[str, Any],
    workflow_state: dict[str, Any],
) -> str:
    lines = [
        "# Project Context",
        "",
        "## Project",
        "",
        f"- Slug: {project_state['project']['slug']}",
        f"- Working title: {project_state['project']['title']}",
        f"- Created on: {project_state['project']['created_on']}",
        f"- Updated on: {project_state['project']['updated_on']}",
        f"- Output mode: {project_state['output_mode']}",
        f"- Active stage: {workflow_state['active_stage']}",
        f"- Workflow status: {workflow_state['status']}",
        "",
        "## Stage Status",
        "",
    ]
    for stage, record in workflow_state["stages"].items():
        lines.append(f"- {stage}: {record['status']}")
    lines.extend(
        [
            "",
            "## Profile Resolution",
            "",
            f"- Paper type: {project_state['profile_resolution']['paper_type_label']}",
            f"- Formatting: {project_state['profile_resolution']['formatting_label']}",
            f"- Citation: {project_state['profile_resolution']['citation_label']}",
            f"- Selection note: {project_state['profile_resolution']['default_reason']}",
            "",
            "## Notes",
            "",
            "- Canonical structured state lives in `.paper_writer/state/`.",
            "",
        ]
    )
    return "\n".join(lines)


def _research_plan_markdown(
    project_state: dict[str, Any],
    manuscript_state: dict[str, Any],
) -> str:
    lines = [
        "# Research Plan",
        "",
        "## Working Objective",
        "",
        f"- Build a {project_state['profiles']['paper_type']} manuscript around `{project_state['project']['title']}`.",
        "",
        "## Expected Structure",
        "",
    ]
    for section in manuscript_state["sections"]:
        requirement = "required" if section["required"] else "optional"
        lines.append(
            f"- {section['title']} ({requirement}, target {section['target_words']} words)"
        )
    lines.extend(
        [
            "",
            "## Evidence Priorities",
            "",
            "- Register verified sources in `.paper_writer/state/sources.json`.",
            "- Link major claims in `.paper_writer/state/evidence.json` before marking review complete.",
            "- Classify substantial uncited prose with `coverage` records in `.paper_writer/state/evidence.json`.",
            "- Run `spw scaffold-coverage` to seed suggested coverage records before manual confirmation.",
            "",
        ]
    )
    return "\n".join(lines)


def _outline_markdown(manuscript_state: dict[str, Any]) -> str:
    lines = ["# Outline", ""]
    for section in manuscript_state["sections"]:
        lines.append(f"## {section['title']}")
        lines.append("")
        lines.append(f"- Target words: {section['target_words']}")
        lines.append(f"- Required: {section['required']}")
        lines.append("")
    return "\n".join(lines)


def _bibliography_markdown(
    project_state: dict[str, Any],
    manuscript_state: dict[str, Any],
    sources_state: dict[str, Any],
    evidence_state: dict[str, Any],
) -> str:
    citation_order = build_citation_order(manuscript_state, evidence_state)
    entries = bibliography_entries(
        sources_state, project_state["profiles"]["citation"], citation_order
    )
    lines = [
        "# Bibliography",
        "",
        f"- Citation style: {project_state['profiles']['citation']}",
        f"- Verified entries exported: {len(entries)}",
        "",
    ]
    if not entries:
        lines.extend(["No verified bibliography entries yet.", ""])
    else:
        for entry in entries:
            lines.append(f"- {entry}")
        lines.append("")
    return "\n".join(lines)


def _coverage_record_status(record: dict[str, Any]) -> str:
    status = str(record.get("status", "confirmed")).strip().lower()
    return status or "confirmed"


def _evidence_matrix_markdown(evidence_state: dict[str, Any]) -> str:
    lines = [
        "# Evidence Matrix",
        "",
        "## Claims",
        "",
        "| Claim ID | Section | Claim | Source IDs | Support Strength |",
        "| --- | --- | --- | --- | --- |",
    ]
    for claim in evidence_state["claims"]:
        lines.append(
            "| {id} | {section} | {claim_text} | {sources} | {strength} |".format(
                id=claim.get("id", ""),
                section=claim.get("section_id", ""),
                claim_text=claim.get("claim_text", "").replace("|", "\\|"),
                sources=", ".join(claim.get("source_ids", [])),
                strength=claim.get("support_strength", ""),
            )
        )
    if not evidence_state["claims"]:
        lines.append("| [none] | | | | |")
    lines.extend(
        [
            "",
            "## Coverage Records",
            "",
        ]
    )
    if any(_coverage_record_status(record) == "suggested" for record in evidence_state.get("coverage", [])):
        lines.extend(
            [
                "Suggested records are review prompts only; final validation still requires confirmed coverage where applicable.",
                "",
            ]
        )
    lines.extend(
        [
            "| Block ID | Status | Kind | Claims | Sources | Note |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in evidence_state.get("coverage", []):
        lines.append(
            "| {block_id} | {status} | {kind} | {claims} | {sources} | {note} |".format(
                block_id=record.get("block_id", "").replace("|", "\\|"),
                status=_coverage_record_status(record).replace("|", "\\|"),
                kind=record.get("kind", "").replace("|", "\\|"),
                claims=", ".join(record.get("claim_ids", [])),
                sources=", ".join(record.get("source_ids", [])),
                note=str(record.get("note", "")).replace("|", "\\|"),
            )
        )
    if not evidence_state.get("coverage"):
        lines.append("| [none] | | | | | |")
    lines.append("")
    return "\n".join(lines)


def _revision_checklist_markdown(reviews_state: dict[str, Any]) -> str:
    lines = ["# Revision Checklist", ""]
    checklist = reviews_state.get("checklist", [])
    for item in checklist:
        lines.append(f"- [ ] {item}")
    if reviews_state.get("findings"):
        lines.extend(["", "## Recorded Findings", ""])
        for finding in reviews_state["findings"]:
            lines.append(
                f"- {finding.get('severity', 'info')}: {finding.get('summary', '')}"
            )
    lines.append("")
    return "\n".join(lines)


def _agent_status_markdown(workflow_state: dict[str, Any]) -> str:
    lines = [
        "# Agent Status",
        "",
        f"- Active stage: {workflow_state['active_stage']}",
        f"- Workflow status: {workflow_state['status']}",
        "",
        "## Worker Tasks",
        "",
        "| ID | Role | Stage | Status | Description | Files | Blocker |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    rows = visible_task_rows(workflow_state)
    if not rows:
        lines.append("| [none] | manager | intake | in_progress | Waiting for first task | | |")
    else:
        for row in rows:
            lines.append(
                "| {id} | {role} | {stage} | {status} | {description} | {files} | {blocker} |".format(
                    id=row["id"],
                    role=row["role"],
                    stage=row["stage"],
                    status=row["status"],
                    description=row["description"].replace("|", "\\|"),
                    files=", ".join(row["owned_paths"]),
                    blocker=row["blocker"].replace("|", "\\|"),
                )
            )
    lines.extend(["", "## Checkpoints", ""])
    if not workflow_state["checkpoints"]:
        lines.append("- No checkpoints recorded yet.")
    else:
        for checkpoint in workflow_state["checkpoints"]:
            lines.append(
                f"- {checkpoint['stage']}: {checkpoint['status']} - {checkpoint['summary']}"
            )
    lines.append("")
    return "\n".join(lines)


def _section_markdown(section: dict[str, Any], level: int = 2) -> list[str]:
    prefix = "#" * level
    lines = [f"{prefix} {section['title']}", ""]
    if section.get("content"):
        lines.append(section["content"].rstrip())
        lines.append("")
    else:
        lines.append("[Section draft pending]")
        lines.append("")
    for subsection in section.get("subsections", []):
        lines.extend(_section_markdown(subsection, level=level + 1))
    return lines


def _draft_markdown(
    project_state: dict[str, Any],
    manuscript_state: dict[str, Any],
    sources_state: dict[str, Any],
    evidence_state: dict[str, Any],
) -> str:
    lines = [
        "# Draft",
        "",
        f"Title: {manuscript_state.get('title') or project_state['project']['title']}",
        "",
        "## Abstract",
        "",
    ]
    lines.append(manuscript_state.get("abstract", "[Abstract pending]").rstrip() or "[Abstract pending]")
    lines.extend(["", "## Body", ""])
    for section in manuscript_state["sections"]:
        lines.extend(_section_markdown(section, level=3))

    if manuscript_state.get("appendices"):
        lines.extend(["## Appendices", ""])
        for appendix in manuscript_state["appendices"]:
            lines.extend(_section_markdown(appendix, level=3))

    citation_order = build_citation_order(manuscript_state, evidence_state)
    entries = bibliography_entries(
        sources_state, project_state["profiles"]["citation"], citation_order
    )
    lines.extend(["## References", ""])
    if entries:
        for entry in entries:
            lines.append(f"- {entry}")
    else:
        lines.append("[No verified references yet]")
    lines.append("")
    return "\n".join(lines)


def render_views(root: Path) -> None:
    states = load_all_states(root)
    project_state = states["project"]
    workflow_state = states["workflow"]
    manuscript_state = states["manuscript"]
    sources_state = states["sources"]
    evidence_state = states["evidence"]
    reviews_state = states["reviews"]

    files = {
        "project_brief.md": _project_brief_markdown(project_state),
        "project_context.md": _project_context_markdown(project_state, workflow_state),
        "research_plan.md": _research_plan_markdown(project_state, manuscript_state),
        "bibliography.md": _bibliography_markdown(
            project_state, manuscript_state, sources_state, evidence_state
        ),
        "evidence_matrix.md": _evidence_matrix_markdown(evidence_state),
        "outline.md": _outline_markdown(manuscript_state),
        "draft.md": _draft_markdown(
            project_state, manuscript_state, sources_state, evidence_state
        ),
        "revision_checklist.md": _revision_checklist_markdown(reviews_state),
        "agent_status.md": _agent_status_markdown(workflow_state),
    }

    for name, content in files.items():
        (root / name).write_text(content.strip() + "\n", encoding="utf-8")

    final_markdown = _draft_markdown(
        project_state, manuscript_state, sources_state, evidence_state
    ).replace("# Draft", "# Final Paper", 1)
    (root / "deliverables" / "final_paper.md").write_text(
        final_markdown.strip() + "\n", encoding="utf-8"
    )


def claim_summary_markdown(evidence_state: dict[str, Any]) -> str:
    summary = claim_support_summary(evidence_state)
    if not summary:
        return "- No evidence links recorded yet."
    return "\n".join(
        f"- {source_id}: supports {', '.join(claim_ids)}"
        for source_id, claim_ids in sorted(summary.items())
    )
