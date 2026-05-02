from __future__ import annotations

import unittest

from scientific_paper_writer.validation import (
    artifact_findings,
    scaffold_coverage_records,
    validate_project_state,
)


class ValidationTests(unittest.TestCase):
    def _project_state(self) -> dict[str, object]:
        return {
            "profiles": {"citation": "apa7"},
            "counting_policy": {
                "include_title": False,
                "include_abstract": False,
                "include_headings": False,
                "include_figure_captions": False,
                "include_tables": False,
                "include_references": False,
                "include_appendices": False,
            },
            "word_target": {
                "mode": "minimum_maximum",
                "minimum": 1,
                "maximum": 200,
                "target": 0,
                "tolerance": 0,
                "exact_target": 0,
            },
        }

    def _workflow_state(self) -> dict[str, object]:
        return {"active_stage": "review", "status": "in_progress", "stages": {}}

    def test_artifact_detection_flags_todos_and_missing_figure_markers(self) -> None:
        manuscript_state = {
            "abstract": "",
            "sections": [
                {
                    "id": "intro",
                    "title": "Introduction",
                    "content": "Claim here. [TODO: evidence]\n\n[[FIGURE:missing-figure]]",
                    "subsections": [],
                }
            ],
            "appendices": [],
        }
        findings = artifact_findings(manuscript_state, {"figures": [], "tables": []})
        labels = {finding["label"] for finding in findings}
        self.assertIn("Unresolved evidence placeholder", labels)
        self.assertIn("Unresolved figure marker", labels)

    def test_resolved_figure_marker_is_not_flagged(self) -> None:
        manuscript_state = {
            "abstract": "",
            "sections": [
                {
                    "id": "intro",
                    "title": "Introduction",
                    "content": "See the workflow.\n\n[[FIGURE:workflow]]",
                    "subsections": [],
                }
            ],
            "appendices": [],
        }
        findings = artifact_findings(
            manuscript_state,
            {"figures": [{"id": "workflow", "caption": "Workflow"}], "tables": []},
        )
        labels = {finding["label"] for finding in findings}
        self.assertNotIn("Unresolved figure marker", labels)

    def test_validation_reports_missing_evidence_links(self) -> None:
        manuscript_state = {
            "title": "Validation Test",
            "abstract": "",
            "sections": [
                {
                    "id": "intro",
                    "title": "Introduction",
                    "content": "A claim without evidence.",
                    "subsections": [],
                }
            ],
            "appendices": [],
        }
        report = validate_project_state(
            self._project_state(),
            self._workflow_state(),
            manuscript_state,
            {"sources": []},
            {"claims": [], "figures": [], "tables": [], "coverage": []},
        )
        labels = {finding["label"] for finding in report["findings"]}
        self.assertIn("No claims are linked to evidence", labels)

    def test_validation_flags_uncovered_argumentative_prose(self) -> None:
        manuscript_state = {
            "title": "Coverage Test",
            "abstract": "",
            "sections": [
                {
                    "id": "analysis",
                    "title": "Analysis",
                    "content": (
                        "This paragraph makes a substantial argument about workflow reliability "
                        "without any citation or explicit evidence coverage mapping at all."
                    ),
                    "subsections": [],
                }
            ],
            "appendices": [],
        }
        report = validate_project_state(
            self._project_state(),
            self._workflow_state(),
            manuscript_state,
            {"sources": []},
            {"claims": [], "figures": [], "tables": [], "coverage": []},
        )

        labels = [finding["label"] for finding in report["findings"]]
        self.assertIn(
            "Substantial argumentative prose lacks evidence coverage classification",
            labels,
        )
        self.assertFalse(report["valid"])
        self.assertEqual(report["coverage_report"]["reviewable_blocks"], 1)
        self.assertEqual(len(report["coverage_report"]["uncovered_blocks"]), 1)

    def test_validation_treats_missing_status_as_confirmed(self) -> None:
        manuscript_state = {
            "title": "Coverage Test",
            "abstract": "",
            "sections": [
                {
                    "id": "analysis",
                    "title": "Analysis",
                    "content": (
                        "This paragraph makes a substantial argument about workflow reliability "
                        "and it is explicitly linked to an evidence-backed claim."
                    ),
                    "subsections": [],
                }
            ],
            "appendices": [],
        }
        sources_state = {
            "sources": [
                {
                    "id": "smith2024",
                    "authors": [{"given": "Jane", "family": "Smith"}],
                    "title": "Reliable Writing Systems",
                    "year": "2024",
                    "container_title": "Journal of Systems",
                    "verified": True,
                }
            ]
        }
        evidence_state = {
            "claims": [
                {
                    "id": "claim-1",
                    "section_id": "analysis",
                    "claim_text": "Workflow reliability improves when evidence links are explicit.",
                    "source_ids": ["smith2024"],
                    "support_strength": "strong",
                }
            ],
            "figures": [],
            "tables": [],
            "coverage": [
                {
                    "block_id": "analysis#block-0",
                    "kind": "claim",
                    "claim_ids": ["claim-1"],
                    "source_ids": [],
                    "note": "",
                }
            ],
        }

        report = validate_project_state(
            self._project_state(),
            self._workflow_state(),
            manuscript_state,
            sources_state,
            evidence_state,
        )

        self.assertTrue(report["valid"], report["findings"])
        self.assertEqual(report["coverage_report"]["covered_blocks"], 1)
        self.assertEqual(report["coverage_report"]["uncovered_blocks"], [])

    def test_validation_accepts_confirmed_paragraph_coverage(self) -> None:
        manuscript_state = {
            "title": "Coverage Test",
            "abstract": "",
            "sections": [
                {
                    "id": "analysis",
                    "title": "Analysis",
                    "content": (
                        "This paragraph makes a substantial argument about workflow reliability "
                        "and it is explicitly linked to an evidence-backed claim."
                    ),
                    "subsections": [],
                }
            ],
            "appendices": [],
        }
        sources_state = {
            "sources": [
                {
                    "id": "smith2024",
                    "authors": [{"given": "Jane", "family": "Smith"}],
                    "title": "Reliable Writing Systems",
                    "year": "2024",
                    "container_title": "Journal of Systems",
                    "verified": True,
                }
            ]
        }
        evidence_state = {
            "claims": [
                {
                    "id": "claim-1",
                    "section_id": "analysis",
                    "claim_text": "Workflow reliability improves when evidence links are explicit.",
                    "source_ids": ["smith2024"],
                    "support_strength": "strong",
                }
            ],
            "figures": [],
            "tables": [],
            "coverage": [
                {
                    "block_id": "analysis#block-0",
                    "status": "confirmed",
                    "kind": "claim",
                    "claim_ids": ["claim-1"],
                    "source_ids": [],
                    "note": "",
                }
            ],
        }

        report = validate_project_state(
            self._project_state(),
            self._workflow_state(),
            manuscript_state,
            sources_state,
            evidence_state,
        )

        self.assertTrue(report["valid"], report["findings"])
        self.assertEqual(report["coverage_report"]["covered_blocks"], 1)
        self.assertEqual(report["coverage_report"]["uncovered_blocks"], [])

    def test_suggested_coverage_does_not_satisfy_export_readiness(self) -> None:
        manuscript_state = {
            "title": "Coverage Test",
            "abstract": "",
            "sections": [
                {
                    "id": "analysis",
                    "title": "Analysis",
                    "content": (
                        "This paragraph argues that explicit evidence coverage is still needed "
                        "before a deterministic export gate should pass."
                    ),
                    "subsections": [],
                }
            ],
            "appendices": [],
        }
        sources_state = {
            "sources": [
                {
                    "id": "smith2024",
                    "authors": [{"given": "Jane", "family": "Smith"}],
                    "title": "Reliable Writing Systems",
                    "year": "2024",
                    "container_title": "Journal of Systems",
                    "verified": True,
                }
            ]
        }
        evidence_state = {
            "claims": [
                {
                    "id": "claim-1",
                    "section_id": "analysis",
                    "claim_text": "Explicit evidence coverage should remain a release gate.",
                    "source_ids": ["smith2024"],
                    "support_strength": "strong",
                }
            ],
            "figures": [],
            "tables": [],
            "coverage": [],
        }
        evidence_state["coverage"] = scaffold_coverage_records(
            manuscript_state,
            evidence_state,
        )["coverage_records"]

        report = validate_project_state(
            self._project_state(),
            self._workflow_state(),
            manuscript_state,
            sources_state,
            evidence_state,
        )

        labels = [finding["label"] for finding in report["findings"]]
        self.assertIn(
            "Substantial argumentative prose lacks evidence coverage classification",
            labels,
        )
        self.assertFalse(report["valid"])
        self.assertEqual(
            report["coverage_report"]["blocks"][0]["classification"],
            "suggested_claim",
        )
        self.assertFalse(report["coverage_report"]["blocks"][0]["covered"])


if __name__ == "__main__":
    unittest.main()
