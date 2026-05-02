from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


ROOT_FILES = {
    "AGENTS.md": "folder_AGENTS.md",
}

WORKSPACE_FILES = {
    "system_prompt.md": "folder_system_prompt.md",
    "workflow.md": "folder_workflow.md",
    "project_brief.md": "project_brief.md",
    "project_context.md": "project_context.md",
    "research_plan.md": "research_plan.md",
    "bibliography.md": "bibliography.md",
    "evidence_matrix.md": "evidence_matrix.md",
    "outline.md": "outline.md",
    "draft.md": "draft.md",
    "revision_checklist.md": "revision_checklist.md",
    "agent_status.md": "agent_status.md",
}

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


def render_template(text: str, slug: str, title: str, created_on: str, output_name: str, output_format: str) -> str:
    return (
        text.replace("{{PROJECT_SLUG}}", slug)
        .replace("{{WORKING_TITLE}}", title)
        .replace("{{CREATED_ON}}", created_on)
        .replace("{{OUTPUT_FILENAME}}", output_name)
        .replace("{{OUTPUT_FORMAT}}", output_format)
    )


def write_if_needed(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.write_text(content, encoding="utf-8")


def copy_markdown_tree(source_dir: Path, target_dir: Path, force: bool) -> None:
    if not source_dir.exists():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for source_path in source_dir.glob("*.md"):
        write_if_needed(
            target_dir / source_path.name,
            source_path.read_text(encoding="utf-8"),
            force,
        )


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


def bootstrap(target_dir: Path, title: str, output_format: str, force: bool) -> Path:
    repo_root = Path(__file__).resolve().parent.parent
    templates_dir = repo_root / "templates"
    slug = slugify(target_dir.name or title)
    created_on = dt.date.today().isoformat()
    output_name = f"paper.{ 'tex' if output_format == 'latex' else 'docx' }"

    target_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir = target_dir / ".paper_writer"
    sources_dir = workspace_dir / "sources"
    notes_dir = workspace_dir / "notes"
    roles_dir = workspace_dir / "roles"
    workflows_dir = workspace_dir / "workflows"
    research_instruments_dir = workspace_dir / "research_instruments"
    workspace_dir.mkdir(exist_ok=True)
    sources_dir.mkdir(exist_ok=True)
    notes_dir.mkdir(exist_ok=True)
    research_instruments_dir.mkdir(exist_ok=True)

    for root_name, template_name in ROOT_FILES.items():
        template_path = templates_dir / template_name
        content = render_template(
            template_path.read_text(encoding="utf-8"),
            slug=slug,
            title=title,
            created_on=created_on,
            output_name=output_name,
            output_format=output_format,
        )
        write_if_needed(target_dir / root_name, content, force)

    for target_name, template_name in WORKSPACE_FILES.items():
        template_path = templates_dir / template_name
        content = render_template(
            template_path.read_text(encoding="utf-8"),
            slug=slug,
            title=title,
            created_on=created_on,
            output_name=output_name,
            output_format=output_format,
        )
        write_if_needed(workspace_dir / target_name, content, force)

    copy_markdown_tree(repo_root / "system" / "roles", roles_dir, force)
    copy_markdown_tree(repo_root / "system" / "workflows", workflows_dir, force)

    write_if_needed(
        workspace_dir / "final_paper.md",
        "# Final Paper\n\n[Approved manuscript goes here]\n",
        force,
    )
    write_if_needed(
        sources_dir / "README.md",
        "# Sources\n\nCreate one file per source using the source note structure.\n",
        force,
    )
    write_if_needed(
        notes_dir / "README.md",
        "# Notes\n\nUse this folder for scratch synthesis and working notes.\n",
        force,
    )
    write_if_needed(
        notes_dir / "handoffs.md",
        "# Handoffs\n\n| From | To | Request | Related Files | Unresolved Risk |\n| --- | --- | --- | --- | --- |\n",
        force,
    )
    for role in ROLE_NOTE_FILES:
        write_if_needed(notes_dir / f"{role}.md", build_agent_note(role), force)
    write_if_needed(
        research_instruments_dir / "README.md",
        "# Research Instruments\n\nUse this folder for interview guides, surveys, protocols, coding frames, and other method-specific assets.\n",
        force,
    )
    write_if_needed(
        workspace_dir / "agent_state.json",
        json.dumps(
            {
                "run_mode": "guided",
                "active_stage": "not started",
                "current_checkpoint": "not started",
                "roles": {
                    role: {
                        "status": "idle",
                        "current_task": "awaiting assignment",
                        "files": [],
                        "blocker": "",
                        "evidence_state": "mixed",
                    }
                    for role in ROLE_NOTE_FILES
                },
            },
            indent=2,
        )
        + "\n",
        force,
    )

    manifest = {
        "title": title,
        "slug": slug,
        "created_on": created_on,
        "output_format": output_format,
        "output_file": output_name,
        "default_run_mode": "guided",
    }
    write_if_needed(
        workspace_dir / "manifest.json",
        json.dumps(manifest, indent=2) + "\n",
        force,
    )

    return target_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap a folder-native scientific paper workspace."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target folder to bootstrap",
    )
    parser.add_argument(
        "--title",
        default="Working Title",
        help="Working title for the paper",
    )
    parser.add_argument(
        "--output",
        choices=["latex", "docx"],
        default="docx",
        help="Final output format",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scaffold files",
    )
    args = parser.parse_args()

    target_dir = Path(args.target).resolve()
    bootstrap(target_dir, title=args.title, output_format=args.output, force=args.force)
    print(target_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
