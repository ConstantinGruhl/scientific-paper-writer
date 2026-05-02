from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


CITATION_TOKEN_RE = re.compile(r"\[@([^\]]+)\]")


def normalize_author(raw: str | dict[str, str]) -> dict[str, str]:
    if isinstance(raw, dict):
        given = raw.get("given", "").strip()
        family = raw.get("family", "").strip()
        return {"given": given, "family": family}

    parts = [part for part in raw.strip().split() if part]
    if not parts:
        return {"given": "", "family": ""}
    if len(parts) == 1:
        return {"given": "", "family": parts[0]}
    return {"given": " ".join(parts[:-1]), "family": parts[-1]}


def normalize_source(source: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(source)
    normalized["authors"] = [normalize_author(author) for author in source.get("authors", [])]
    normalized["title"] = source.get("title", "").strip()
    normalized["type"] = source.get("type", "article").strip() or "article"
    normalized["year"] = str(source.get("year", "")).strip()
    normalized["container_title"] = source.get("container_title", "").strip()
    normalized["doi"] = source.get("doi", "").strip()
    normalized["url"] = source.get("url", "").strip()
    normalized["verified"] = bool(source.get("verified", False))
    normalized["notes"] = source.get("notes", "").strip()
    return normalized


def missing_source_fields(source: dict[str, Any]) -> list[str]:
    required = ["id", "title", "year"]
    missing = [field for field in required if not source.get(field)]
    if not source.get("authors"):
        missing.append("authors")
    return missing


def source_sort_key(source: dict[str, Any]) -> tuple[str, str, str]:
    authors = source.get("authors", [])
    family = authors[0]["family"] if authors else ""
    return (family.lower(), str(source.get("year", "")), source.get("title", "").lower())


def author_list_text(
    authors: list[dict[str, str]],
    *,
    style: str,
    invert_first: bool = False,
) -> str:
    if not authors:
        return "Unknown Author"

    rendered: list[str] = []
    for index, author in enumerate(authors):
        given = author.get("given", "").strip()
        family = author.get("family", "").strip()
        initials = " ".join(f"{part[0]}." for part in given.split() if part)
        if style == "apa7":
            if index == 0 or invert_first:
                piece = f"{family}, {initials}".strip().rstrip(",")
            else:
                piece = f"{initials} {family}".strip()
        elif style == "ieee":
            piece = f"{initials} {family}".strip()
        elif style == "mla9":
            if index == 0 or invert_first:
                piece = f"{family}, {given}".strip().rstrip(",")
            else:
                piece = f"{given} {family}".strip()
        else:
            piece = f"{family}, {given}".strip().rstrip(",")
        rendered.append(piece)

    if len(rendered) == 1:
        return rendered[0]
    if len(rendered) == 2:
        joiner = " & " if style == "apa7" else " and "
        return joiner.join(rendered)
    if style == "apa7":
        return ", ".join(rendered[:-1]) + f", & {rendered[-1]}"
    return ", ".join(rendered[:-1]) + f", and {rendered[-1]}"


def _volume_issue_pages(source: dict[str, Any], *, style: str) -> str:
    volume = str(source.get("volume", "")).strip()
    issue = str(source.get("issue", "")).strip()
    pages = str(source.get("pages", "")).strip()
    fragments: list[str] = []
    if style == "apa7":
        if volume:
            issue_part = f"({issue})" if issue else ""
            fragments.append(f"{volume}{issue_part}")
        if pages:
            fragments.append(pages)
        return ", ".join(fragments)
    if style == "ieee":
        if volume:
            fragments.append(f"vol. {volume}")
        if issue:
            fragments.append(f"no. {issue}")
        if pages:
            fragments.append(f"pp. {pages}")
        return ", ".join(fragments)
    if style == "mla9":
        if volume:
            fragments.append(f"vol. {volume}")
        if issue:
            fragments.append(f"no. {issue}")
        if pages:
            fragments.append(f"pp. {pages}")
        return ", ".join(fragments)
    if volume:
        fragments.append(volume)
    if issue:
        fragments.append(f"({issue})")
    if pages:
        fragments.append(pages)
    return ", ".join(fragments)


def format_reference(source: dict[str, Any], style_id: str, ordinal: int | None = None) -> str:
    source = normalize_source(source)
    authors = author_list_text(source.get("authors", []), style=style_id, invert_first=True)
    title = source.get("title", "")
    container = source.get("container_title", "")
    year = source.get("year", "")
    vip = _volume_issue_pages(source, style=style_id)
    doi = source.get("doi", "")
    url = source.get("url", "")
    locator = doi or url

    if style_id == "apa7":
        parts = [f"{authors} ({year}). {title}."]
        if container:
            container_part = container
            if vip:
                container_part += f", {vip}"
            parts.append(container_part + ".")
        elif vip:
            parts.append(vip + ".")
        if locator:
            parts.append(locator)
        return " ".join(part.strip() for part in parts if part.strip()).strip()

    if style_id == "ieee":
        prefix = f"[{ordinal}] " if ordinal is not None else ""
        parts = [f'{prefix}{authors}, "{title},"']
        if container:
            parts.append(container)
        if vip:
            parts.append(vip)
        if year:
            parts.append(year)
        if locator:
            locator_prefix = "doi: " if doi else ""
            parts.append(locator_prefix + locator)
        return ", ".join(part.strip().rstrip(",") for part in parts if part.strip()) + "."

    if style_id == "mla9":
        parts = [f'{authors}. "{title}."']
        if container:
            parts.append(container)
        if vip:
            parts.append(vip)
        if year:
            parts.append(year)
        if locator:
            parts.append(locator)
        return ", ".join(part.strip().rstrip(",") for part in parts if part.strip()) + "."

    parts = [f'{authors}. {year}. "{title}."']
    if container:
        container_part = container
        if vip:
            container_part += f" {vip}"
        parts.append(container_part + ".")
    elif vip:
        parts.append(vip + ".")
    if locator:
        parts.append(locator + ".")
    return " ".join(part.strip() for part in parts if part.strip()).strip()


def inline_citation(source: dict[str, Any], style_id: str, ordinal: int | None = None) -> str:
    authors = source.get("authors", [])
    family = authors[0]["family"] if authors else "Unknown"
    year = source.get("year", "n.d.")
    if style_id == "ieee":
        return f"[{ordinal}]"
    if style_id == "apa7":
        if len(authors) >= 2:
            return f"({family} & {authors[1]['family']}, {year})"
        return f"({family}, {year})"
    if style_id == "mla9":
        return f"({family})"
    return f"({family} {year})"


def extract_citation_ids_from_text(text: str) -> list[str]:
    ids: list[str] = []
    for match in CITATION_TOKEN_RE.findall(text):
        for raw_piece in match.split(";"):
            citation_id = raw_piece.strip().lstrip("@")
            if citation_id:
                ids.append(citation_id)
    return ids


def build_citation_order(
    manuscript_state: dict[str, Any],
    evidence_state: dict[str, Any],
) -> dict[str, int]:
    order: dict[str, int] = {}
    next_number = 1

    def register(source_id: str) -> None:
        nonlocal next_number
        if source_id not in order:
            order[source_id] = next_number
            next_number += 1

    if manuscript_state.get("abstract"):
        for source_id in extract_citation_ids_from_text(manuscript_state["abstract"]):
            register(source_id)

    def walk_sections(sections: list[dict[str, Any]]) -> None:
        for section in sections:
            for source_id in extract_citation_ids_from_text(section.get("content", "")):
                register(source_id)
            walk_sections(section.get("subsections", []))

    walk_sections(manuscript_state.get("sections", []))
    walk_sections(manuscript_state.get("appendices", []))

    for claim in evidence_state.get("claims", []):
        for source_id in claim.get("source_ids", []):
            register(source_id)

    return order


def render_inline_citations(
    text: str,
    sources_by_id: dict[str, dict[str, Any]],
    style_id: str,
    citation_order: dict[str, int],
) -> str:
    def replacer(match: re.Match[str]) -> str:
        rendered: list[str] = []
        for raw_piece in match.group(1).split(";"):
            citation_id = raw_piece.strip().lstrip("@")
            source = sources_by_id.get(citation_id)
            if not source:
                rendered.append(f"[missing:{citation_id}]")
                continue
            rendered.append(
                inline_citation(source, style_id, ordinal=citation_order.get(citation_id))
            )
        return "; ".join(rendered)

    return CITATION_TOKEN_RE.sub(replacer, text)


def bibliography_entries(
    sources_state: dict[str, Any],
    style_id: str,
    citation_order: dict[str, int],
) -> list[str]:
    normalized_sources = [normalize_source(source) for source in sources_state.get("sources", [])]
    if style_id == "ieee":
        numbered = sorted(
            normalized_sources,
            key=lambda source: citation_order.get(source["id"], 10_000),
        )
        return [
            format_reference(source, style_id, ordinal=citation_order.get(source["id"]))
            for source in numbered
            if source.get("verified", False)
        ]

    sorted_sources = sorted(normalized_sources, key=source_sort_key)
    return [
        format_reference(source, style_id)
        for source in sorted_sources
        if source.get("verified", False)
    ]


def source_index(sources_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {source["id"]: normalize_source(source) for source in sources_state.get("sources", [])}


def cited_source_ids(
    manuscript_state: dict[str, Any],
    evidence_state: dict[str, Any],
) -> list[str]:
    order = build_citation_order(manuscript_state, evidence_state)
    return list(order.keys())


def claim_support_summary(evidence_state: dict[str, Any]) -> dict[str, list[str]]:
    summary: dict[str, list[str]] = defaultdict(list)
    for claim in evidence_state.get("claims", []):
        for source_id in claim.get("source_ids", []):
            summary[source_id].append(claim.get("id", "claim"))
    return dict(summary)
