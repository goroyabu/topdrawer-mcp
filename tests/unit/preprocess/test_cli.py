from __future__ import annotations

import json

import pytest

from topdrawer_mcp.preprocess import cli


pytestmark = pytest.mark.unit


def test_run_writes_command_index(tmp_path, capsys: pytest.CaptureFixture[str]):
    source = tmp_path / "topdrawer.doc"
    output_dir = tmp_path / "index"
    source.write_text(
        "\n".join(
            [
                "     15.1  FORMAT_OF_COMMANDS ",
                "     format text",
                "     15.10  BARGRAPH ",
                "     bargraph text",
                "     16.1  LIST_OF_NAMES ",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = cli.run(["--source", str(source), "--output-dir", str(output_dir)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Wrote 2 command entries" in output
    generated = output_dir / "command-index.json"
    parsed = json.loads(generated.read_text(encoding="utf-8"))
    assert [entry["command"] for entry in parsed["entries"]] == [
        "FORMAT OF COMMANDS",
        "BARGRAPH",
    ]
