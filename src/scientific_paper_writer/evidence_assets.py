from __future__ import annotations

from typing import Any


_META_KEYS = {"id", "kind", "path", "style", "type"}
_TEXT_KEYS = (
    "text",
    "value",
    "label",
    "title",
    "caption",
    "note",
    "notes",
    "description",
)
_COLUMN_KEYS = ("id", "key", "field", "name", "label", "title")


def lookup_figure(evidence_state: dict[str, Any], figure_id: str) -> dict[str, Any] | None:
    return next(
        (item for item in evidence_state.get("figures", []) if item.get("id") == figure_id),
        None,
    )


def lookup_table(evidence_state: dict[str, Any], table_id: str) -> dict[str, Any] | None:
    return next(
        (item for item in evidence_state.get("tables", []) if item.get("id") == table_id),
        None,
    )


def figure_caption_text(figure: dict[str, Any]) -> str:
    return str(figure.get("caption") or figure.get("title") or "").strip()


def _stringify_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        for key in _TEXT_KEYS:
            if key in value:
                text = _stringify_value(value[key])
                if text:
                    return text
        pieces = [
            _stringify_value(item)
            for key, item in value.items()
            if key not in _META_KEYS and key not in _COLUMN_KEYS
        ]
        return " ".join(piece for piece in pieces if piece)
    if isinstance(value, (list, tuple)):
        return " ".join(piece for piece in (_stringify_value(item) for item in value) if piece)
    return str(value).strip()


def _column_specs(table: dict[str, Any], rows: list[Any]) -> list[dict[str, Any]]:
    raw_columns = table.get("columns") or table.get("headers") or []
    specs: list[dict[str, Any]] = []
    for raw_column in raw_columns:
        if isinstance(raw_column, str):
            label = raw_column.strip()
            if label:
                specs.append({"label": label, "keys": [label]})
            continue

        if isinstance(raw_column, dict):
            keys = [
                str(raw_column[key]).strip()
                for key in _COLUMN_KEYS
                if raw_column.get(key) is not None and str(raw_column.get(key)).strip()
            ]
            if keys:
                specs.append({"label": keys[0], "keys": keys})

    if specs or not rows:
        return specs

    first_row = rows[0]
    if isinstance(first_row, dict):
        for key in first_row:
            if key in _META_KEYS:
                continue
            label = str(key).replace("_", " ").strip()
            specs.append({"label": label.title(), "keys": [str(key)]})
    return specs


def _row_cells(row: Any, columns: list[dict[str, Any]]) -> list[str]:
    if isinstance(row, dict):
        if not columns:
            return [
                _stringify_value(value)
                for key, value in row.items()
                if key not in _META_KEYS
            ]

        cells: list[str] = []
        for column in columns:
            value = ""
            for key in column["keys"]:
                if key in row:
                    value = _stringify_value(row[key])
                    break
            cells.append(value)
        return cells

    if isinstance(row, (list, tuple)):
        return [_stringify_value(cell) for cell in row]

    text = _stringify_value(row)
    return [text] if text else []


def table_display_model(table: dict[str, Any]) -> dict[str, Any]:
    rows = list(table.get("rows") or table.get("cells") or [])
    columns = _column_specs(table, rows)
    headers = [column["label"] for column in columns]
    rendered_rows = [_row_cells(row, columns) for row in rows]
    return {
        "caption": str(table.get("caption") or table.get("title") or "").strip(),
        "headers": headers,
        "rows": rendered_rows,
    }


def table_text_fragments(table: dict[str, Any]) -> list[str]:
    model = table_display_model(table)
    fragments: list[str] = []
    if model["caption"]:
        fragments.append(model["caption"])
    fragments.extend(header for header in model["headers"] if header)
    for row in model["rows"]:
        fragments.extend(cell for cell in row if cell)
    for key in ("notes", "footnotes", "description"):
        text = _stringify_value(table.get(key))
        if text:
            fragments.append(text)
    return fragments
