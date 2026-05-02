from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path


def _load_runtime() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root / "src"))


def _copy_markdown_tree(source_dir: Path, target_dir: Path, force: bool) -> None:
    if not source_dir.exists():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for source_path in source_dir.glob("*.md"):
        target_path = target_dir / source_path.name
        if target_path.exists() and not force:
            continue
        target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")


def _render_template(path: Path, *, title: str, output_mode: str, slug: str) -> str:
    text = path.read_text(encoding="utf-8")
    return (
        text.replace("{{WORKING_TITLE}}", title)
        .replace("{{PROJECT_SLUG}}", slug)
        .replace("{{CREATED_ON}}", date.today().isoformat())
        .replace("{{OUTPUT_FORMAT}}", output_mode)
        .replace("{{OUTPUT_FILENAME}}", "deliverables/final_paper.md")
    )


def main() -> int:
    _load_runtime()
    from scientific_paper_writer.workspace import init_workspace, slugify

    parser = argparse.ArgumentParser(
        description="Bootstrap a folder-native scientific paper workspace."
    )
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--title", default="Working Title")
    parser.add_argument("--paper-type", default="empirical_imrad")
    parser.add_argument(
        "--output-mode",
        default="both",
        choices=["raw", "formatted", "both"],
    )
    parser.add_argument("--citation-style", default=None)
    parser.add_argument("--formatting-profile", default=None)
    parser.add_argument(
        "--figure-mode",
        default="suggest_only",
        choices=["off", "suggest_only", "auto"],
    )
    parser.add_argument(
        "--run-mode",
        default="guided",
        choices=["guided", "just_write_it"],
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    target_dir = Path(args.target).resolve()
    slug = slugify(target_dir.name or args.title)
    init_workspace(
        target_dir,
        title=args.title,
        paper_type=args.paper_type,
        output_mode=args.output_mode,
        citation_style=args.citation_style,
        formatting_profile=args.formatting_profile,
        figure_mode=args.figure_mode,
        discipline="",
        deadline="",
        run_mode=args.run_mode,
        institution_override_path=None,
        word_target=None,
        counting_policy=None,
        force=args.force,
    )

    templates_dir = repo_root / "templates"
    root_agents = target_dir / "AGENTS.md"
    if not root_agents.exists() or args.force:
        root_agents.write_text(
            _render_template(
                templates_dir / "folder_AGENTS.md",
                title=args.title,
                output_mode=args.output_mode,
                slug=slug,
            ),
            encoding="utf-8",
        )

    for source_name, target_name in [
        ("folder_system_prompt.md", "system_prompt.md"),
        ("folder_workflow.md", "workflow.md"),
    ]:
        target_path = target_dir / ".paper_writer" / target_name
        if target_path.exists() and not args.force:
            continue
        target_path.write_text(
            _render_template(
                templates_dir / source_name,
                title=args.title,
                output_mode=args.output_mode,
                slug=slug,
            ),
            encoding="utf-8",
        )

    _copy_markdown_tree(repo_root / "system" / "roles", target_dir / ".paper_writer" / "roles", args.force)
    _copy_markdown_tree(
        repo_root / "system" / "workflows",
        target_dir / ".paper_writer" / "workflows",
        args.force,
    )

    print(target_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
