from __future__ import annotations

import json

import pytest

from topdrawer_mcp.preprocess.commands import CommandEntry
from topdrawer_mcp.preprocess.writer import command_index_payload, write_command_index


pytestmark = pytest.mark.unit


def _entry(section: str = "15.10", command: str = "BARGRAPH") -> CommandEntry:
    return CommandEntry(
        section=section,
        command=command,
        title=command,
        start_line=10,
        end_line=20,
        text=f"{section}  {command}\nbody",
    )


def test_command_index_payload_is_machine_independent():
    payload = command_index_payload(source_name="topdrawer.doc", entries=[_entry()])

    assert payload["schema_version"] == 1
    assert payload["source_name"] == "topdrawer.doc"
    assert payload["entry_count"] == 1
    assert payload["entries"][0]["command"] == "BARGRAPH"


def test_write_command_index_creates_deterministic_json(tmp_path):
    first = write_command_index(tmp_path, source_name="topdrawer.doc", entries=[_entry()])
    first_text = first.read_text(encoding="utf-8")

    second = write_command_index(tmp_path, source_name="topdrawer.doc", entries=[_entry()])
    second_text = second.read_text(encoding="utf-8")

    assert first == second
    assert first_text == second_text
    parsed = json.loads(first_text)
    assert parsed["entries"][0]["section"] == "15.10"
