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


def _run_inspector(manual_path: Path, *args: str) -> dict:
    if shutil.which("node") is None or shutil.which("npx") is None:
        pytest.skip("Node.js and npx are required for Inspector integration tests")

    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")

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
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=REPO_ROOT,
        env=env,
    )
    return json.loads(result.stdout)


def test_inspector_lists_search_manual(write_manual):
    manual_path = write_manual("BARGRAPH command\n")

    response = _run_inspector(manual_path, "--method", "tools/list")

    names = [tool["name"] for tool in response["tools"]]
    assert "search_manual" in names


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
