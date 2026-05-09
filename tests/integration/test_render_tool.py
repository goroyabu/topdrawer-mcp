from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from topdrawer_mcp import render


pytestmark = pytest.mark.integration


def _assert_png_file(path: Path):
    assert path.exists()
    file_result = subprocess.run(
        ["file", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PNG image data" in file_result.stdout


def test_render_topdrawer_input_renders_error_bar_sample(tmp_path: Path):
    if shutil.which("td") is None or shutil.which("gs") is None:
        pytest.skip("td and gs are required for render integration tests")

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

    result = render.render_topdrawer_input(
        str(input_path),
        output_path=str(output_path),
    )

    assert result["success"] is True
    assert Path(result["output_path"]) == output_path.resolve()
    _assert_png_file(output_path)


def test_render_topdrawer_input_renders_manual_style_symbol_sample(tmp_path: Path):
    if shutil.which("td") is None or shutil.which("gs") is None:
        pytest.skip("td and gs are required for render integration tests")

    input_path = tmp_path / "manual-style.top"
    output_path = tmp_path / "manual-style.png"
    input_path.write_text(
        "set font duplex\n"
        "set device postscript orientation=3\n"
        "set order x y symbol\n"
        "1 1 4P\n"
        "2 4 5P\n"
        "3 9 6P\n"
        "4 16 AG\n"
        "5 25 PI\n"
        "plot size=5\n",
        encoding="utf-8",
    )

    result = render.render_topdrawer_input(
        str(input_path),
        output_path=str(output_path),
    )

    assert result["success"] is True
    assert Path(result["output_path"]) == output_path.resolve()
    _assert_png_file(output_path)


def test_render_topdrawer_input_fails_when_output_exists(tmp_path: Path):
    if shutil.which("td") is None or shutil.which("gs") is None:
        pytest.skip("td and gs are required for render integration tests")

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
    output_path.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Output file already exists"):
        render.render_topdrawer_input(
            str(input_path),
            output_path=str(output_path),
            overwrite=False,
        )
