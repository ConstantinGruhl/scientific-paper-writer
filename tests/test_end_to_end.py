from __future__ import annotations

import json
import tempfile
import unittest
from builtins import __import__ as builtin_import
from pathlib import Path
from unittest.mock import patch

from docx import Document

from scientific_paper_writer.exporters import export_project
from scientific_paper_writer.validation import validate_project_state
from scientific_paper_writer.workspace import init_workspace, load_all_states, render_views, save_state


PNG_FIXTURE_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x04\x00\x00\x00\xb5\x1c\x0c\x02\x00\x00\x00\x0bIDATx\xdac\xfc"
    b"\xff\x1f\x00\x03\x03\x02\x00\xee~\xbb\xc9\x00\x00\x00\x00IEND\xaeB`\x82"
)


class EndToEndTests(unittest.TestCase):
    def _build_valid_workspace(self, root: Path) -> Path:
        init_workspace(
            root,
            title="Workflow Reliability",
            paper_type="short_conference",
            output_mode="both",
            citation_style="ieee",
            formatting_profile=None,
            figure_mode="auto",
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
        sources = states["sources"]
        evidence = states["evidence"]
        section_ids = [section["id"] for section in manuscript["sections"]]

        image_path = root / "workflow.png"
        image_path.write_bytes(PNG_FIXTURE_BYTES)

        manuscript["abstract"] = "This paper summarizes a reliable academic workflow [@smith2024]."
        manuscript["sections"][0]["content"] = (
            "Scientific writing systems fail when workflow guarantees live only in prompts [@smith2024].\n\n"
            "[[FIGURE:workflow-diagram]]"
        )
        manuscript["sections"][1]["content"] = "Prior work shows that traceable evidence improves revision quality [@smith2024]."
        manuscript["sections"][2]["content"] = (
            "We use a structured state model and deterministic validation to keep the workflow inspectable.\n\n"
            "[[TABLE:validation-checks]]"
        )
        manuscript["sections"][3]["content"] = "The redesigned pipeline exports clean DOCX and PDF deliverables for human review."
        manuscript["sections"][4]["content"] = "Structured state reduces ambiguity and makes quality measurable across revisions."

        sources["sources"] = [
            {
                "id": "smith2024",
                "authors": [{"given": "Jane", "family": "Smith"}],
                "title": "Reliable Writing Systems",
                "year": "2024",
                "container_title": "Journal of Systems",
                "volume": "12",
                "issue": "3",
                "pages": "44-60",
                "doi": "https://doi.org/10.1234/example",
                "verified": True,
            }
        ]
        evidence["claims"] = [
            {
                "id": "claim-1",
                "section_id": section_ids[0],
                "claim_text": "Workflow guarantees should be enforced by code.",
                "source_ids": ["smith2024"],
                "support_strength": "strong",
            }
        ]
        evidence["figures"] = [
            {
                "id": "workflow-diagram",
                "title": "Workflow Diagram",
                "caption": "Figure 1. Structured workflow state and export pipeline.",
                "path": str(image_path),
                "kind": "conceptual_diagram",
            }
        ]
        evidence["tables"] = [
            {
                "id": "validation-checks",
                "caption": "Table 1. Validation checks covered by deterministic export gates.",
                "columns": [
                    {"id": "check", "label": "Check"},
                    {"id": "status", "label": "Status"},
                ],
                "rows": [
                    {"check": "Coverage records", "status": "Enabled"},
                    {"check": "Profile overrides", "status": "Persisted"},
                ],
            }
        ]
        evidence["coverage"] = [
            {
                "block_id": f"{section_ids[2]}#block-0",
                "kind": "method_note",
                "claim_ids": [],
                "source_ids": [],
                "note": "Repository-internal method description for the test workspace.",
            },
            {
                "block_id": f"{section_ids[3]}#block-0",
                "kind": "uncited_ok",
                "claim_ids": [],
                "source_ids": [],
                "note": "Export smoke-test summary sentence.",
            },
            {
                "block_id": f"{section_ids[4]}#block-0",
                "kind": "uncited_ok",
                "claim_ids": [],
                "source_ids": [],
                "note": "Closing synthesis sentence for end-to-end validation.",
            },
        ]

        save_state(root, "manuscript.json", manuscript)
        save_state(root, "sources.json", sources)
        save_state(root, "evidence.json", evidence)
        render_views(root)
        return root

    def test_export_pipeline_generates_clean_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "sample-project"
            root.mkdir(parents=True, exist_ok=True)

            def guarded_import(
                name: str,
                globals: dict[str, object] | None = None,
                locals: dict[str, object] | None = None,
                fromlist: tuple[str, ...] = (),
                level: int = 0,
            ) -> object:
                if name == "PIL" or name.startswith("PIL."):
                    raise ImportError("Pillow should not be required for end-to-end export tests.")
                return builtin_import(name, globals, locals, fromlist, level)

            with patch("builtins.__import__", side_effect=guarded_import):
                self._build_valid_workspace(root)

                states = load_all_states(root)
                validation = validate_project_state(
                    states["project"],
                    states["workflow"],
                    states["manuscript"],
                    states["sources"],
                    states["evidence"],
                )
                self.assertTrue(validation["valid"], json.dumps(validation, indent=2))

                outputs = export_project(root)
                self.assertTrue(Path(outputs["raw_text"]).exists())
                self.assertTrue(Path(outputs["docx"]).exists())
                self.assertTrue(Path(outputs["pdf"]).exists())
                self.assertGreater(Path(outputs["pdf"]).stat().st_size, 0)

                raw_text = Path(outputs["raw_text"]).read_text(encoding="utf-8")
                self.assertNotIn("[TODO:", raw_text)
                self.assertNotIn("[[FIGURE:", raw_text)
                self.assertNotIn("[[TABLE:", raw_text)
                self.assertIn("Table 1. Validation checks covered by deterministic export gates.", raw_text)

                document = Document(outputs["docx"])
                joined = "\n".join(paragraph.text for paragraph in document.paragraphs)
                self.assertIn("Workflow Reliability", joined)
                self.assertIn("Figure 1. Structured workflow state and export pipeline.", joined)
                self.assertIn("Table 1. Validation checks covered by deterministic export gates.", joined)
                self.assertNotIn("[@smith2024]", joined)
                self.assertNotIn("[[FIGURE:workflow-diagram]]", joined)
                self.assertNotIn("[[TABLE:validation-checks]]", joined)
                self.assertNotIn("TODO", joined)


if __name__ == "__main__":
    unittest.main()
