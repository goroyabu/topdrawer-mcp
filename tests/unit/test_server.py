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
    assert "render_topdrawer_script" in tool_names
    assert "list_manual_samples" in tool_names
    assert "get_manual_sample" in tool_names
    assert "lookup_command" in tool_names


def test_render_topdrawer_script_rejects_empty_script():
    with pytest.raises(ValueError, match="script must be a non-empty string"):
        server.render_topdrawer_script("   ")


def test_render_topdrawer_script_uses_shared_render_core(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_render(source_text: str, **kwargs):
        captured["source_text"] = source_text
        captured["kwargs"] = kwargs
        return {
            "output_path": "/tmp/render.png",
            "td_executable": "/bin/td",
            "success": True,
            "message": "ok",
        }

    monkeypatch.setattr(server, "render_topdrawer_source_text", fake_render)

    result = server.render_topdrawer_script(
        "plot\n",
        base_dir="samples",
        output_path="out.png",
        overwrite=True,
    )

    assert captured["source_text"] == "plot\n"
    assert captured["kwargs"] == {
        "base_dir": "samples",
        "output_path": "out.png",
        "overwrite": True,
    }
    assert result["success"] is True


def test_list_manual_samples_returns_structured_entries():
    result = server.list_manual_samples(category="histogram")

    assert result == {
        "samples": [
            {
                "id": "histogram-basic",
                "title": "Basic histogram",
                "category": "histogram",
                "description": "Draws a simple histogram from point-like x/y input pairs.",
                "primary_commands": ["HISTOGRAM"],
            }
        ]
    }


def test_get_manual_sample_returns_structured_entry():
    result = server.get_manual_sample("scatter-error-bars")

    assert result["id"] == "scatter-error-bars"
    assert result["category"] == "scatter"


def test_lookup_command_returns_title_entry():
    result = server.lookup_command("TITLE")

    assert result["command"] == "TITLE"
    assert result["section"] == "15.72"


def test_lookup_command_resolves_symbol_alias():
    result = server.lookup_command("SYMBOL")

    assert result["command"] == "SET SYMBOL"
    assert result["kind"] == "set-subcommand"


def test_lookup_command_returns_case_modifier_entry():
    result = server.lookup_command("CASE")

    assert result["command"] == "CASE"
    assert result["kind"] == "modifier"
    assert result["parent_command"] == "TITLE"
