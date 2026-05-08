from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


TOP_LEVEL_COMMAND_RE = re.compile(r"^\s*(15\.(\d+))\s+(\S.*?)\s*$")
NEXT_CHAPTER_RE = re.compile(r"^\s*16\.\d+\s+\S")


@dataclass(frozen=True)
class CommandEntry:
    """A top-level Chapter 15 command section extracted from topdrawer.doc."""

    section: str
    command: str
    title: str
    start_line: int
    end_line: int
    text: str

    def to_json(self) -> dict[str, Any]:
        """Return a stable JSON-serializable representation."""
        return asdict(self)


def _command_from_title(title: str) -> str:
    return title.replace("_", " ").strip().upper()


def _find_chapter_15_bounds(lines: list[str]) -> tuple[int, int]:
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if (match := TOP_LEVEL_COMMAND_RE.match(line))
            and match.group(1) == "15.1"
            and match.group(3).strip() == "FORMAT_OF_COMMANDS"
        ),
        None,
    )
    if start is None:
        raise ValueError("Unable to find Chapter 15 start section 15.1 FORMAT_OF_COMMANDS")

    end = next(
        (
            index
            for index, line in enumerate(lines[start + 1 :], start=start + 1)
            if NEXT_CHAPTER_RE.match(line)
        ),
        len(lines),
    )
    return start, end


def extract_command_entries(text: str) -> list[CommandEntry]:
    """Extract top-level Chapter 15 command sections from manual text."""
    lines = text.splitlines()
    chapter_start, chapter_end = _find_chapter_15_bounds(lines)
    headings: list[tuple[int, str, str]] = []

    for index in range(chapter_start, chapter_end):
        match = TOP_LEVEL_COMMAND_RE.match(lines[index])
        if match is None:
            continue
        section = match.group(1)
        title = match.group(3).strip()
        headings.append((index, section, title))

    entries: list[CommandEntry] = []
    for offset, (start_index, section, title) in enumerate(headings):
        next_start = headings[offset + 1][0] if offset + 1 < len(headings) else chapter_end
        entries.append(
            CommandEntry(
                section=section,
                command=_command_from_title(title),
                title=title,
                start_line=start_index + 1,
                end_line=next_start,
                text="\n".join(lines[start_index:next_start]).rstrip(),
            )
        )
    return entries
