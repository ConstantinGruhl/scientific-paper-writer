from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


TEMPLATE_FILES = [
    "project_brief.md",
    "project_context.md",
    "research_plan.md",
    "bibliography.md",
    "evidence_matrix.md",
    "outline.md",
    "draft.md",
    "revision_checklist.md",
    "agent_status.md",
]

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


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "paper-project"


def render_template(
    text: str,
    slug: str,
    title: str,
    created_on: str,
    output_format: str,
    output_name: str,
) -> str:
    return (
        text.replace("{{PROJECT_SLUG}}", slug)
        .replace("{{WORKING_TITLE}}", title)
        .replace("{{CREATED_ON}}", created_on)
        .replace("{{OUTPUT_FORMAT}}", output_format)
        .replace("{{OUTPUT_FILENAME}}", output_name)
    )


def write_if_needed(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.write_text(content, encoding="utf-8")


def build_agent_note(role: str) -> str:
    title = role.replace("_", " ").title()
    return (
        f"# {title} Notes\n\n"
        "- Current goal:\n"
        "- Current plan:\n"
        "- Decisions made:\n"
        "- Evidence needed next:\n"
        "- Handoff request:\n"
    )


def build_project(repo_root: Path, slug: str, title: str, force: bool) -> Path:
    templates_dir = repo_root / "templates"
    project_dir = repo_root / "projects" / slug
    created_on = dt.date.today().isoformat()
    output_format = "markdown"
    output_name = "deliverables/final_paper.md"

    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "sources").mkdir(exist_ok=True)
    (project_dir / "notes").mkdir(exist_ok=True)
    (project_dir / "deliverables").mkdir(exist_ok=True)

    for filename in TEMPLATE_FILES:
        template_path = templates_dir / filename
        target_path = project_dir / filename
        content = render_template(
            template_path.read_text(encoding="utf-8"),
            slug=slug,
            title=title,
            created_on=created_on,
            output_format=output_format,
            output_name=output_name,
        )
        write_if_needed(target_path, content, force)

    write_if_needed(
        project_dir / "sources" / "README.md",
        "# Sources\n\nCreate one file per source using `templates/source_note.md`.\n",
        force,
    )
    write_if_needed(
        project_dir / "notes" / "README.md",
        "# Notes\n\nUse this folder for working notes, excerpts, and scratch synthesis.\n",
        force,
    )
    write_if_needed(
        project_dir / "notes" / "handoffs.md",
        "# Handoffs\n\n| From | To | Request | Related Files | Unresolved Risk |\n| --- | --- | --- | --- | --- |\n",
        force,
    )
    for role in ROLE_NOTE_FILES:
        write_if_needed(project_dir / "notes" / f"{role}.md", build_agent_note(role), force)
    write_if_needed(
        project_dir / "deliverables" / "final_paper.md",
        "# Final Paper\n\n[Approved manuscript goes here]\n",
        force,
    )
    write_if_needed(
        project_dir / "agent_state.json",
        "{\n"
        '  "run_mode": "guided",\n'
        '  "active_stage": "not started",\n'
        '  "current_checkpoint": "not started"\n'
        "}\n",
        force,
    )

    return project_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a new scientific paper project scaffold."
    )
    parser.add_argument("slug", help="Project slug or title seed")
    parser.add_argument(
        "--title",
        help="Working title to write into the project files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scaffold files",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    slug = slugify(args.slug)
    title = args.title or args.slug
    project_dir = build_project(repo_root, slug=slug, title=title, force=args.force)

    print(project_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
