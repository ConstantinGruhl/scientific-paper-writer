from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scientific_paper_writer.migrate import migrate_legacy_workspace
from scientific_paper_writer.workspace import load_all_states


class MigrationTests(unittest.TestCase):
    def test_migrate_handles_empty_legacy_brief_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "legacy-paper"
            root.mkdir(parents=True, exist_ok=True)
            (root / "project_brief.md").write_text(
                "# Project Brief\n\n"
                "## Project Identity\n\n"
                "- Working title: Legacy Paper\n"
                "- Project slug: legacy-paper\n\n"
                "## Core Inputs\n\n"
                "- Paper type:\n"
                "- Citation style:\n",
                encoding="utf-8",
            )
            (root / "draft.md").write_text(
                "# Draft\n\n"
                "## Title\n\n"
                "Legacy Paper\n\n"
                "## Abstract\n\n"
                "Short abstract.\n\n"
                "## Introduction\n\n"
                "Legacy draft text.\n",
                encoding="utf-8",
            )

            migrate_legacy_workspace(root, force=True)
            states = load_all_states(root)

            self.assertEqual(states["project"]["project"]["title"], "Legacy Paper")
            self.assertEqual(states["project"]["profiles"]["paper_type"], "empirical_imrad")
            self.assertTrue((root / ".paper_writer" / "state" / "project.json").exists())


if __name__ == "__main__":
    unittest.main()
