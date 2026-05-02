from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from docx import Document

from scientific_paper_writer.exporters import export_project
from scientific_paper_writer.workspace import init_workspace, load_all_states, save_state


class ExporterTests(unittest.TestCase):
    def _build_workspace_with_override(self, root: Path, override_path: Path) -> Path:
        init_workspace(
            root,
            title="Override Export Test",
            paper_type="short_conference",
            output_mode="formatted",
            citation_style="ieee",
            formatting_profile=None,
            figure_mode="suggest_only",
            discipline="Computer Science",
            deadline="",
            run_mode="guided",
            institution_override_path=str(override_path),
            word_target={
                "mode": "minimum_maximum",
                "minimum": 5,
                "maximum": 200,
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

        for section in manuscript["sections"]:
            section["content"] = ""

        first_section_id = manuscript["sections"][0]["id"]
        manuscript["sections"][0]["content"] = (
            "This export path preserves resolved institution formatting overrides [@smith2024]."
        )
        sources["sources"] = [
            {
                "id": "smith2024",
                "authors": [{"given": "Jane", "family": "Smith"}],
                "title": "Reliable Writing Systems",
                "year": "2024",
                "container_title": "Journal of Systems",
                "verified": True,
            }
        ]
        evidence["claims"] = [
            {
                "id": "claim-1",
                "section_id": first_section_id,
                "claim_text": "Resolved formatting should survive into export.",
                "source_ids": ["smith2024"],
                "support_strength": "strong",
            }
        ]

        save_state(root, "manuscript.json", manuscript)
        save_state(root, "sources.json", sources)
        save_state(root, "evidence.json", evidence)
        return root

    def test_export_backfills_and_uses_effective_formatting_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "override-project"
            root.mkdir(parents=True, exist_ok=True)
            override_path = root / "institution_override.json"
            override_path.write_text(
                json.dumps(
                    {
                        "formatting": {
                            "font_name": "Arial",
                            "font_size_pt": 11,
                            "line_spacing": 2.0,
                            "paragraph_indent_inches": 0.4,
                            "heading_numbering": True,
                            "margins_inches": {
                                "top": 1.2,
                                "right": 1.1,
                                "bottom": 1.2,
                                "left": 1.5,
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )

            self._build_workspace_with_override(root, override_path)

            states = load_all_states(root)
            project_state = states["project"]
            project_state["profile_resolution"].pop("effective_formatting", None)
            save_state(root, "project.json", project_state)

            outputs = export_project(root)

            saved_project = load_all_states(root)["project"]
            effective = saved_project["profile_resolution"]["effective_formatting"]
            self.assertEqual(effective["font_name"], "Arial")
            self.assertEqual(effective["font_size_pt"], 11)
            self.assertAlmostEqual(effective["margins_inches"]["left"], 1.5)

            document = Document(outputs["docx"])
            self.assertAlmostEqual(document.sections[0].left_margin.inches, 1.5, places=2)
            self.assertAlmostEqual(document.sections[0].right_margin.inches, 1.1, places=2)
            self.assertEqual(document.styles["Normal"].font.size.pt, 11.0)
            self.assertTrue(
                any(paragraph.text.startswith("1. ") for paragraph in document.paragraphs),
                "Expected numbered headings from the resolved override profile.",
            )


if __name__ == "__main__":
    unittest.main()
