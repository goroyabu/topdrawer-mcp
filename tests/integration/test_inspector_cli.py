from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]
INSPECTOR_PACKAGE = "@modelcontextprotocol/inspector@0.21.2"
INSPECTOR_TIMEOUT_SECONDS = 10


def _run_inspector(manual_path: Path, *args: str) -> dict:
    if shutil.which("node") is None or shutil.which("npx") is None:
        pytest.skip("Node.js and npx are required for Inspector integration tests")

    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")
    env.setdefault("UV_CACHE_DIR", "/private/tmp/uv-cache")

    command = [
        "npx",
        "-y",
        INSPECTOR_PACKAGE,
        "--cli",
        "-e",
        f"TOPDRAWER_MANUAL_PATH={manual_path}",
        "uv",
        "--directory",
        str(REPO_ROOT),
        "run",
        "topdrawer-mcp",
        *args,
    ]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=INSPECTOR_TIMEOUT_SECONDS,
            cwd=REPO_ROOT,
            env=env,
        )
    except subprocess.TimeoutExpired:
        pytest.skip(
            f"Inspector CLI did not complete within {INSPECTOR_TIMEOUT_SECONDS} seconds in this environment"
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        pytest.skip(
            "Inspector CLI failed in this environment"
            + (f": {stderr}" if stderr else "")
        )
    return json.loads(result.stdout)


def test_inspector_lists_search_manual(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(manual_path, "--method", "tools/list")

    names = [tool["name"] for tool in response["tools"]]
    assert "search_manual" in names
    assert "generate_topdrawer_png" in names
    assert "generate_topdrawer_postscript" in names
    assert "render_topdrawer_file" in names
    assert "render_topdrawer_script" in names
    assert "list_manual_samples" in names
    assert "get_manual_sample" in names
    assert "lookup_command" in names
    assert "get_server_runtime_info" in names
    assert "scan_topdrawer_script" in names
    assert "scan_topdrawer_file" in names


def test_inspector_lists_resources(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(manual_path, "--method", "resources/list")

    uris = [resource["uri"] for resource in response["resources"]]
    assert uris == ["resource://commands/index"]


def test_inspector_lists_resource_templates(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(manual_path, "--method", "resources/templates/list")

    uri_templates = [template["uriTemplate"] for template in response["resourceTemplates"]]
    assert "resource://commands/{command}" in uri_templates
    assert "resource://commands/{parent}/{command}" in uri_templates


def test_inspector_reads_command_index_resource(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(
        manual_path,
        "--method",
        "resources/read",
        "--uri",
        "resource://commands/index",
    )

    content = response["contents"][0]
    assert content["mimeType"] == "application/json"
    assert "\"command\": \"PLOT\"" in content["text"]


def test_inspector_reads_set_order_command_resource(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(
        manual_path,
        "--method",
        "resources/read",
        "--uri",
        "resource://commands/set/order",
    )

    content = response["contents"][0]
    assert content["mimeType"] == "application/json"
    assert "\"command\": \"SET ORDER\"" in content["text"]


def test_inspector_lists_prompts(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(manual_path, "--method", "prompts/list")

    names = [prompt["name"] for prompt in response["prompts"]]
    assert "inspect_topdrawer_script" in names
    assert "discover_topdrawer_command" in names


def test_inspector_gets_inspect_topdrawer_script_prompt(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(
        manual_path,
        "--method",
        "prompts/get",
        "--prompt-name",
        "inspect_topdrawer_script",
        "--prompt-args",
        "script_text=plot",
        "--prompt-args",
        "goal=understand the script",
    )

    message = response["messages"][0]["content"]["text"]
    assert "scan_topdrawer_script" in message
    assert "lookup_command" in message
    assert "search_manual" in message


def test_inspector_gets_discover_topdrawer_command_prompt(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(
        manual_path,
        "--method",
        "prompts/get",
        "--prompt-name",
        "discover_topdrawer_command",
        "--prompt-args",
        "query=polar plot",
        "--prompt-args",
        "context=user wants a polar chart",
    )

    message = response["messages"][0]["content"]["text"]
    assert "search_manual" in message
    assert "lookup_command" in message


def test_inspector_calls_search_manual(write_manual):
    manual_path = write_manual("Intro line\nBARGRAPH command\nFinal line\n")

    response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "search_manual",
        "--tool-arg",
        "query=BARGRAPH",
        "--tool-arg",
        "limit=1",
        "--tool-arg",
        "context_lines=0",
    )

    assert response["isError"] is False
    text = response["content"][0]["text"]
    assert "Found 1 matches for 'BARGRAPH'." in text
    assert "> 2: BARGRAPH command" in text


def test_inspector_calls_list_manual_samples(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "list_manual_samples",
        "--tool-arg",
        "category=histogram",
        "--tool-arg",
        "command=HISTOGRAM",
    )

    assert response["isError"] is False
    structured = response["structuredContent"]
    assert structured["samples"] == [
        {
            "id": "histogram-basic",
            "title": "Basic histogram",
            "category": "histogram",
            "description": "Draws a simple histogram from point-like x/y input pairs.",
            "primary_commands": ["HISTOGRAM"],
        }
    ]


def test_inspector_calls_get_manual_sample(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "get_manual_sample",
        "--tool-arg",
        "sample_id=scatter-error-bars",
    )

    assert response["isError"] is False
    structured = response["structuredContent"]
    assert structured["id"] == "scatter-error-bars"
    assert structured["category"] == "scatter"


def test_inspector_calls_lookup_command_title(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "lookup_command",
        "--tool-arg",
        "command=TITLE",
    )

    assert response["isError"] is False
    structured = response["structuredContent"]
    assert structured["command"] == "TITLE"
    assert structured["section"] == "15.72"


def test_inspector_calls_lookup_command_symbol_alias(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "lookup_command",
        "--tool-arg",
        "command=SYMBOL",
    )

    assert response["isError"] is False
    structured = response["structuredContent"]
    assert structured["command"] == "SET SYMBOL"
    assert structured["kind"] == "set-subcommand"


def test_inspector_calls_get_server_runtime_info(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "get_server_runtime_info",
    )

    assert response["isError"] is False
    structured = response["structuredContent"]
    assert structured["manual"]["source"] == "env"
    assert structured["manual"]["exists"] is True
    assert "render" in structured


def test_inspector_calls_render_topdrawer_file(write_manual, tmp_path: Path):
    if shutil.which("td") is None or shutil.which("gs") is None:
        pytest.skip("td and gs are required for render Inspector integration tests")

    manual_path = write_manual("BARGRAPH command\n")
    input_path = tmp_path / "input.top"
    output_path = tmp_path / "output.png"
    input_path.write_text(
        "set symbol 1P\n"
        "set order y x dx dy\n"
        "100 1 0.5 10\n"
        "144 2 0.5 12\n"
        "196 3 0.5 14\n"
        "plot\n",
        encoding="utf-8",
    )

    response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "render_topdrawer_file",
        "--tool-arg",
        f"input_path={input_path}",
        "--tool-arg",
        f"output_path={output_path}",
        "--tool-arg",
        "overwrite=true",
    )

    assert response["isError"] is False
    structured = response["structuredContent"]
    assert structured["success"] is True
    assert structured["artifact_id"]
    assert structured["resource_uri"].startswith("resource://artifacts/")
    assert Path(structured["metadata"]["output_path"]).exists()


def test_inspector_calls_generate_topdrawer_png(write_manual, tmp_path: Path):
    if shutil.which("td") is None or shutil.which("gs") is None:
        pytest.skip("td and gs are required for render Inspector integration tests")

    manual_path = write_manual("BARGRAPH command\n")
    output_path = tmp_path / "generated.png"

    response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "generate_topdrawer_png",
        "--tool-arg",
        "script=set symbol 1P\nset order y x dx dy\n100 1 0.5 10\n144 2 0.5 12\n196 3 0.5 14\nplot\n",
        "--tool-arg",
        f"output_path={output_path}",
        "--tool-arg",
        "overwrite=true",
        "--tool-arg",
        "background=transparent",
        "--tool-arg",
        "crop=false",
    )

    assert response["isError"] is False
    structured = response["structuredContent"]
    assert structured["success"] is True
    assert structured["format"] == "png"
    assert structured["artifact_id"]
    assert structured["resource_uri"].startswith("resource://artifacts/")
    assert Path(structured["metadata"]["output_path"]).exists()


def test_inspector_calls_render_topdrawer_script(write_manual, tmp_path: Path):
    if shutil.which("td") is None or shutil.which("gs") is None:
        pytest.skip("td and gs are required for render Inspector integration tests")

    manual_path = write_manual("BARGRAPH command\n")
    output_path = tmp_path / "output-script.png"

    response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "render_topdrawer_script",
        "--tool-arg",
        "script=set symbol 1P\nset order y x dx dy\n100 1 0.5 10\n144 2 0.5 12\n196 3 0.5 14\nplot\n",
        "--tool-arg",
        f"output_path={output_path}",
        "--tool-arg",
        "overwrite=true",
    )

    assert response["isError"] is False
    structured = response["structuredContent"]
    assert structured["success"] is True
    assert structured["artifact_id"]
    assert Path(structured["metadata"]["output_path"]).exists()


def test_inspector_calls_generate_topdrawer_postscript(write_manual, tmp_path: Path):
    if shutil.which("td") is None:
        pytest.skip("td is required for PostScript Inspector integration tests")

    manual_path = write_manual("BARGRAPH command\n")
    output_path = tmp_path / "generated.ps"

    response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "generate_topdrawer_postscript",
        "--tool-arg",
        "script=set symbol 1P\nset order y x dx dy\n100 1 0.5 10\n144 2 0.5 12\n196 3 0.5 14\nplot\n",
        "--tool-arg",
        f"output_path={output_path}",
        "--tool-arg",
        "overwrite=true",
    )

    assert response["isError"] is False
    structured = response["structuredContent"]
    assert structured["success"] is True
    assert structured["format"] == "postscript"
    assert structured["artifact_id"]
    assert structured["resource_uri"].startswith("resource://artifacts/")
    assert Path(structured["metadata"]["output_path"]).exists()


def test_inspector_reads_generated_artifact_manifest_and_output(write_manual, tmp_path: Path):
    if shutil.which("td") is None or shutil.which("gs") is None:
        pytest.skip("td and gs are required for render Inspector integration tests")

    manual_path = write_manual("BARGRAPH command\n")
    output_path = tmp_path / "generated-manifest.png"

    tool_response = _run_inspector(
        manual_path,
        "--method",
        "tools/call",
        "--tool-name",
        "generate_topdrawer_png",
        "--tool-arg",
        "script=set symbol 1P\nset order y x dx dy\n100 1 0.5 10\n144 2 0.5 12\n196 3 0.5 14\nplot\n",
        "--tool-arg",
        f"output_path={output_path}",
        "--tool-arg",
        "overwrite=true",
    )

    manifest_uri = tool_response["structuredContent"]["resource_uri"]
    manifest_response = _run_inspector(
        manual_path,
        "--method",
        "resources/read",
        "--uri",
        manifest_uri,
    )

    manifest_content = manifest_response["contents"][0]
    assert manifest_content["mimeType"] == "application/json"
    assert "\"artifact_id\"" in manifest_content["text"]

    artifact_id = tool_response["structuredContent"]["artifact_id"]
    output_response = _run_inspector(
        manual_path,
        "--method",
        "resources/read",
        "--uri",
        f"resource://artifacts/{artifact_id}/output",
    )

    output_content = output_response["contents"][0]
    assert output_content["mimeType"] == "image/png"
    assert output_content["blob"]
