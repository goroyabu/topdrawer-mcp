from __future__ import annotations

import json

import pytest

from topdrawer_mcp.preprocess import cli


pytestmark = pytest.mark.unit


def test_run_writes_command_index(tmp_path, capsys: pytest.CaptureFixture[str]):
    source = tmp_path / "topdrawer.doc"
    output_dir = tmp_path / "index"
    targets = tmp_path / "targets.json"
    reviewed = tmp_path / "reviewed.json"
    source.write_text(
        "\n".join(
            [
                "     15.1  FORMAT_OF_COMMANDS ",
                "     format text",
                "     15.64.56  SYMBOL",
                '     SET SYMBOL "xx" [SIZE=n]',
                "     15.72  TITLE ",
                "     title text",
                "     TITLE [x] 'text_of_title'",
                "     15.72.16  CASE",
                "     case text",
                "          CASE 'case_text'",
                "     16.1  LIST_OF_NAMES ",
            ]
        ),
        encoding="utf-8",
    )
    targets.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {"command": "TITLE", "aliases": [], "kind": "command", "section": "15.72"},
                    {
                        "command": "CASE",
                        "aliases": [],
                        "kind": "modifier",
                        "parent_command": "TITLE",
                        "section": "15.72.16",
                    },
                    {
                        "command": "SET SYMBOL",
                        "aliases": ["SYMBOL"],
                        "kind": "set-subcommand",
                        "parent_command": "SET",
                        "section": "15.64.56",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    reviewed.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "command": "TITLE",
                        "summary": "title summary",
                        "important_rules": ["quoted text required"],
                        "option_groups": [],
                    },
                    {
                        "command": "CASE",
                        "summary": "case summary",
                        "important_rules": ["must follow TITLE"],
                        "option_groups": [],
                    },
                    {
                        "command": "SET SYMBOL",
                        "summary": "symbol summary",
                        "important_rules": ["only 0O to 9O are centered"],
                        "option_groups": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.run(
        [
            "--source",
            str(source),
            "--output-dir",
            str(output_dir),
            "--lookup-targets",
            str(targets),
            "--lookup-reviewed",
            str(reviewed),
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Wrote 2 command entries" in output
    assert "Wrote 3 command lookup entries" in output
    generated = output_dir / "command-index.json"
    generated_lookup = output_dir / "command-lookup-index.json"
    parsed = json.loads(generated.read_text(encoding="utf-8"))
    parsed_lookup = json.loads(generated_lookup.read_text(encoding="utf-8"))
    assert [entry["command"] for entry in parsed["entries"]] == [
        "FORMAT OF COMMANDS",
        "TITLE",
    ]
    assert [entry["command"] for entry in parsed_lookup["entries"]] == [
        "TITLE",
        "CASE",
        "SET SYMBOL",
    ]
    assert parsed_lookup["entries"][0]["section"] == "15.72"
    assert parsed_lookup["entries"][2]["aliases"] == ["SYMBOL"]
