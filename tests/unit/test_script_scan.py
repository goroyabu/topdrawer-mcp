from __future__ import annotations

import pytest

from topdrawer_mcp.script_scan import scan_topdrawer_script_text


pytestmark = pytest.mark.unit


def test_scan_topdrawer_script_detects_known_commands_and_counts():
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
    assert result["summary"]["counts"] == {
        "CASE": 1,
        "PLOT": 2,
        "SET LIMITS": 1,
        "SET WINDOW": 1,
        "TITLE": 1,
    }
    assert result["checks"] == []


def test_scan_topdrawer_script_warns_when_case_does_not_follow_title_or_more():
    result = scan_topdrawer_script_text(
        "\n".join(
            [
                'title top "Example"',
                "plot",
                'case "GGGGGGG"',
            ]
        )
        + "\n"
    )

    assert result["checks"] == [
        {
            "severity": "warning",
            "line": 3,
            "message": "CASE should immediately follow TITLE or MORE.",
        }
    ]


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
    assert result["summary"]["counts"] == {"PLOT": 1}
    assert result["checks"] == []


def test_scan_topdrawer_script_rejects_empty_script():
    with pytest.raises(ValueError, match="script must be a non-empty string"):
        scan_topdrawer_script_text("   ")
