from __future__ import annotations

import json
from pathlib import Path

from .commands import CommandEntry
from .lookup import CommandLookupEntry


COMMAND_INDEX_FILENAME = "command-index.json"
COMMAND_LOOKUP_INDEX_FILENAME = "command-lookup-index.json"
SCHEMA_VERSION = 1


def command_index_payload(source_name: str, entries: list[CommandEntry]) -> dict:
    """Create a deterministic command index payload."""
    return {
        "schema_version": SCHEMA_VERSION,
        "source_name": source_name,
        "entry_count": len(entries),
        "entries": [entry.to_json() for entry in entries],
    }


def command_lookup_index_payload(
    source_name: str,
    entries: list[CommandLookupEntry],
) -> dict:
    """Create a deterministic command lookup payload."""
    return {
        "schema_version": SCHEMA_VERSION,
        "source_name": source_name,
        "entry_count": len(entries),
        "entries": [entry.to_json() for entry in entries],
    }


def write_command_index(
    output_dir: str | Path,
    source_name: str,
    entries: list[CommandEntry],
) -> Path:
    """Write command index JSON under `output_dir` and return the path."""
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = resolved_output_dir / COMMAND_INDEX_FILENAME
    payload = command_index_payload(source_name=source_name, entries=entries)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def write_command_lookup_index(
    output_dir: str | Path,
    source_name: str,
    entries: list[CommandLookupEntry],
) -> Path:
    """Write command lookup JSON under `output_dir` and return the path."""
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = resolved_output_dir / COMMAND_LOOKUP_INDEX_FILENAME
    payload = command_lookup_index_payload(source_name=source_name, entries=entries)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path
