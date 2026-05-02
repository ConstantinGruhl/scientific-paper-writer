from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _load_runtime() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root / "src"))


def main() -> int:
    _load_runtime()
    from scientific_paper_writer.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["init-project", *sys.argv[1:]])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
