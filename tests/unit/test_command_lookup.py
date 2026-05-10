from __future__ import annotations

import json

import pytest

from topdrawer_mcp.command_lookup import load_command_lookup_index
from topdrawer_mcp.command_lookup import lookup_command_entry
from topdrawer_mcp.command_lookup import validate_command_lookup_index


pytestmark = pytest.mark.unit


def _index_payload(entries: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "source_name": "topdrawer.doc",
        "entry_count": len(entries),
        "entries": entries,
    }


def _entry(
    *,
    command: str = "BARGRAPH",
    aliases: list[str] | None = None,
    kind: str = "command",
    parent_command: str | None = None,
) -> dict:
    return {
        "command": command,
        "aliases": [] if aliases is None else aliases,
        "kind": kind,
        "parent_command": parent_command,
        "section": "15.10",
        "title": command,
        "start_line": 10,
        "end_line": 20,
        "summary": "summary",
        "syntax_lines": [f"{command} [EXPAND]"],
        "important_rules": ["rule"],
        "option_groups": [{"name": "options", "items": ["WIDTH=n"]}],
        "raw_text": f"15.10  {command}\nbody",
    }


def test_load_command_lookup_index_reads_valid_payload(tmp_path):
    path = tmp_path / "lookup.json"
    path.write_text(json.dumps(_index_payload([_entry()])), encoding="utf-8")

    loaded = load_command_lookup_index(path)

    assert loaded["entry_count"] == 1
    assert loaded["entries"][0]["command"] == "BARGRAPH"


def test_validate_command_lookup_index_rejects_invalid_kind():
    with pytest.raises(ValueError, match="invalid command lookup kind"):
        validate_command_lookup_index(_index_payload([_entry(kind="unknown")]))


def test_validate_command_lookup_index_rejects_duplicate_command():
    payload = _index_payload([_entry(), _entry()])

    with pytest.raises(ValueError, match="duplicate command lookup entry"):
        validate_command_lookup_index(payload)


def test_validate_command_lookup_index_rejects_malformed_aliases():
    payload = _index_payload([_entry(aliases=["SYMBOL"])])
    payload["entries"][0]["aliases"] = "SYMBOL"

    with pytest.raises(ValueError, match="aliases"):
        validate_command_lookup_index(payload)


def test_validate_command_lookup_index_rejects_malformed_option_groups():
    payload = _index_payload([_entry()])
    payload["entries"][0]["option_groups"] = [{"name": "options", "items": []}]

    with pytest.raises(ValueError, match="items"):
        validate_command_lookup_index(payload)


def test_lookup_command_entry_resolves_canonical_and_alias_and_underscore(tmp_path):
    path = tmp_path / "lookup.json"
    path.write_text(
        json.dumps(
            _index_payload(
                [
                    _entry(command="BARGRAPH"),
                    _entry(
                        command="SET SYMBOL",
                        aliases=["SYMBOL"],
                        kind="set-subcommand",
                        parent_command="SET",
                    ),
                ]
            )
        ),
        encoding="utf-8",
    )

    assert lookup_command_entry("BARGRAPH", path)["command"] == "BARGRAPH"
    assert lookup_command_entry("SYMBOL", path)["command"] == "SET SYMBOL"
    assert lookup_command_entry("set_symbol", path)["command"] == "SET SYMBOL"


def test_lookup_command_entry_rejects_unknown_command(tmp_path):
    path = tmp_path / "lookup.json"
    path.write_text(json.dumps(_index_payload([_entry()])), encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown command lookup entry"):
        lookup_command_entry("MISSING", path)


def test_lookup_command_entry_rejects_ambiguous_alias(tmp_path):
    path = tmp_path / "lookup.json"
    path.write_text(
        json.dumps(
            _index_payload(
                [
                    _entry(command="SET SYMBOL", aliases=["SYMBOL"]),
                    _entry(command="PLOT SYMBOL", aliases=["SYMBOL"]),
                ]
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Ambiguous command alias"):
        lookup_command_entry("SYMBOL", path)
