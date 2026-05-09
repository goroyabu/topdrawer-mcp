from __future__ import annotations

import asyncio

import pytest

from topdrawer_mcp import server


pytestmark = pytest.mark.unit


def test_search_manual_finds_case_insensitive_match(sample_manual):
    result = server.search_manual("bargraph", limit=1, context_lines=0)

    assert "Found 1 matches for 'bargraph'." in result
    assert "> 2: BARGRAPH command" in result


def test_search_manual_includes_context_lines(sample_manual):
    result = server.search_manual("Middle", limit=1, context_lines=1)

    assert "Match 1: line 3 (showing 2-4)" in result
    assert "  2: BARGRAPH command" in result
    assert "> 3: Middle context" in result
    assert "  4: bargraph lowercase match" in result


def test_search_manual_limits_result_count(sample_manual):
    result = server.search_manual("bargraph", limit=1, context_lines=0)

    assert "Found 1 matches for 'bargraph'." in result
    assert "BARGRAPH command" in result
    assert "bargraph lowercase match" not in result


def test_search_manual_clamps_limit_to_minimum(sample_manual):
    result = server.search_manual("bargraph", limit=0, context_lines=0)

    assert "Found 1 matches for 'bargraph'." in result


def test_search_manual_clamps_limit_to_maximum(write_manual):
    write_manual("\n".join(f"hit line {index}" for index in range(25)) + "\n")

    result = server.search_manual("hit", limit=99, context_lines=0)

    assert "Found 20 matches for 'hit'." in result
    assert "Match 20: line 20" in result
    assert "Match 21" not in result


def test_search_manual_clamps_context_lines_to_maximum(write_manual):
    lines = [f"line {index}" for index in range(1, 31)]
    lines[15] = "needle line"
    write_manual("\n".join(lines) + "\n")

    result = server.search_manual("needle", limit=1, context_lines=99)

    assert "Match 1: line 16 (showing 6-26)" in result
    assert "  6: line 6" in result
    assert "> 16: needle line" in result
    assert "  26: line 26" in result


def test_search_manual_rejects_empty_query(sample_manual):
    with pytest.raises(ValueError, match="query must be a non-empty string"):
        server.search_manual("   ")


def test_search_manual_reports_no_matches(sample_manual):
    result = server.search_manual("not-present")

    assert result == "No manual matches found for 'not-present'."


def test_search_manual_reports_missing_manual(monkeypatch: pytest.MonkeyPatch, tmp_path):
    missing = tmp_path / "missing.txt"
    monkeypatch.setenv("TOPDRAWER_MANUAL_PATH", str(missing))
    server._manual_for_path.cache_clear()

    with pytest.raises(OSError, match="Unable to read manual text"):
        server.search_manual("anything")


def test_create_server_returns_fastmcp_server():
    assert server.create_server() is not None


def test_create_server_registers_search_and_render_tools():
    tool_names = {
        tool.name for tool in asyncio.run(server.create_server().list_tools())
    }

    assert "search_manual" in tool_names
    assert "render_topdrawer_file" in tool_names
