from __future__ import annotations

import pytest

from topdrawer_mcp.command_lookup import CommandLookupEntry
from topdrawer_mcp.reverse_lookup import reverse_lookup_command_candidates


pytestmark = pytest.mark.unit


def _entry(
    command: str,
    *,
    aliases: list[str] | None = None,
    title: str | None = None,
    summary: str = "Reviewed summary",
    syntax_lines: list[str] | None = None,
    important_rules: list[str] | None = None,
) -> CommandLookupEntry:
    return {
        "command": command,
        "aliases": aliases or [],
        "kind": "command",
        "parent_command": None,
        "section": "15.1",
        "title": title or command,
        "start_line": 1,
        "end_line": 5,
        "summary": summary,
        "syntax_lines": syntax_lines or [command],
        "important_rules": important_rules or [],
        "option_groups": [],
        "raw_text": f"{command} raw text",
    }


def test_reverse_lookup_rejects_empty_query():
    with pytest.raises(ValueError, match="query must be a non-empty string"):
        reverse_lookup_command_candidates("   ")


def test_reverse_lookup_finds_set_polar_first():
    result = reverse_lookup_command_candidates("polar")

    assert result["commands"]
    assert result["commands"][0] == "SET POLAR"


def test_reverse_lookup_returns_join_for_points_and_line():
    result = reverse_lookup_command_candidates("points and line")

    assert "JOIN" in result["commands"]


def test_reverse_lookup_prefers_default_limit_of_five():
    result = reverse_lookup_command_candidates("set")

    assert result["commands"]
    assert len(result["commands"]) <= 5


def test_reverse_lookup_honors_explicit_limit():
    result = reverse_lookup_command_candidates("set", limit=2)

    assert result["commands"]
    assert len(result["commands"]) <= 2


def test_reverse_lookup_clamps_limit_to_minimum():
    result = reverse_lookup_command_candidates("set", limit=0)

    assert result["commands"]
    assert len(result["commands"]) == 1


def test_reverse_lookup_clamps_limit_to_maximum():
    result = reverse_lookup_command_candidates("a", limit=99)

    assert len(result["commands"]) <= 20


def test_reverse_lookup_returns_canonical_command_headings_only(
    monkeypatch: pytest.MonkeyPatch,
):
    entries = [
        _entry("SET POLAR", aliases=["polar mode"], title="POLAR"),
        _entry("PLOT", aliases=["plot points"], title="PLOT"),
    ]
    monkeypatch.setattr(
        "topdrawer_mcp.reverse_lookup.load_command_lookup_index",
        lambda: {"schema_version": 1, "source_name": "test", "entry_count": 2, "entries": entries},
    )

    result = reverse_lookup_command_candidates("polar mode")

    assert result["commands"] == ["SET POLAR"]


def test_reverse_lookup_deduplicates_command_headings(
    monkeypatch: pytest.MonkeyPatch,
):
    entries = [
        _entry("SET POLAR", title="POLAR", summary="Primary polar command"),
        _entry("SET POLAR", title="POLAR", summary="Duplicate reviewed polar command"),
        _entry("PLOT", summary="Plot data points"),
    ]
    monkeypatch.setattr(
        "topdrawer_mcp.reverse_lookup.load_command_lookup_index",
        lambda: {"schema_version": 1, "source_name": "test", "entry_count": 3, "entries": entries},
    )

    result = reverse_lookup_command_candidates("polar", limit=5)

    assert result["commands"] == ["SET POLAR"]
