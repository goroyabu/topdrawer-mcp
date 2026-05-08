from __future__ import annotations

import pytest

from topdrawer_mcp.preprocess.commands import extract_command_entries


pytestmark = pytest.mark.unit


def test_extract_command_entries_from_chapter_15_body():
    text = "\n".join(
        [
            "contents",
            "     15.1    FORMAT_OF_COMMANDS                                      29",
            "     15.2    QUESTION_MARK                                           30",
            "",
            "     15.1  FORMAT_OF_COMMANDS ",
            "     format text",
            "     15.2  QUESTION_MARK ",
            "     question text",
            "     15.10  BARGRAPH ",
            "     bargraph text",
            "     15.10.1  Option ",
            "     option text",
            "     15.50  NEW_FRAME ",
            "     new frame text",
            "     16.1  LIST_OF_NAMES ",
            "     chapter 16 text",
        ]
    )

    entries = extract_command_entries(text)

    assert [entry.section for entry in entries] == ["15.1", "15.2", "15.10", "15.50"]
    assert [entry.command for entry in entries] == [
        "FORMAT OF COMMANDS",
        "QUESTION MARK",
        "BARGRAPH",
        "NEW FRAME",
    ]
    assert entries[2].start_line == 9
    assert entries[2].end_line == 12
    assert "15.10.1  Option" in entries[2].text
    assert "16.1  LIST_OF_NAMES" not in entries[-1].text


def test_extract_command_entries_requires_chapter_15_start():
    with pytest.raises(ValueError, match="Unable to find Chapter 15 start"):
        extract_command_entries("15.2  QUESTION_MARK\n")
