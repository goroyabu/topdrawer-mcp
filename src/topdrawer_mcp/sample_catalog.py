from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE_CATALOG_PATH = ROOT_DIR / "data" / "samples" / "catalog.json"
DEFAULT_SAMPLE_LIST_LIMIT = 20
MAX_SAMPLE_LIST_LIMIT = 20
ALLOWED_SAMPLE_CATEGORIES = frozenset(
    {
        "scatter",
        "symbols",
        "join",
        "histogram",
        "function",
        "title",
        "ticks",
        "labels",
        "window",
        "polar",
    }
)

class SampleCatalogEntry(TypedDict):
    """One curated manual-sample catalog entry."""

    id: str
    title: str
    category: str
    description: str
    primary_commands: list[str]


class SampleCatalog(TypedDict):
    """Top-level manual sample catalog document."""

    version: int
    samples: list[SampleCatalogEntry]


class SampleCatalogListResult(TypedDict):
    """Structured result returned by sample catalog listing tools."""

    samples: list[SampleCatalogEntry]


def load_sample_catalog(path: Path = DEFAULT_SAMPLE_CATALOG_PATH) -> SampleCatalog:
    """Load the repository-owned sample catalog from JSON."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def get_sample_catalog_entry(
    sample_id: str,
    path: Path = DEFAULT_SAMPLE_CATALOG_PATH,
) -> SampleCatalogEntry:
    """Return one catalog entry by id."""
    stripped_sample_id = sample_id.strip()
    if not stripped_sample_id:
        raise ValueError("sample_id must be a non-empty string")

    catalog = load_sample_catalog(path)
    validate_sample_catalog(catalog)
    for entry in catalog["samples"]:
        if entry["id"] == stripped_sample_id:
            return entry
    raise ValueError(f"Unknown manual sample id: {stripped_sample_id!r}")


def list_sample_catalog_entries(
    *,
    category: str | None = None,
    command: str | None = None,
    query: str | None = None,
    limit: int = DEFAULT_SAMPLE_LIST_LIMIT,
    path: Path = DEFAULT_SAMPLE_CATALOG_PATH,
) -> list[SampleCatalogEntry]:
    """List catalog entries filtered by category, command, and free-text query."""
    catalog = load_sample_catalog(path)
    validate_sample_catalog(catalog)

    normalized_category = _normalize_optional_filter(category)
    normalized_command = _normalize_optional_filter(command)
    normalized_query = _normalize_optional_filter(query)
    clamped_limit = _clamp_limit(limit)

    if (
        normalized_category is not None
        and normalized_category not in ALLOWED_SAMPLE_CATEGORIES
    ):
        raise ValueError(f"invalid sample category: {normalized_category!r}")

    matches = []
    for entry in catalog["samples"]:
        if normalized_category is not None and entry["category"] != normalized_category:
            continue
        if normalized_command is not None and not _entry_has_command(
            entry, normalized_command
        ):
            continue
        if normalized_query is not None and not _entry_matches_query(
            entry, normalized_query
        ):
            continue
        matches.append(entry)
        if len(matches) >= clamped_limit:
            break
    return matches


def validate_sample_catalog(catalog: SampleCatalog) -> None:
    """Validate the minimal schema and curation expectations for the sample catalog."""
    if catalog.get("version") != 1:
        raise ValueError("sample catalog version must be 1")

    samples = catalog.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError("sample catalog must contain a non-empty samples list")

    seen_ids: set[str] = set()
    seen_categories: set[str] = set()
    expected_keys = {"id", "title", "category", "description", "primary_commands"}

    for entry in samples:
        if set(entry) != expected_keys:
            raise ValueError(
                f"sample catalog entry keys must be exactly {sorted(expected_keys)}"
            )
        _require_non_empty_string(entry, "id")
        _require_non_empty_string(entry, "title")
        _require_non_empty_string(entry, "description")

        sample_id = entry["id"]
        if sample_id in seen_ids:
            raise ValueError(f"duplicate sample id: {sample_id}")
        seen_ids.add(sample_id)

        category = entry.get("category")
        if category not in ALLOWED_SAMPLE_CATEGORIES:
            raise ValueError(f"invalid sample category: {category!r}")
        seen_categories.add(category)

        commands = entry.get("primary_commands")
        if not isinstance(commands, list) or not commands:
            raise ValueError(f"sample {sample_id} must declare at least one primary command")
        if any(not isinstance(command, str) or not command.strip() for command in commands):
            raise ValueError(f"sample {sample_id} has an invalid primary command")

    expected_categories = ALLOWED_SAMPLE_CATEGORIES
    if seen_categories != expected_categories:
        missing = sorted(expected_categories - seen_categories)
        extra = sorted(seen_categories - expected_categories)
        raise ValueError(
            "sample catalog category coverage mismatch: "
            f"missing={missing}, extra={extra}"
        )


def _require_non_empty_string(mapping: dict[str, object], key: str) -> None:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"sample catalog field {key!r} must be a non-empty string")


def _normalize_optional_filter(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _clamp_limit(value: int) -> int:
    parsed = int(value)
    return max(1, min(parsed, MAX_SAMPLE_LIST_LIMIT))


def _entry_has_command(entry: SampleCatalogEntry, command: str) -> bool:
    needle = command.casefold()
    return any(command_name.casefold() == needle for command_name in entry["primary_commands"])


def _entry_matches_query(entry: SampleCatalogEntry, query: str) -> bool:
    needle = query.casefold()
    haystacks = [
        entry["id"],
        entry["title"],
        entry["description"],
        *entry["primary_commands"],
    ]
    return any(needle in value.casefold() for value in haystacks)
