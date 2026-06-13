from __future__ import annotations

import asyncio
import json

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

    with pytest.raises(OSError, match="get_server_runtime_info"):
        server.search_manual("anything")


def test_create_server_returns_fastmcp_server():
    assert server.create_server() is not None


def test_create_server_registers_search_and_render_tools():
    tool_names = {
        tool.name for tool in asyncio.run(server.create_server().list_tools())
    }

    assert "search_manual" in tool_names
    assert "generate_topdrawer_png" in tool_names
    assert "generate_topdrawer_postscript" in tool_names
    assert "render_topdrawer_file" in tool_names
    assert "render_topdrawer_script" in tool_names
    assert "list_manual_samples" in tool_names
    assert "get_manual_sample" in tool_names
    assert "lookup_command" in tool_names
    assert "get_server_runtime_info" in tool_names
    assert "scan_topdrawer_script" in tool_names
    assert "scan_topdrawer_file" in tool_names


def test_create_server_registers_resources_and_prompts():
    resource_uris = {
        str(resource.uri) for resource in asyncio.run(server.create_server().list_resources())
    }
    template_uris = {
        template.uriTemplate
        for template in asyncio.run(server.create_server().list_resource_templates())
    }
    prompt_names = {
        prompt.name for prompt in asyncio.run(server.create_server().list_prompts())
    }

    assert resource_uris == {"resource://commands/index"}
    assert "resource://commands/{command}" in template_uris
    assert "resource://commands/{parent}/{command}" in template_uris
    assert "resource://artifacts/{artifact_id}" in template_uris
    assert "resource://artifacts/{artifact_id}/output" in template_uris
    assert "resource://artifacts/{artifact_id}/source" in template_uris
    assert "resource://artifacts/{artifact_id}/metadata" in template_uris
    assert "inspect_topdrawer_script" in prompt_names
    assert "discover_topdrawer_command" in prompt_names


def test_command_index_resource_returns_known_entries():
    contents = list(
        asyncio.run(
            server.create_server().read_resource("resource://commands/index")
        )
    )

    payload = json.loads(contents[0].content)

    assert payload["entry_count"] >= 5
    assert {"command", "kind", "section", "title", "uri"} <= set(payload["entries"][0].keys())
    assert any(entry["command"] == "PLOT" for entry in payload["entries"])
    assert any(entry["command"] == "TITLE" for entry in payload["entries"])
    assert any(entry["command"] == "SET ORDER" for entry in payload["entries"])
    assert any(entry["uri"] == "resource://commands/title" for entry in payload["entries"])
    assert any(entry["uri"] == "resource://commands/set/order" for entry in payload["entries"])
    assert any(entry["uri"] == "resource://commands/title/case" for entry in payload["entries"])


def test_single_command_resource_returns_full_reviewed_entry():
    contents = list(
        asyncio.run(
            server.create_server().read_resource("resource://commands/title")
        )
    )

    payload = json.loads(contents[0].content)

    assert payload["command"] == "TITLE"
    assert payload["section"] == "15.72"
    assert "summary" in payload
    assert "raw_text" in payload


def test_set_subcommand_resource_returns_full_reviewed_entry():
    contents = list(
        asyncio.run(
            server.create_server().read_resource("resource://commands/set/order")
        )
    )

    payload = json.loads(contents[0].content)

    assert payload["command"] == "SET ORDER"
    assert payload["kind"] == "set-subcommand"
    assert payload["parent_command"] == "SET"


def test_modifier_resource_returns_full_reviewed_entry():
    contents = list(
        asyncio.run(
            server.create_server().read_resource("resource://commands/title/case")
        )
    )

    payload = json.loads(contents[0].content)

    assert payload["command"] == "CASE"
    assert payload["kind"] == "modifier"
    assert payload["parent_command"] == "TITLE"


def test_artifact_manifest_resource_reads_manager_payload(monkeypatch: pytest.MonkeyPatch):
    class FakeManager:
        def read_manifest(self, artifact_id: str):
            return {"artifact_id": artifact_id, "format": "png"}

    monkeypatch.setattr(server, "get_artifact_manager", lambda: FakeManager())

    contents = list(
        asyncio.run(
            server.create_server().read_resource("resource://artifacts/tdart_test")
        )
    )

    payload = json.loads(contents[0].content)
    assert payload["artifact_id"] == "tdart_test"


def test_artifact_output_resource_reads_manager_payload(monkeypatch: pytest.MonkeyPatch):
    class FakeManager:
        def read_output(self, artifact_id: str):
            return b"\x89PNG\r\n\x1a\n"

        def load_artifact(self, artifact_id: str):
            class FakeArtifact:
                output_mime_type = "image/png"

            return FakeArtifact()

    monkeypatch.setattr(server, "get_artifact_manager", lambda: FakeManager())

    contents = list(
        asyncio.run(
            server.create_server().read_resource("resource://artifacts/tdart_test/output")
        )
    )

    assert contents[0].content == b"\x89PNG\r\n\x1a\n"
    assert contents[0].mime_type == "image/png"


def test_artifact_output_resource_uses_postscript_mime_type(monkeypatch: pytest.MonkeyPatch):
    class FakeManager:
        def read_output(self, artifact_id: str):
            return "%!PS-Adobe-1.0\n"

        def load_artifact(self, artifact_id: str):
            class FakeArtifact:
                output_mime_type = "application/postscript"

            return FakeArtifact()

    monkeypatch.setattr(server, "get_artifact_manager", lambda: FakeManager())

    contents = list(
        asyncio.run(
            server.create_server().read_resource("resource://artifacts/tdart_test/output")
        )
    )

    assert contents[0].mime_type == "application/postscript"


def test_single_command_resource_rejects_unknown_canonical_path():
    with pytest.raises(ValueError, match="Unknown command lookup entry"):
        list(
            asyncio.run(
                server.create_server().read_resource("resource://commands/missing")
            )
        )


def test_inspect_topdrawer_script_prompt_returns_scan_lookup_flow():
    result = asyncio.run(
        server.create_server().get_prompt(
            "inspect_topdrawer_script",
            {"script_text": "plot\n", "goal": "understand the script"},
        )
    )

    message_text = result.messages[0].content.text
    assert "scan_topdrawer_script" in message_text
    assert "lookup_command" in message_text
    assert "search_manual" in message_text


def test_inspect_topdrawer_script_prompt_requires_exactly_one_input_source():
    with pytest.raises(ValueError, match="exactly one of script_text or input_path"):
        asyncio.run(
            server.create_server().get_prompt(
                "inspect_topdrawer_script",
                {"script_text": "plot\n", "input_path": "sample.top"},
            )
        )


def test_discover_topdrawer_command_prompt_returns_search_lookup_flow():
    result = asyncio.run(
        server.create_server().get_prompt(
            "discover_topdrawer_command",
            {"query": "polar plot", "context": "user wants a polar chart"},
        )
    )

    message_text = result.messages[0].content.text
    assert "search_manual" in message_text
    assert "lookup_command" in message_text


def test_render_topdrawer_script_rejects_empty_script():
    with pytest.raises(ValueError, match="script must be a non-empty string"):
        server.render_topdrawer_script("   ")


def test_render_topdrawer_script_uses_shared_render_core(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_render(source_text: str, **kwargs):
        captured["source_text"] = source_text
        captured["kwargs"] = kwargs
        return {
            "success": True,
            "format": "png",
            "message": "ok",
            "artifact_id": "tdart_test",
            "resource_uri": "resource://artifacts/tdart_test",
            "metadata": {},
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


def test_generate_topdrawer_png_uses_render_core(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_generate(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "success": True,
            "format": "png",
            "message": "ok",
            "artifact_id": "tdart_test",
            "resource_uri": "resource://artifacts/tdart_test",
            "metadata": {},
        }

    monkeypatch.setattr(server, "generate_topdrawer_png_core", fake_generate)

    result = server.generate_topdrawer_png(
        script="plot\n",
        base_dir="samples",
        output_path="out.png",
        overwrite=True,
        dpi=200,
        padding=24,
        crop=False,
        background="transparent",
    )

    assert captured["kwargs"] == {
        "input_path": None,
        "script": "plot\n",
        "base_dir": "samples",
        "output_path": "out.png",
        "overwrite": True,
        "dpi": 200,
        "padding": 24,
        "crop": False,
        "background": "transparent",
    }
    assert result["format"] == "png"


def test_generate_topdrawer_postscript_uses_render_core(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_generate(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "success": True,
            "format": "postscript",
            "message": "ok",
            "artifact_id": "tdart_test",
            "resource_uri": "resource://artifacts/tdart_test",
            "metadata": {},
        }

    monkeypatch.setattr(server, "generate_topdrawer_postscript_core", fake_generate)

    result = server.generate_topdrawer_postscript(
        input_path="sample.top",
        output_path="out.ps",
        overwrite=True,
    )

    assert captured["kwargs"] == {
        "input_path": "sample.top",
        "script": None,
        "base_dir": None,
        "output_path": "out.ps",
        "overwrite": True,
    }
    assert result["format"] == "postscript"


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


def test_lookup_command_returns_delete_entry():
    result = server.lookup_command("DELETE")

    assert result["command"] == "DELETE"
    assert result["kind"] == "command"
    assert result["section"] == "15.19"


def test_lookup_command_resolves_symbol_alias():
    result = server.lookup_command("SYMBOL")

    assert result["command"] == "SET SYMBOL"
    assert result["kind"] == "set-subcommand"


def test_lookup_command_returns_case_modifier_entry():
    result = server.lookup_command("CASE")

    assert result["command"] == "CASE"
    assert result["kind"] == "modifier"
    assert result["parent_command"] == "TITLE"


def test_lookup_command_returns_set_order_entry():
    result = server.lookup_command("SET ORDER")

    assert result["command"] == "SET ORDER"
    assert result["kind"] == "set-subcommand"
    assert result["parent_command"] == "SET"


def test_lookup_command_returns_set_font_entry():
    result = server.lookup_command("SET FONT")

    assert result["command"] == "SET FONT"
    assert result["kind"] == "set-subcommand"
    assert result["parent_command"] == "SET"


def test_lookup_command_returns_set_polar_entry():
    result = server.lookup_command("SET POLAR")

    assert result["command"] == "SET POLAR"
    assert result["kind"] == "set-subcommand"
    assert result["parent_command"] == "SET"


@pytest.mark.parametrize("command", ["PLOT AXIS", "PLOT TITLE", "TITLE DATA"])
def test_lookup_command_rejects_non_standalone_phrases(command: str):
    with pytest.raises(ValueError, match="Unknown command lookup entry"):
        server.lookup_command(command)


def test_lookup_command_rejects_delete_abbreviation():
    with pytest.raises(ValueError, match="Unknown command lookup entry"):
        server.lookup_command("DEL")


def test_get_server_runtime_info_uses_runtime_info_helper(monkeypatch: pytest.MonkeyPatch):
    expected = {
        "manual": {
            "env_var": "TOPDRAWER_MANUAL_PATH",
            "configured_path": None,
            "resolved_path": "/tmp/manual.txt",
            "exists": True,
            "source": "default",
            "error": None,
            "user_action": [],
        },
        "command_lookup_sources": [],
        "render": {
            "available": False,
            "td": {
                "env_var": "TD_EXECUTABLE_PATH",
                "configured_path": None,
                "resolved_path": None,
                "available": False,
                "error": "missing td",
            },
            "gs": {
                "env_var": "GS_EXECUTABLE_PATH",
                "configured_path": None,
                "resolved_path": None,
                "available": False,
                "error": "missing gs",
            },
            "missing_requirements": ["td", "gs"],
            "user_action": ["step 1", "step 2"],
        },
    }
    monkeypatch.setattr(server, "get_runtime_info", lambda: expected)

    assert server.get_server_runtime_info() == expected


def test_scan_topdrawer_script_uses_script_scan_helper(monkeypatch: pytest.MonkeyPatch):
    expected = {"commands": []}
    monkeypatch.setattr(server, "scan_topdrawer_script_text", lambda script: expected)

    assert server.scan_topdrawer_script("plot\n") == expected


def test_scan_topdrawer_file_uses_script_scan_file_helper(monkeypatch: pytest.MonkeyPatch):
    expected = {"commands": []}
    monkeypatch.setattr(server, "scan_topdrawer_script_file", lambda path: expected)

    assert server.scan_topdrawer_file("example.top") == expected
