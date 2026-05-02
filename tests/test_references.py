from __future__ import annotations

import unittest

from scientific_paper_writer.references import (
    format_reference,
    normalize_source,
    render_inline_citations,
)


class ReferenceFormattingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = normalize_source(
            {
                "id": "smith2024",
                "authors": ["Jane Smith", "Alan Lee"],
                "title": "Reliable Writing Systems",
                "year": "2024",
                "container_title": "Journal of Systems",
                "volume": "12",
                "issue": "3",
                "pages": "44-60",
                "doi": "https://doi.org/10.1234/example",
                "verified": True,
            }
        )

    def test_reference_formatting_apa_and_ieee(self) -> None:
        apa = format_reference(self.source, "apa7")
        ieee = format_reference(self.source, "ieee", ordinal=1)

        self.assertIn("Smith, J.", apa)
        self.assertIn("(2024).", apa)
        self.assertIn("[1]", ieee)
        self.assertIn('"Reliable Writing Systems,"', ieee)

    def test_inline_citation_rendering_replaces_tokens(self) -> None:
        sources = {"smith2024": self.source}
        rendered_apa = render_inline_citations(
            "Evidence matters [@smith2024].",
            sources,
            "apa7",
            {"smith2024": 1},
        )
        rendered_ieee = render_inline_citations(
            "Evidence matters [@smith2024].",
            sources,
            "ieee",
            {"smith2024": 1},
        )

        self.assertEqual(rendered_apa, "Evidence matters (Smith & Lee, 2024).")
        self.assertEqual(rendered_ieee, "Evidence matters [1].")


if __name__ == "__main__":
    unittest.main()
