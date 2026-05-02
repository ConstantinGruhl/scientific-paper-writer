from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scientific_paper_writer.cli import main
from scientific_paper_writer.workspace import init_workspace, load_all_states, save_state


class CoverageScaffoldCliTests(unittest.TestCase):
    def _build_workspace(self, root: Path) -> list[str]:
        init_workspace(
            root,
            title="Coverage Scaffold Test",
            paper_type="short_conference",
            output_mode="raw",
            citation_style="ieee",
            formatting_profile=None,
            figure_mode="suggest_only",
            discipline="Computer Science",
            deadline="",
            run_mode="guided",
            institution_override_path=None,
            word_target={
                "mode": "minimum_maximum",
                "minimum": 20,
                "maximum": 400,
                "target": 0,
                "tolerance": 0,
                "exact_target": 0,
            },
            counting_policy=None,
            force=True,
        )

        states = load_all_states(root)
        manuscript = states["manuscript"]
        evidence = states["evidence"]

        for section in manuscript["sections"]:
            section["content"] = ""

        section_ids = [section["id"] for section in manuscript["sections"]]
        manuscript["sections"][0]["content"] = (
            "Prior work frames reliable workflows as inspectable systems [@smith2024]."
        )
        manuscript["sections"][1]["content"] = (
            "We use a structured workflow and deterministic validation to keep the export pipeline inspectable."
        )
        manuscript["sections"][2]["content"] = (
            "This paragraph argues that explicit evidence state reduces ambiguity across revisions "
            "and improves review quality for academic teams."
        )
        manuscript["sections"][3]["content"] = (
            "This concluding synthesis is already classified for review."
        )
        evidence["coverage"] = [
            {
                "block_id": f"{section_ids[3]}#block-0",
                "status": "confirmed",
                "kind": "uncited_ok",
                "claim_ids": [],
                "source_ids": [],
                "note": "Manually reviewed summary sentence.",
            }
        ]

        save_state(root, "manuscript.json", manuscript)
        save_state(root, "evidence.json", evidence)
        return section_ids

    def _run_cli(self, *args: str) -> tuple[int, dict[str, object]]:
        buffer = io.StringIO()
        with patch.object(sys, "argv", ["spw", *args]), contextlib.redirect_stdout(buffer):
            exit_code = main()
        return exit_code, json.loads(buffer.getvalue())

    def test_scaffold_coverage_creates_suggested_records_and_preserves_existing_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "coverage-project"
            root.mkdir(parents=True, exist_ok=True)
            section_ids = self._build_workspace(root)

            exit_code, report = self._run_cli("scaffold-coverage", str(root))

            self.assertEqual(exit_code, 0)
            self.assertEqual(report["created_count"], 3)
            self.assertEqual(report["existing_blocks"], 1)
            self.assertEqual(report["reviewable_blocks"], 4)

            created_by_block = {
                record["block_id"]: record for record in report["created_records"]
            }
            self.assertEqual(
                created_by_block[f"{section_ids[0]}#block-0"]["kind"],
                "background",
            )
            self.assertEqual(
                created_by_block[f"{section_ids[1]}#block-0"]["kind"],
                "method_note",
            )
            self.assertEqual(
                created_by_block[f"{section_ids[2]}#block-0"]["kind"],
                "claim",
            )
            self.assertTrue(
                all(record["status"] == "suggested" for record in report["created_records"])
            )

            states = load_all_states(root)
            saved_coverage = states["evidence"]["coverage"]
            self.assertEqual(len(saved_coverage), 4)
            preserved_record = next(
                record
                for record in saved_coverage
                if record["block_id"] == f"{section_ids[3]}#block-0"
            )
            self.assertEqual(preserved_record["status"], "confirmed")
            self.assertEqual(
                preserved_record["note"],
                "Manually reviewed summary sentence.",
            )

            evidence_matrix = (root / "evidence_matrix.md").read_text(encoding="utf-8")
            self.assertIn(
                "| Block ID | Status | Kind | Claims | Sources | Note |",
                evidence_matrix,
            )
            self.assertIn("Suggested records are review prompts only", evidence_matrix)

    def test_scaffold_coverage_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "coverage-project"
            root.mkdir(parents=True, exist_ok=True)
            self._build_workspace(root)

            first_exit_code, first_report = self._run_cli("scaffold-coverage", str(root))
            first_records = load_all_states(root)["evidence"]["coverage"]
            second_exit_code, second_report = self._run_cli("scaffold-coverage", str(root))
            second_records = load_all_states(root)["evidence"]["coverage"]

            self.assertEqual(first_exit_code, 0)
            self.assertEqual(second_exit_code, 0)
            self.assertEqual(first_report["created_count"], 3)
            self.assertEqual(second_report["created_count"], 0)
            self.assertEqual(second_report["existing_blocks"], 4)
            self.assertEqual(first_records, second_records)


if __name__ == "__main__":
    unittest.main()
