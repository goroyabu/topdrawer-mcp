from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from topdrawer_mcp.render import render_topdrawer_input


pytestmark = pytest.mark.integration


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "topdrawer"


def _require_render_dependencies() -> None:
    if shutil.which("td") is None or shutil.which("gs") is None:
        pytest.skip("td and gs are required for render fixture integration tests")


def test_render_basic_plot_fixture(tmp_path: Path):
    _require_render_dependencies()

    input_path = FIXTURE_ROOT / "plotting" / "scatter" / "basic-plot.top"
    output_path = tmp_path / "basic-plot.png"

    result = render_topdrawer_input(
        str(input_path),
        output_path=str(output_path),
        overwrite=True,
    )

    assert result["success"] is True
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_render_basic_join_fixture(tmp_path: Path):
    _require_render_dependencies()

    input_path = FIXTURE_ROOT / "plotting" / "join" / "basic-join.top"
    output_path = tmp_path / "basic-join.png"

    result = render_topdrawer_input(
        str(input_path),
        output_path=str(output_path),
        overwrite=True,
    )

    assert result["success"] is True
    assert output_path.exists()
    assert output_path.stat().st_size > 0
