from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _add_section(parts: list[str], title: str, path: Path) -> None:
    if not path.exists():
        return
    parts.append(f"## {title}")
    parts.append(f"Source: {path.as_posix()}")
    parts.append("")
    parts.append(_load_text(path))
    parts.append("")


def build_packet(repo_root: Path, slug: str) -> str:
    project_root = repo_root / "projects" / slug
    state_root = project_root / ".paper_writer" / "state"
    parts = [
        f"# Prompt Packet: {slug}",
        "",
        "Use this packet as the operating context for a scientific paper writing assistant.",
        "",
    ]

    for title, relative_path in [
        ("Agent Instructions", "AGENTS.md"),
        ("System Prompt", "system/system_prompt.md"),
        ("Global Context", "context.md"),
    ]:
        _add_section(parts, title, repo_root / relative_path)

    for view_name in [
        "project_context.md",
        "project_brief.md",
        "research_plan.md",
        "agent_status.md",
        "outline.md",
        "draft.md",
    ]:
        _add_section(parts, view_name.replace(".md", "").replace("_", " ").title(), project_root / view_name)

    if state_root.exists():
        for state_file in [
            "project.json",
            "workflow.json",
            "manuscript.json",
            "sources.json",
            "evidence.json",
        ]:
            path = state_root / state_file
            if not path.exists():
                continue
            parts.append(f"## Structured State: {state_file}")
            parts.append(f"Source: {path.as_posix()}")
            parts.append("")
            parts.append(json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2))
            parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a portable prompt packet for a paper project."
    )
    parser.add_argument("slug", help="Project slug under projects/")
    parser.add_argument("--stdout", action="store_true")
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
