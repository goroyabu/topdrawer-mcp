from __future__ import annotations

import json

import pytest

from topdrawer_mcp.preprocess.lookup import build_command_lookup_entries
from topdrawer_mcp.preprocess.lookup import load_command_lookup_targets
from topdrawer_mcp.preprocess.lookup import load_reviewed_command_lookup_entries


pytestmark = pytest.mark.unit


def test_load_command_lookup_targets_and_reviewed_entries(tmp_path):
    targets_path = tmp_path / "targets.json"
    reviewed_path = tmp_path / "reviewed.json"
    targets_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "command": "SET SYMBOL",
                        "aliases": ["SYMBOL"],
                        "kind": "set-subcommand",
                        "parent_command": "SET",
                        "section": "15.64.56",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    reviewed_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "command": "SET SYMBOL",
                        "summary": "Sets the default plot symbol.",
                        "important_rules": ["Only 0O to 9O are centered."],
                        "option_groups": [
                            {"name": "symbol", "items": ['"xx"', "NONE", "DOT"]}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    targets = load_command_lookup_targets(targets_path)
    reviewed = load_reviewed_command_lookup_entries(reviewed_path)

    assert targets[0].command == "SET SYMBOL"
    assert targets[0].aliases == ["SYMBOL"]
    assert targets[0].parent_command == "SET"
    assert reviewed[0].option_groups[0].items == ['"xx"', "NONE", "DOT"]


def test_build_command_lookup_entries_uses_selected_sections_and_merges_reviewed_data(tmp_path):
    text = "\n".join(
        [
            "     15.1  FORMAT_OF_COMMANDS",
            "     format text",
            "     15.5  TITLE",
            "     Uses the name of the data set.",
            "     15.10  BARGRAPH",
            "     Produces a simple bar graph.",
            "     BARGRAPH [EXPAND]",
            "          [POINTS=[FROM] n1 [TO] [n2]]",
            "     15.40  HISTOGRAM",
            "     Draws a histogram.",
            "     HISTOGRAM [EXPAND]",
            "          [POINTS|COLUMNS [FROM] n1 [TO] n2]",
            "     15.64.56  SYMBOL",
            '     SET SYMBOL "xx" [SIZE=n] [THETA=n] [PHI=n] [ANGLE=n] [PERMANENT]',
            "     If no parameters are specified the symbol and size are set to NONE and 2.",
            "     15.72  TITLE",
            "     Puts a title on the plot",
            "     TITLE [x, [y, [z]]|CURSOR] 'text_of_title' [TIME] [lexicals]",
            "          [TOP|BOTTOM|RIGHT|LEFT|X|Y|Z|GENERAL]",
            "          [DATA|XDATA|YDATA|TEXT]",
            "     15.72.16  CASE",
            "     Controls the format of the title.",
            "          CASE 'case_text'",
            "     16.1  LIST_OF_NAMES",
        ]
    )
    targets_path = tmp_path / "targets.json"
    reviewed_path = tmp_path / "reviewed.json"
    targets_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {"command": "BARGRAPH", "aliases": [], "kind": "command", "section": "15.10"},
                    {"command": "TITLE", "aliases": [], "kind": "command", "section": "15.72"},
                    {
                        "command": "CASE",
                        "aliases": [],
                        "kind": "modifier",
                        "section": "15.72.16",
                        "parent_command": "TITLE",
                    },
                    {
                        "command": "SET SYMBOL",
                        "aliases": ["SYMBOL"],
                        "kind": "set-subcommand",
                        "section": "15.64.56",
                        "parent_command": "SET",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    reviewed_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "command": "BARGRAPH",
                        "summary": "bargraph summary",
                        "important_rules": ["uses Y"],
                        "option_groups": [{"name": "selection", "items": ["POINTS=[FROM] n1 [TO] [n2]"]}],
                    },
                    {
                        "command": "TITLE",
                        "summary": "title summary",
                        "important_rules": ["quoted text required"],
                        "option_groups": [{"name": "placement", "items": ["TOP|BOTTOM|RIGHT|LEFT|X|Y|Z|GENERAL"]}],
                    },
                    {
                        "command": "CASE",
                        "summary": "case summary",
                        "important_rules": ["must follow TITLE"],
                        "option_groups": [{"name": "syntax", "items": ["CASE 'case_text'"]}],
                    },
                    {
                        "command": "SET SYMBOL",
                        "summary": "symbol summary",
                        "important_rules": ["only 0O to 9O are centered"],
                        "option_groups": [{"name": "options", "items": ["SIZE=n", "ANGLE=n"]}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    targets = load_command_lookup_targets(targets_path)
    reviewed = load_reviewed_command_lookup_entries(reviewed_path)

    result = build_command_lookup_entries(text, targets, reviewed)

    title_entry = next(entry for entry in result if entry.command == "TITLE")
    case_entry = next(entry for entry in result if entry.command == "CASE")
    symbol_entry = next(entry for entry in result if entry.command == "SET SYMBOL")

    assert title_entry.section == "15.72"
    assert title_entry.syntax_lines == [
        "TITLE [x, [y, [z]]|CURSOR] 'text_of_title' [TIME] [lexicals]",
        "[TOP|BOTTOM|RIGHT|LEFT|X|Y|Z|GENERAL]",
        "[DATA|XDATA|YDATA|TEXT]",
    ]
    assert case_entry.parent_command == "TITLE"
    assert case_entry.syntax_lines == ["CASE 'case_text'"]
    assert symbol_entry.section == "15.64.56"
    assert symbol_entry.aliases == ["SYMBOL"]
    assert symbol_entry.syntax_lines == [
        'SET SYMBOL "xx" [SIZE=n] [THETA=n] [PHI=n] [ANGLE=n] [PERMANENT]'
    ]
    assert "Uses the name of the data set." not in title_entry.raw_text
