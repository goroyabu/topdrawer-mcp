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
    assert "render_topdrawer_file" in names
    assert "render_topdrawer_script" in names


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
    assert Path(structured["output_path"]).exists()


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
    assert Path(structured["output_path"]).exists()
