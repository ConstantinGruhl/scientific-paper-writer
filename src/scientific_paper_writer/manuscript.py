from __future__ import annotations

import re
from typing import Any

from .references import render_inline_citations


FIGURE_MARKER_RE = re.compile(r"^\[\[FIGURE:([a-zA-Z0-9._-]+)\]\]$")
TABLE_MARKER_RE = re.compile(r"^\[\[TABLE:([a-zA-Z0-9._-]+)\]\]$")


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_markdown_blocks(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    paragraph: list[str] = []
    unordered_items: list[str] = []
    ordered_items: list[str] = []

    def flush_lists() -> None:
        nonlocal unordered_items, ordered_items
        if unordered_items:
            blocks.append({"kind": "bullet_list", "items": unordered_items})
            unordered_items = []
        if ordered_items:
            blocks.append({"kind": "ordered_list", "items": ordered_items})
            ordered_items = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append({"kind": "paragraph", "text": " ".join(paragraph).strip()})
            paragraph = []

    for raw_line in normalize_text(text).split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_lists()
            continue

        figure_match = FIGURE_MARKER_RE.match(stripped)
        if figure_match:
            flush_paragraph()
            flush_lists()
            blocks.append({"kind": "figure", "figure_id": figure_match.group(1)})
            continue

        table_match = TABLE_MARKER_RE.match(stripped)
        if table_match:
            flush_paragraph()
            flush_lists()
            blocks.append({"kind": "table", "table_id": table_match.group(1)})
            continue

        unordered_match = re.match(r"^[-*]\s+(.*)$", stripped)
        if unordered_match:
            flush_paragraph()
            if ordered_items:
                flush_lists()
            unordered_items.append(unordered_match.group(1).strip())
            continue

        ordered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if ordered_match:
            flush_paragraph()
            if unordered_items:
                flush_lists()
            ordered_items.append(ordered_match.group(1).strip())
            continue

        flush_lists()
        paragraph.append(stripped)

    flush_paragraph()
    flush_lists()
    return blocks


def block_plain_text(block: dict[str, Any]) -> str:
    kind = block["kind"]
    if kind == "paragraph":
        return block["text"]
    if kind in {"bullet_list", "ordered_list"}:
        return " ".join(block["items"])
    return ""


def render_section_text(
    section: dict[str, Any],
    sources_by_id: dict[str, dict[str, Any]],
    citation_style: str,
    citation_order: dict[str, int],
) -> dict[str, Any]:
    blocks = parse_markdown_blocks(section.get("content", ""))
    rendered_blocks: list[dict[str, Any]] = []
    for block in blocks:
        if block["kind"] == "paragraph":
            rendered_blocks.append(
                {
                    "kind": "paragraph",
                    "text": render_inline_citations(
                        block["text"], sources_by_id, citation_style, citation_order
                    ),
                }
            )
        elif block["kind"] in {"bullet_list", "ordered_list"}:
            rendered_blocks.append(
                {
                    "kind": block["kind"],
                    "items": [
                        render_inline_citations(item, sources_by_id, citation_style, citation_order)
                        for item in block["items"]
                    ],
                }
            )
        else:
            rendered_blocks.append(block)
    return {
        "id": section["id"],
        "title": section["title"],
        "role": section.get("role", "section"),
        "required": section.get("required", False),
        "target_words": section.get("target_words", 0),
        "blocks": rendered_blocks,
        "subsections": [
            render_section_text(subsection, sources_by_id, citation_style, citation_order)
            for subsection in section.get("subsections", [])
        ],
    }


def render_document_model(
    project_state: dict[str, Any],
    manuscript_state: dict[str, Any],
    sources_by_id: dict[str, dict[str, Any]],
    citation_style: str,
    citation_order: dict[str, int],
) -> dict[str, Any]:
    abstract_blocks = parse_markdown_blocks(manuscript_state.get("abstract", ""))
    rendered_abstract = [
        {
            "kind": block["kind"],
            "text": render_inline_citations(
                block["text"], sources_by_id, citation_style, citation_order
            )
            if block["kind"] == "paragraph"
            else block.get("text", ""),
            "items": [
                render_inline_citations(item, sources_by_id, citation_style, citation_order)
                for item in block.get("items", [])
            ]
            if "items" in block
            else [],
            **({"figure_id": block["figure_id"]} if "figure_id" in block else {}),
            **({"table_id": block["table_id"]} if "table_id" in block else {}),
        }
        for block in abstract_blocks
    ]

    return {
        "title": manuscript_state.get("title") or project_state["project"]["title"],
        "keywords": manuscript_state.get("keywords", []),
        "abstract_blocks": rendered_abstract,
        "sections": [
            render_section_text(section, sources_by_id, citation_style, citation_order)
            for section in manuscript_state.get("sections", [])
        ],
        "appendices": [
            render_section_text(section, sources_by_id, citation_style, citation_order)
            for section in manuscript_state.get("appendices", [])
        ],
    }
