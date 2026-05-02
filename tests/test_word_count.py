from __future__ import annotations

import unittest

from scientific_paper_writer.word_count import (
    manuscript_word_report,
    section_budget_report,
    under_over_diagnostics,
    validate_target_policy,
)


class WordCountTests(unittest.TestCase):
    def _project_state(self, **policy_overrides: bool) -> dict[str, object]:
        counting_policy = {
            "include_title": False,
            "include_abstract": False,
            "include_headings": False,
            "include_figure_captions": False,
            "include_tables": False,
            "include_references": False,
            "include_appendices": False,
        }
        counting_policy.update(policy_overrides)
        return {
            "profiles": {"citation": "apa7"},
            "counting_policy": counting_policy,
            "word_target": {
                "mode": "target_tolerance",
                "target": 20,
                "tolerance": 5,
                "minimum": 0,
                "maximum": 0,
                "exact_target": 0,
            },
        }

    def _evidence_state(self) -> dict[str, object]:
        return {
            "claims": [],
            "figures": [{"id": "fig-1", "caption": "Figure caption words"}],
            "tables": [
                {
                    "id": "tbl-1",
                    "caption": "Table caption",
                    "columns": [
                        {"id": "topic", "label": "Topic"},
                        {"id": "score", "label": "Score"},
                    ],
                    "rows": [
                        {"topic": "Coverage", "score": "Strong"},
                    ],
                }
            ],
        }

    def test_nested_subsection_rollup_counts_each_level_once(self) -> None:
        manuscript_state = {
            "title": "",
            "abstract": "",
            "sections": [
                {
                    "id": "intro",
                    "title": "Intro",
                    "target_words": 5,
                    "content": "alpha beta",
                    "subsections": [
                        {
                            "id": "intro-sub",
                            "title": "Sub",
                            "target_words": 3,
                            "content": "gamma delta epsilon",
                            "subsections": [],
                        }
                    ],
                }
            ],
            "appendices": [],
        }

        report = manuscript_word_report(
            self._project_state(),
            manuscript_state,
            {"sources": []},
            self._evidence_state(),
        )

        top_section = report["sections"][0]
        self.assertEqual(top_section["included_words"], 5)
        self.assertEqual(top_section["bucket_counts"]["body"], 5)
        self.assertEqual(top_section["subsections"][0]["included_words"], 3)
        self.assertEqual(report["included_total"], 5)

    def test_multiple_nested_levels_roll_up_without_double_counting(self) -> None:
        manuscript_state = {
            "title": "",
            "abstract": "",
            "sections": [
                {
                    "id": "analysis",
                    "title": "Analysis",
                    "target_words": 6,
                    "content": "alpha",
                    "subsections": [
                        {
                            "id": "analysis-a",
                            "title": "Layer A",
                            "target_words": 4,
                            "content": "beta gamma",
                            "subsections": [
                                {
                                    "id": "analysis-b",
                                    "title": "Layer B",
                                    "target_words": 3,
                                    "content": "delta epsilon zeta",
                                    "subsections": [],
                                }
                            ],
                        }
                    ],
                }
            ],
            "appendices": [],
        }

        report = manuscript_word_report(
            self._project_state(),
            manuscript_state,
            {"sources": []},
            self._evidence_state(),
        )

        top_section = report["sections"][0]
        subsection = top_section["subsections"][0]
        subsubsection = subsection["subsections"][0]
        self.assertEqual(top_section["included_words"], 6)
        self.assertEqual(subsection["included_words"], 5)
        self.assertEqual(subsubsection["included_words"], 3)
        self.assertEqual(report["bucket_counts"]["body"], 6)
        self.assertEqual(report["included_total"], 6)

    def test_appendix_nesting_and_policy_exclusion_report_raw_totals_correctly(self) -> None:
        manuscript_state = {
            "title": "",
            "abstract": "",
            "sections": [],
            "appendices": [
                {
                    "id": "app-a",
                    "title": "Appendix A",
                    "target_words": 0,
                    "content": "appendix base",
                    "subsections": [
                        {
                            "id": "app-a-figure",
                            "title": "Figure Detail",
                            "target_words": 0,
                            "content": "[[FIGURE:fig-1]]",
                            "subsections": [
                                {
                                    "id": "app-a-table",
                                    "title": "Table Detail",
                                    "target_words": 0,
                                    "content": "[[TABLE:tbl-1]]",
                                    "subsections": [],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        report = manuscript_word_report(
            self._project_state(include_tables=True, include_figure_captions=True),
            manuscript_state,
            {"sources": []},
            self._evidence_state(),
        )

        appendix = report["sections"][0]
        self.assertEqual(appendix["included_words"], 0)
        self.assertEqual(appendix["excluded_words"], 17)
        self.assertEqual(appendix["total_words"], 17)
        self.assertEqual(report["bucket_counts"]["figure_captions"], 3)
        self.assertEqual(report["bucket_counts"]["tables"], 6)
        self.assertEqual(report["bucket_counts"]["appendices"], 17)
        self.assertEqual(report["excluded_total"], 17)

    def test_budget_report_flattens_nested_sections(self) -> None:
        manuscript_state = {
            "title": "",
            "abstract": "",
            "sections": [
                {
                    "id": "results",
                    "title": "Results",
                    "target_words": 10,
                    "required": True,
                    "content": "one two three four",
                    "subsections": [
                        {
                            "id": "results-a",
                            "title": "Results A",
                            "target_words": 5,
                            "required": True,
                            "content": "five six",
                            "subsections": [
                                {
                                    "id": "results-b",
                                    "title": "Results B",
                                    "target_words": 3,
                                    "required": True,
                                    "content": "seven",
                                    "subsections": [],
                                }
                            ],
                        }
                    ],
                }
            ],
            "appendices": [],
        }
        report = manuscript_word_report(
            self._project_state(),
            manuscript_state,
            {"sources": []},
            self._evidence_state(),
        )
        target_validation = validate_target_policy(self._project_state()["word_target"], report["included_total"])
        budget_rows = section_budget_report(manuscript_state, report)
        diagnostics = under_over_diagnostics(manuscript_state, report, target_validation)

        by_id = {row["id"]: row for row in budget_rows}
        self.assertEqual(by_id["results"]["actual_words"], 7)
        self.assertEqual(by_id["results-a"]["actual_words"], 3)
        self.assertEqual(by_id["results-b"]["actual_words"], 1)
        self.assertIn("Results", {row["title"] for row in diagnostics["underdeveloped_sections"]})

    def test_figure_caption_policy_toggles_included_and_excluded_totals(self) -> None:
        manuscript_state = {
            "title": "",
            "abstract": "",
            "sections": [
                {
                    "id": "figures",
                    "title": "Figures",
                    "target_words": 0,
                    "content": "[[FIGURE:fig-1]]",
                    "subsections": [],
                }
            ],
            "appendices": [],
        }

        excluded_report = manuscript_word_report(
            self._project_state(include_figure_captions=False),
            manuscript_state,
            {"sources": []},
            self._evidence_state(),
        )
        included_report = manuscript_word_report(
            self._project_state(include_figure_captions=True),
            manuscript_state,
            {"sources": []},
            self._evidence_state(),
        )

        self.assertEqual(excluded_report["bucket_counts"]["figure_captions"], 3)
        self.assertEqual(excluded_report["included_total"], 0)
        self.assertEqual(excluded_report["excluded_total"], 4)
        self.assertEqual(included_report["included_total"], 3)
        self.assertEqual(included_report["excluded_total"], 1)

    def test_table_policy_toggles_table_bucket_without_losing_body_counts(self) -> None:
        manuscript_state = {
            "title": "",
            "abstract": "",
            "sections": [
                {
                    "id": "mixed",
                    "title": "Mixed",
                    "target_words": 0,
                    "content": "body words here\n\n[[TABLE:tbl-1]]",
                    "subsections": [],
                }
            ],
            "appendices": [],
        }

        excluded_report = manuscript_word_report(
            self._project_state(include_tables=False),
            manuscript_state,
            {"sources": []},
            self._evidence_state(),
        )
        included_report = manuscript_word_report(
            self._project_state(include_tables=True),
            manuscript_state,
            {"sources": []},
            self._evidence_state(),
        )

        self.assertEqual(excluded_report["bucket_counts"]["body"], 3)
        self.assertEqual(excluded_report["bucket_counts"]["tables"], 6)
        self.assertEqual(excluded_report["included_total"], 3)
        self.assertEqual(excluded_report["excluded_total"], 7)
        self.assertEqual(included_report["included_total"], 9)
        self.assertEqual(included_report["excluded_total"], 1)


if __name__ == "__main__":
    unittest.main()
