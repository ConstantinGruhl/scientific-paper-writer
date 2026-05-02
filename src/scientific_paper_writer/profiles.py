from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any


def _data_root() -> Any:
    return files("scientific_paper_writer").joinpath("data")


def _load_json(resource_path: list[str]) -> dict[str, Any]:
    current = _data_root()
    for part in resource_path:
        current = current.joinpath(part)
    return json.loads(current.read_text(encoding="utf-8"))


def _load_collection(kind: str) -> dict[str, dict[str, Any]]:
    root = _data_root().joinpath(kind)
    collection: dict[str, dict[str, Any]] = {}
    for child in root.iterdir():
        if child.is_file() and child.name.endswith(".json"):
            collection[child.stem] = json.loads(child.read_text(encoding="utf-8"))
    return collection


def load_paper_type_profile(profile_id: str) -> dict[str, Any]:
    return _load_json(["paper_types", f"{profile_id}.json"])


def load_formatting_profile(profile_id: str) -> dict[str, Any]:
    return _load_json(["formatting", f"{profile_id}.json"])


def load_citation_profile(profile_id: str) -> dict[str, Any]:
    return _load_json(["citation_styles", f"{profile_id}.json"])


def list_paper_type_profiles() -> dict[str, dict[str, Any]]:
    return _load_collection("paper_types")


def list_formatting_profiles() -> dict[str, dict[str, Any]]:
    return _load_collection("formatting")


def list_citation_profiles() -> dict[str, dict[str, Any]]:
    return _load_collection("citation_styles")


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        base_value = merged.get(key)
        if isinstance(base_value, dict) and isinstance(value, dict):
            merged[key] = deep_merge(base_value, value)
        else:
            merged[key] = value
    return merged


def resolve_profiles(
    paper_type_id: str,
    formatting_profile_id: str | None = None,
    citation_profile_id: str | None = None,
    institution_override_path: str | None = None,
) -> dict[str, dict[str, Any]]:
    paper_type = load_paper_type_profile(paper_type_id)
    formatting_id = formatting_profile_id or paper_type["default_formatting_profile"]
    citation_id = citation_profile_id or paper_type["default_citation_style"]

    formatting = load_formatting_profile(formatting_id)
    citation = load_citation_profile(citation_id)

    resolved = {
        "paper_type": paper_type,
        "formatting": formatting,
        "citation": citation,
    }

    if institution_override_path:
        override_path = Path(institution_override_path)
        if override_path.exists():
            override = json.loads(override_path.read_text(encoding="utf-8"))
            resolved = deep_merge(resolved, override)

    return resolved


def resolve_effective_formatting_profile(project_state: dict[str, Any]) -> dict[str, Any]:
    effective = project_state.get("profile_resolution", {}).get("effective_formatting")
    if isinstance(effective, dict) and effective.get("id"):
        return effective

    profiles = resolve_profiles(
        project_state["profiles"]["paper_type"],
        formatting_profile_id=project_state["profiles"].get("formatting"),
        citation_profile_id=project_state["profiles"].get("citation"),
        institution_override_path=project_state["profiles"].get("institution_override_path") or None,
    )
    return profiles["formatting"]
