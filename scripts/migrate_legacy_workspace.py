from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _load_runtime() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root / "src"))


def main() -> int:
    _load_runtime()
    from scientific_paper_writer.migrate import migrate_legacy_workspace

    parser = argparse.ArgumentParser(
        description="Migrate a legacy markdown-first paper workspace to structured state."
    )
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    migrated = migrate_legacy_workspace(Path(args.target).resolve(), force=args.force)
    print(migrated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
