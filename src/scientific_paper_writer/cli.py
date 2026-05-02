from __future__ import annotations

import argparse
import json
from pathlib import Path

from .validation import scaffold_coverage_records, validate_project_state
from .workspace import init_workspace, load_all_states, render_views, save_state, slugify


def _word_target_from_args(args: argparse.Namespace) -> dict[str, int | str]:
    if args.exact_words:
        return {
            "mode": "exact",
            "exact_target": args.exact_words,
            "target": 0,
            "tolerance": 0,
            "minimum": 0,
            "maximum": 0,
        }
    if args.min_words or args.max_words:
        return {
            "mode": "minimum_maximum",
            "minimum": args.min_words or 0,
            "maximum": args.max_words or 0,
            "target": 0,
            "tolerance": 0,
            "exact_target": 0,
        }
    target = args.target_words or 5000
    tolerance = args.tolerance or max(100, int(target * 0.05))
    return {
        "mode": "target_tolerance",
        "target": target,
        "tolerance": tolerance,
        "minimum": 0,
        "maximum": 0,
        "exact_target": 0,
    }


def _bootstrap_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", default="Working Title")
    parser.add_argument(
        "--paper-type",
        default="empirical_imrad",
        choices=[
            "empirical_imrad",
            "literature_review",
            "theoretical_conceptual",
            "case_study",
            "thesis_chapter",
            "short_conference",
        ],
    )
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
    parser.add_argument("--discipline", default="")
    parser.add_argument("--deadline", default="")
    parser.add_argument("--institution-override", default=None)
    parser.add_argument(
        "--run-mode",
        default="guided",
        choices=["guided", "just_write_it"],
    )
    parser.add_argument("--target-words", type=int, default=None)
    parser.add_argument("--tolerance", type=int, default=None)
    parser.add_argument("--exact-words", type=int, default=None)
    parser.add_argument("--min-words", type=int, default=None)
    parser.add_argument("--max-words", type=int, default=None)
    parser.add_argument("--force", action="store_true")


def _cmd_bootstrap(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    init_workspace(
        target,
        title=args.title,
        paper_type=args.paper_type,
        output_mode=args.output_mode,
        citation_style=args.citation_style,
        formatting_profile=args.formatting_profile,
        figure_mode=args.figure_mode,
        discipline=args.discipline,
        deadline=args.deadline,
        run_mode=args.run_mode,
        institution_override_path=args.institution_override,
        word_target=_word_target_from_args(args),
        counting_policy=None,
        force=args.force,
    )
    print(target)
    return 0


def _cmd_init_project(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    slug = slugify(args.slug)
    target = repo_root / "projects" / slug
    init_workspace(
        target,
        title=args.title or args.slug,
        paper_type=args.paper_type,
        output_mode=args.output_mode,
        citation_style=args.citation_style,
        formatting_profile=args.formatting_profile,
        figure_mode=args.figure_mode,
        discipline=args.discipline,
        deadline=args.deadline,
        run_mode=args.run_mode,
        institution_override_path=args.institution_override,
        word_target=_word_target_from_args(args),
        counting_policy=None,
        force=args.force,
    )
    print(target)
    return 0


def _cmd_render_views(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    render_views(target)
    print(target)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    states = load_all_states(target)
    report = validate_project_state(
        states["project"],
        states["workflow"],
        states["manuscript"],
        states["sources"],
        states["evidence"],
    )
    exports_state = states["exports"]
    exports_state["last_validation"] = report
    save_state(target, "exports.json", exports_state)
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


def _cmd_scaffold_coverage(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    states = load_all_states(target)
    scaffold_report = scaffold_coverage_records(
        states["manuscript"],
        states["evidence"],
    )
    states["evidence"]["coverage"] = scaffold_report["coverage_records"]
    save_state(target, "evidence.json", states["evidence"])
    render_views(target)
    print(
        json.dumps(
            {
                "target": str(target),
                "reviewable_blocks": scaffold_report["reviewable_blocks"],
                "existing_blocks": scaffold_report["existing_blocks"],
                "created_count": scaffold_report["created_count"],
                "created_records": scaffold_report["created_records"],
            },
            indent=2,
        )
    )
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    from .exporters import export_project

    target = Path(args.target).resolve()
    outputs = export_project(target)
    print(json.dumps(outputs, indent=2))
    return 0


def _cmd_wordcount(args: argparse.Namespace) -> int:
    from .word_count import manuscript_word_report

    target = Path(args.target).resolve()
    states = load_all_states(target)
    report = manuscript_word_report(
        states["project"], states["manuscript"], states["sources"], states["evidence"]
    )
    print(json.dumps(report, indent=2))
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    states = load_all_states(target)
    summary = {
        "title": states["project"]["project"]["title"],
        "active_stage": states["workflow"]["active_stage"],
        "workflow_status": states["workflow"]["status"],
        "output_mode": states["project"]["output_mode"],
        "paper_type": states["project"]["profiles"]["paper_type"],
    }
    print(json.dumps(summary, indent=2))
    return 0


def _cmd_migrate(args: argparse.Namespace) -> int:
    from .migrate import migrate_legacy_workspace

    target = Path(args.target).resolve()
    migrated = migrate_legacy_workspace(target, force=args.force)
    print(migrated)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scientific Paper Writer CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser("bootstrap", help="Initialize a folder-native workspace")
    bootstrap_parser.add_argument("target", nargs="?", default=".")
    _bootstrap_common(bootstrap_parser)
    bootstrap_parser.set_defaults(func=_cmd_bootstrap)

    init_parser = subparsers.add_parser("init-project", help="Initialize a project under projects/")
    init_parser.add_argument("slug")
    init_parser.add_argument("--repo-root", default=".")
    _bootstrap_common(init_parser)
    init_parser.set_defaults(func=_cmd_init_project)

    render_parser = subparsers.add_parser("render-views", help="Render markdown views from structured state")
    render_parser.add_argument("target", nargs="?", default=".")
    render_parser.set_defaults(func=_cmd_render_views)

    validate_parser = subparsers.add_parser("validate", help="Run deterministic validation checks")
    validate_parser.add_argument("target", nargs="?", default=".")
    validate_parser.set_defaults(func=_cmd_validate)

    scaffold_parser = subparsers.add_parser(
        "scaffold-coverage",
        help="Add suggested coverage records for reviewable prose blocks",
    )
    scaffold_parser.add_argument("target", nargs="?", default=".")
    scaffold_parser.set_defaults(func=_cmd_scaffold_coverage)

    export_parser = subparsers.add_parser("export", help="Export raw text and/or formatted deliverables")
    export_parser.add_argument("target", nargs="?", default=".")
    export_parser.set_defaults(func=_cmd_export)

    wordcount_parser = subparsers.add_parser("wordcount", help="Generate a deterministic word-count report")
    wordcount_parser.add_argument("target", nargs="?", default=".")
    wordcount_parser.set_defaults(func=_cmd_wordcount)

    status_parser = subparsers.add_parser("status", help="Show current workflow status")
    status_parser.add_argument("target", nargs="?", default=".")
    status_parser.set_defaults(func=_cmd_status)

    migrate_parser = subparsers.add_parser("migrate", help="Migrate a legacy markdown-first workspace")
    migrate_parser.add_argument("target", nargs="?", default=".")
    migrate_parser.add_argument("--force", action="store_true")
    migrate_parser.set_defaults(func=_cmd_migrate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
