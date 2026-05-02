from __future__ import annotations

import argparse
from pathlib import Path


ROLE_FILES = [
    ("Manager Role", "system/roles/manager.md"),
    ("Researcher Role", "system/roles/researcher.md"),
    ("Scientist Role", "system/roles/scientist.md"),
    ("Source Checker Role", "system/roles/source_checker.md"),
    ("Outliner Role", "system/roles/outliner.md"),
    ("Drafter Role", "system/roles/drafter.md"),
    ("Strict Reviewer Role", "system/roles/reviewer.md"),
    ("Style Proofreader Role", "system/roles/style_proofreader.md"),
    ("Progress Auditor Role", "system/roles/progress_auditor.md"),
]

WORKFLOW_FILES = [
    ("Workflow Index", "system/workflow.md"),
    ("Guided Workflow", "system/workflows/normal.md"),
    ("Just Write It Workflow", "system/workflows/just_write_it.md"),
]


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def add_section(parts: list[str], title: str, path: Path) -> None:
    if not path.exists():
        return
    parts.append(f"## {title}")
    parts.append(f"Source: {path.as_posix()}")
    parts.append("")
    parts.append(load_text(path))
    parts.append("")


def build_packet(repo_root: Path, slug: str) -> str:
    project_dir = repo_root / "projects" / slug
    parts: list[str] = [
        f"# Prompt Packet: {slug}",
        "",
        "Use this packet as the operating context for a scientific paper writing assistant.",
        "",
    ]

    add_section(parts, "Agent Instructions", repo_root / "AGENTS.md")
    add_section(parts, "System Prompt", repo_root / "system" / "system_prompt.md")
    add_section(parts, "Global Context", repo_root / "context.md")
    add_section(parts, "Project Context", project_dir / "project_context.md")
    add_section(parts, "Project Brief", project_dir / "project_brief.md")
    add_section(parts, "Research Plan", project_dir / "research_plan.md")
    add_section(parts, "Agent Status", project_dir / "agent_status.md")

    for title, relative_path in WORKFLOW_FILES:
        add_section(parts, title, repo_root / relative_path)

    for title, relative_path in ROLE_FILES:
        add_section(parts, title, repo_root / relative_path)

    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a portable prompt packet for a paper project."
    )
    parser.add_argument("slug", help="Project slug under projects/")
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the packet instead of writing prompt_packet.md",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    project_dir = repo_root / "projects" / args.slug
    if not project_dir.exists():
        raise SystemExit(f"Project not found: {project_dir}")

    packet = build_packet(repo_root, args.slug)

    if args.stdout:
        print(packet, end="")
        return 0

    output_path = project_dir / "prompt_packet.md"
    output_path.write_text(packet, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
