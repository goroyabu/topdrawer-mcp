from __future__ import annotations

from pathlib import Path

import pytest

from topdrawer_mcp import script_scan
from topdrawer_mcp.script_scan import scan_topdrawer_script_file
from topdrawer_mcp.script_scan import scan_topdrawer_script_text


pytestmark = pytest.mark.unit


def test_scan_topdrawer_script_detects_known_commands():
    result = scan_topdrawer_script_text(
        "\n".join(
            [
                "set window x 0 13 y 0 10",
                "set limits x 0 to 5 y 0 to 6",
                "plot axis",
                'title top "Example"',
                'case "GGGGGGG"',
                "plot",
            ]
        )
        + "\n"
    )

    assert result["commands"] == [
        {
            "line": 1,
            "raw": "set window x 0 13 y 0 10",
            "normalized": "SET WINDOW",
            "kind": "set-subcommand",
        },
        {
            "line": 2,
            "raw": "set limits x 0 to 5 y 0 to 6",
            "normalized": "SET LIMITS",
            "kind": "set-subcommand",
        },
        {
            "line": 3,
            "raw": "plot axis",
            "normalized": "PLOT",
            "kind": "command",
        },
        {
            "line": 4,
            "raw": 'title top "Example"',
            "normalized": "TITLE",
            "kind": "command",
        },
        {
            "line": 5,
            "raw": 'case "GGGGGGG"',
            "normalized": "CASE",
            "kind": "modifier",
        },
        {
            "line": 6,
            "raw": "plot",
            "normalized": "PLOT",
            "kind": "command",
        },
    ]
    assert result == {
        "commands": [
            {
                "line": 1,
                "raw": "set window x 0 13 y 0 10",
                "normalized": "SET WINDOW",
                "kind": "set-subcommand",
            },
            {
                "line": 2,
                "raw": "set limits x 0 to 5 y 0 to 6",
                "normalized": "SET LIMITS",
                "kind": "set-subcommand",
            },
            {
                "line": 3,
                "raw": "plot axis",
                "normalized": "PLOT",
                "kind": "command",
            },
            {
                "line": 4,
                "raw": 'title top "Example"',
                "normalized": "TITLE",
                "kind": "command",
            },
            {
                "line": 5,
                "raw": 'case "GGGGGGG"',
                "normalized": "CASE",
                "kind": "modifier",
            },
            {
                "line": 6,
                "raw": "plot",
                "normalized": "PLOT",
                "kind": "command",
            },
        ]
    }


def test_scan_topdrawer_script_ignores_non_command_lines_and_comments():
    result = scan_topdrawer_script_text(
        "\n".join(
            [
                "! comment",
                "# comment",
                "1 2 3 4",
                "th=0 to 360 step 1",
                "plot",
            ]
        )
        + "\n"
    )

    assert result["commands"] == [
        {
            "line": 5,
            "raw": "plot",
            "normalized": "PLOT",
            "kind": "command",
        }
    ]
    assert result == {
        "commands": [
            {
                "line": 5,
                "raw": "plot",
                "normalized": "PLOT",
                "kind": "command",
            }
        ]
    }


def test_scan_topdrawer_script_recognizes_read():
    result = scan_topdrawer_script_text(
        "\n".join(
            [
                "read points",
                "set gridd on",
                "set label bottom off",
            ]
        )
        + "\n"
    )

    assert result["commands"] == [
        {
            "line": 1,
            "raw": "read points",
            "normalized": "READ",
            "kind": "command",
        }
    ]
    assert result == {
        "commands": [
            {
                "line": 1,
                "raw": "read points",
                "normalized": "READ",
                "kind": "command",
            }
        ]
    }


def test_scan_topdrawer_script_file_reads_and_scans_file(tmp_path: Path):
    input_path = tmp_path / "sample.top"
    input_path.write_text("set window x 0 13 y 0 10\nplot\n", encoding="utf-8")

    result = scan_topdrawer_script_file(str(input_path))

    assert result == {
        "commands": [
            {
                "line": 1,
                "raw": "set window x 0 13 y 0 10",
                "normalized": "SET WINDOW",
                "kind": "set-subcommand",
            },
            {
                "line": 2,
                "raw": "plot",
                "normalized": "PLOT",
                "kind": "command",
            },
        ]
    }


def test_known_set_subcommand_names_include_manual_and_alias_coverage():
    names = script_scan._known_set_subcommand_names()

    assert "WINDOWS" in names
    assert "LABELS" in names
    assert "ORDER" in names
    assert "FONT" in names


def test_scan_topdrawer_script_rejects_empty_script():
    with pytest.raises(ValueError, match="script must be a non-empty string"):
        scan_topdrawer_script_text("   ")


def test_scan_topdrawer_script_file_rejects_empty_path():
    with pytest.raises(ValueError, match="input_path must be a non-empty string"):
        scan_topdrawer_script_file("   ")
