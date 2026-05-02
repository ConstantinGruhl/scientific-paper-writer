from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .workspace import (
    init_workspace,
    load_all_states,
    render_views,
    save_state,
    slugify,
)


HEADING_RE = re.compile(r"^(#{2,3})\s+(.*)$")


def _extract_bullet_field(text: str, label: str) -> str:
    pattern = re.compile(rf"^- {re.escape(label)}:[ \t]*(.*)$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _map_paper_type(raw: str) -> str:
    lowered = raw.strip().lower()
    mapping = {
        "literature review": "literature_review",
        "theoretical / conceptual paper": "theoretical_conceptual",
        "case study": "case_study",
        "thesis/dissertation chapter": "thesis_chapter",
        "short conference paper": "short_conference",
        "empirical / imrad paper": "empirical_imrad",
    }
    return mapping.get(lowered, "empirical_imrad")


def _split_legacy_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "preface"
    sections[current] = []
    for line in text.splitlines():
        match = HEADING_RE.match(line.strip())
        if match:
            current = match.group(2).strip()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def _section_id(title: str) -> str:
    return slugify(title)


def migrate_legacy_workspace(root: Path, force: bool = False) -> Path:
    state_root = root / ".paper_writer" / "state"
    if state_root.exists() and list(state_root.glob("*.json")) and not force:
        return root

    legacy_workspace = root / ".paper_writer"
    legacy_folder_native = legacy_workspace.exists()
    legacy_base = legacy_workspace if legacy_folder_native else root

    manifest = {}
    manifest_path = legacy_base / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    project_brief_path = legacy_base / "project_brief.md"
    brief_text = project_brief_path.read_text(encoding="utf-8") if project_brief_path.exists() else ""
    title = _extract_bullet_field(brief_text, "Working title") or manifest.get("title") or root.name
    paper_type = _map_paper_type(_extract_bullet_field(brief_text, "Paper type"))
    citation_style = _extract_bullet_field(brief_text, "Citation style") or None
    output_mode = "formatted"
    if manifest.get("output_format") == "markdown":
        output_mode = "raw"

    init_workspace(
        root,
        title=title,
        paper_type=paper_type,
        output_mode=output_mode,
        citation_style=citation_style,
        formatting_profile=None,
        figure_mode="suggest_only",
        discipline="",
        deadline=_extract_bullet_field(brief_text, "Deadline"),
        run_mode=manifest.get("default_run_mode", "guided"),
        institution_override_path=None,
        word_target=None,
        counting_policy=None,
        force=True,
    )

    states = load_all_states(root)
    manuscript_state = states["manuscript"]
    sources_state = states["sources"]
    reviews_state = states["reviews"]

    draft_path = legacy_base / "draft.md"
    if draft_path.exists():
        section_map = _split_legacy_sections(draft_path.read_text(encoding="utf-8"))
        if section_map.get("Title"):
            manuscript_state["title"] = section_map["Title"].strip("[]") or title
        if section_map.get("Abstract"):
            manuscript_state["abstract"] = section_map["Abstract"]

        existing_sections = {section["id"]: section for section in manuscript_state["sections"]}
        for heading, body in section_map.items():
            if heading in {"preface", "Title", "Abstract", "References"}:
                continue
            section_id = _section_id(heading)
            if section_id in existing_sections:
                existing_sections[section_id]["content"] = body
            else:
                manuscript_state["sections"].append(
                    {
                        "id": section_id,
                        "title": heading,
                        "role": "section",
                        "required": False,
                        "target_words": 0,
                        "content": body,
                        "subsections": [],
                    }
                )

    bibliography_path = legacy_base / "bibliography.md"
    if bibliography_path.exists():
        bibliography_text = bibliography_path.read_text(encoding="utf-8").strip()
        if bibliography_text:
            sources_state["notes"].append(
                {
                    "id": "legacy-bibliography-import",
                    "kind": "raw_bibliography_text",
                    "text": bibliography_text,
                }
            )
            reviews_state["findings"].append(
                {
                    "severity": "warning",
                    "summary": "Legacy bibliography text imported as notes and requires normalization into verified source records before clean export.",
                }
            )

    save_state(root, "manuscript.json", manuscript_state)
    save_state(root, "sources.json", sources_state)
    save_state(root, "reviews.json", reviews_state)
    render_views(root)
    return root
