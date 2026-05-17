from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE_DIR = ROOT_DIR / "data" / "reference"
DEFAULT_SET_WINDOW_REFERENCE_PATH = DEFAULT_REFERENCE_DIR / "set-window-reference.json"
DEFAULT_SYMBOL_CODE_REFERENCE_PATH = DEFAULT_REFERENCE_DIR / "symbol-codes.json"


class ReferenceEntry(TypedDict):
    """One concept-level reference entry within a topic."""

    id: str
    title: str
    summary: str
    rules: list[str]
    examples: list[str]


class ReferenceTopic(TypedDict):
    """One tracked reference-data topic document."""

    schema_version: int
    topic: str
    command: str
    entries: list[ReferenceEntry]


class SymbolCodeRow(TypedDict):
    """One code-to-glyph mapping row for symbol reference data."""

    code: str
    glyph: str


class SymbolCodeReference(TypedDict):
    """One tracked symbol-code reference document."""

    schema_version: int
    topic: str
    rows: list[SymbolCodeRow]


def load_reference_topic(path: Path) -> ReferenceTopic:
    """Load one repository-owned reference-data document from JSON."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def load_symbol_code_reference(path: Path = DEFAULT_SYMBOL_CODE_REFERENCE_PATH) -> SymbolCodeReference:
    """Load one repository-owned symbol-code reference document from JSON."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def validate_reference_topic(topic: ReferenceTopic) -> None:
    """Validate the minimal schema for a small reference-data topic."""
    if topic.get("schema_version") != 1:
        raise ValueError("reference topic schema_version must be 1")

    _require_non_empty_string(topic, "topic")
    _require_non_empty_string(topic, "command")

    entries = topic.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("reference topic must contain a non-empty entries list")

    seen_ids: set[str] = set()
    expected_keys = {"id", "title", "summary", "rules", "examples"}
    for entry in entries:
        if set(entry) != expected_keys:
            raise ValueError(
                f"reference entry keys must be exactly {sorted(expected_keys)}"
            )
        entry_id = _require_non_empty_string(entry, "id")
        if entry_id in seen_ids:
            raise ValueError(f"duplicate reference entry id: {entry_id}")
        seen_ids.add(entry_id)
        _require_non_empty_string(entry, "title")
        _require_non_empty_string(entry, "summary")
        _require_string_list(entry, "rules")
        _require_string_list(entry, "examples")


def validate_symbol_code_reference(reference: SymbolCodeReference) -> None:
    """Validate the minimal schema for code-to-glyph symbol reference data."""
    if reference.get("schema_version") != 1:
        raise ValueError("symbol code reference schema_version must be 1")

    topic = _require_non_empty_string(reference, "topic")
    if topic != "symbol-codes":
        raise ValueError(f"unexpected symbol reference topic: {topic!r}")

    rows = reference.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("symbol code reference must contain a non-empty rows list")

    seen_codes: set[str] = set()
    expected_keys = {"code", "glyph"}
    for row in rows:
        if set(row) != expected_keys:
            raise ValueError(
                f"symbol reference row keys must be exactly {sorted(expected_keys)}"
            )
        code = _require_non_empty_string(row, "code")
        if code in seen_codes:
            raise ValueError(f"duplicate symbol code: {code}")
        seen_codes.add(code)
        _require_non_empty_string(row, "glyph")


def _require_non_empty_string(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"reference field {key!r} must be a non-empty string")
    return value


def _require_string_list(mapping: dict[str, object], key: str) -> None:
    value = mapping.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"reference field {key!r} must be a non-empty list")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"reference field {key!r} must contain non-empty strings"
            )
