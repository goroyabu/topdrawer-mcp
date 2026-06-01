from __future__ import annotations

from pathlib import Path

import pytest

from topdrawer_mcp.script_scan import scan_topdrawer_script_file


pytestmark = pytest.mark.unit


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "topdrawer"


def test_basic_plot_fixture_scans_as_one_plot_command():
    result = scan_topdrawer_script_file(
        str(FIXTURE_ROOT / "plotting" / "scatter" / "basic-plot.top")
    )

    assert result["commands"] == [
        {
            "line": 4,
            "raw": "plot",
            "normalized": "PLOT",
            "kind": "command",
        }
    ]
    assert result["summary"]["counts"] == {"PLOT": 1}
    assert result["checks"] == []


def test_basic_join_fixture_scans_as_one_join_command():
    result = scan_topdrawer_script_file(
        str(FIXTURE_ROOT / "plotting" / "join" / "basic-join.top")
    )

    assert result["commands"] == [
        {
            "line": 4,
            "raw": "join",
            "normalized": "JOIN",
            "kind": "command",
        }
    ]
    assert result["summary"]["counts"] == {"JOIN": 1}
    assert result["checks"] == []
