from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Literal
from typing import TypedDict

from topdrawer_mcp.preprocess.lookup import build_command_lookup_entries
from topdrawer_mcp.preprocess.lookup import load_command_lookup_targets
from topdrawer_mcp.preprocess.lookup import load_reviewed_command_lookup_entries
from topdrawer_mcp.preprocess.sources import DEFAULT_LOOKUP_REVIEWED_PATH
from topdrawer_mcp.preprocess.sources import DEFAULT_LOOKUP_TARGETS_PATH


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_COMMAND_LOOKUP_INDEX_PATH = ROOT_DIR / "data" / "index" / "command-lookup-index.json"
DEFAULT_COMMAND_LOOKUP_MANUAL_PATH = ROOT_DIR / "data" / "topdrawer.txt"
VALID_COMMAND_LOOKUP_KINDS = frozenset({"command", "modifier", "set-subcommand"})


class CommandLookupOptionGroup(TypedDict):
    """One reviewed option group for a command lookup entry."""

    name: str
    items: list[str]


CommandLookupKind = Literal["command", "modifier", "set-subcommand"]


class CommandLookupEntry(TypedDict):
    """One command lookup entry returned by the MCP tool."""

    command: str
    aliases: list[str]
    kind: CommandLookupKind
    parent_command: str | None
    section: str
    title: str
    start_line: int
    end_line: int
    summary: str
    syntax_lines: list[str]
    important_rules: list[str]
    option_groups: list[CommandLookupOptionGroup]
    raw_text: str


class CommandLookupIndex(TypedDict):
    """Top-level command lookup index document."""

    schema_version: int
    source_name: str
    entry_count: int
    entries: list[CommandLookupEntry]


def load_command_lookup_index(
    path: Path | None = None,
) -> CommandLookupIndex:
    """Load the reviewed command lookup index.

    When `path` is provided, read the JSON payload directly. When omitted, build
    the runtime index from tracked sources in the repository.
    """
    if path is not None:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    return _build_runtime_command_lookup_index()


def lookup_command_entry(
    command: str,
    path: Path | None = None,
) -> CommandLookupEntry:
    """Resolve one command or unique alias from the lookup index."""
    normalized_query = _normalize_command_name(command)
    if not normalized_query:
        raise ValueError("command must be a non-empty string")

    index = load_command_lookup_index(path)
    validate_command_lookup_index(index)

    entries = index["entries"]
    for entry in entries:
        if _normalize_command_name(entry["command"]) == normalized_query:
            return entry

    alias_matches = [
        entry
        for entry in entries
        if any(_normalize_command_name(alias) == normalized_query for alias in entry["aliases"])
    ]
    if len(alias_matches) == 1:
        return alias_matches[0]
    if len(alias_matches) > 1:
        raise ValueError(f"Ambiguous command alias: {command.strip()!r}")
    raise ValueError(f"Unknown command lookup entry: {command.strip()!r}")


@lru_cache(maxsize=1)
def _build_runtime_command_lookup_index() -> CommandLookupIndex:
    source_text = DEFAULT_COMMAND_LOOKUP_MANUAL_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )
    targets = load_command_lookup_targets(DEFAULT_LOOKUP_TARGETS_PATH)
    reviewed_entries = load_reviewed_command_lookup_entries(DEFAULT_LOOKUP_REVIEWED_PATH)
    entries = [entry.to_json() for entry in build_command_lookup_entries(source_text, targets, reviewed_entries)]
    index: CommandLookupIndex = {
        "schema_version": 1,
        "source_name": (
            "data/topdrawer.txt + data/lookup/command-lookup-targets.json + "
            "data/lookup/command-lookup-reviewed.json"
        ),
        "entry_count": len(entries),
        "entries": entries,
    }
    validate_command_lookup_index(index)
    return index


def validate_command_lookup_index(index: CommandLookupIndex) -> None:
    """Validate the minimal runtime schema for command lookup data."""
    if index.get("schema_version") != 1:
        raise ValueError("command lookup index schema_version must be 1")

    entries = index.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("command lookup index must contain a non-empty entries list")

    entry_count = index.get("entry_count")
    if entry_count != len(entries):
        raise ValueError("command lookup index entry_count does not match entries length")

    seen_commands: set[str] = set()
    for entry in entries:
        command = _required_non_empty_string(entry, "command")
        if command in seen_commands:
            raise ValueError(f"duplicate command lookup entry: {command}")
        seen_commands.add(command)

        kind = entry.get("kind")
        if kind not in VALID_COMMAND_LOOKUP_KINDS:
            raise ValueError(f"invalid command lookup kind: {kind!r}")

        _require_string_list(entry, "aliases", allow_empty=True)
        _required_non_empty_string(entry, "section")
        _required_non_empty_string(entry, "title")
        _required_non_empty_string(entry, "summary")
        _required_non_empty_string(entry, "raw_text")
        _require_positive_int(entry, "start_line")
        _require_positive_int(entry, "end_line")
        _require_string_list(entry, "syntax_lines", allow_empty=False)
        _require_string_list(entry, "important_rules", allow_empty=True)

        parent_command = entry.get("parent_command")
        if parent_command is not None and (
            not isinstance(parent_command, str) or not parent_command.strip()
        ):
            raise ValueError("parent_command must be null or a non-empty string")

        option_groups = entry.get("option_groups")
        if not isinstance(option_groups, list):
            raise ValueError("option_groups must be a list")
        for group in option_groups:
            if not isinstance(group, dict):
                raise ValueError("option_groups entries must be objects")
            _required_non_empty_string(group, "name")
            _require_string_list(group, "items", allow_empty=False)


def _normalize_command_name(value: str) -> str:
    return " ".join(value.replace("_", " ").strip().upper().split())


def _required_non_empty_string(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"command lookup field {key!r} must be a non-empty string")
    return value


def _require_positive_int(mapping: dict[str, object], key: str) -> None:
    value = mapping.get(key)
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"command lookup field {key!r} must be a positive integer")


def _require_string_list(
    mapping: dict[str, object],
    key: str,
    *,
    allow_empty: bool,
) -> None:
    value = mapping.get(key)
    if not isinstance(value, list):
        raise ValueError(f"command lookup field {key!r} must be a list")
    if not allow_empty and not value:
        raise ValueError(f"command lookup field {key!r} must be non-empty")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"command lookup field {key!r} must contain non-empty strings"
            )
