from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .commands import _find_chapter_15_bounds


PAGE_HEADER_RE = re.compile(r"^\s*PAGE\s+\d+\s*$", re.IGNORECASE)
COMMANDS_HEADER_RE = re.compile(r"^\s*COMMANDS\s*$")
SECTION_HEADING_RE = re.compile(r"^\s*(15(?:\.\d+)+)\s+(\S.*?)\s*$")
GROUP_LABEL_RE = re.compile(r"^\s*(?:3-d|MESH)\s+options\s*$", re.IGNORECASE)
UNDERLINE_RE = re.compile(r"^[\-\s]+$")
VALID_LOOKUP_KINDS = {"command", "modifier", "set-subcommand"}


@dataclass(frozen=True)
class CommandLookupOptionGroup:
    name: str
    items: list[str]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CommandLookupTarget:
    command: str
    aliases: list[str]
    kind: str
    section: str
    parent_command: str | None = None


@dataclass(frozen=True)
class ReviewedCommandLookupEntry:
    command: str
    summary: str
    important_rules: list[str]
    option_groups: list[CommandLookupOptionGroup]


@dataclass(frozen=True)
class CommandLookupEntry:
    """Lookup entry merged from deterministic extraction and reviewed metadata."""

    command: str
    aliases: list[str]
    kind: str
    section: str
    title: str
    start_line: int
    end_line: int
    summary: str
    syntax_lines: list[str]
    important_rules: list[str]
    option_groups: list[CommandLookupOptionGroup]
    raw_text: str
    parent_command: str | None = None

    def to_json(self) -> dict[str, Any]:
        """Return a stable JSON-serializable representation."""
        return asdict(self)


@dataclass(frozen=True)
class _ExtractedSection:
    section: str
    title: str
    start_line: int
    end_line: int
    text: str


def load_command_lookup_targets(path: str | Path) -> list[CommandLookupTarget]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = payload.get("entries")
    if payload.get("schema_version") != 1 or not isinstance(entries, list) or not entries:
        raise ValueError("Invalid command lookup targets payload")

    targets: list[CommandLookupTarget] = []
    seen_commands: set[str] = set()

    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Invalid command lookup target entry")
        command = _required_non_empty_string(entry, "command")
        if command in seen_commands:
            raise ValueError(f"Duplicate command lookup target: {command}")
        aliases = _string_list(entry.get("aliases", []), "aliases")
        kind = _required_non_empty_string(entry, "kind")
        if kind not in VALID_LOOKUP_KINDS:
            raise ValueError(f"Invalid command lookup kind for {command}: {kind}")
        section = _required_non_empty_string(entry, "section")
        parent_command = _optional_non_empty_string(entry.get("parent_command"))
        targets.append(
            CommandLookupTarget(
                command=command,
                aliases=aliases,
                kind=kind,
                section=section,
                parent_command=parent_command,
            )
        )
        seen_commands.add(command)
    return targets


def load_reviewed_command_lookup_entries(path: str | Path) -> list[ReviewedCommandLookupEntry]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = payload.get("entries")
    if payload.get("schema_version") != 1 or not isinstance(entries, list) or not entries:
        raise ValueError("Invalid reviewed command lookup payload")

    reviewed_entries: list[ReviewedCommandLookupEntry] = []
    seen_commands: set[str] = set()

    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Invalid reviewed command lookup entry")
        command = _required_non_empty_string(entry, "command")
        if command in seen_commands:
            raise ValueError(f"Duplicate reviewed command lookup entry: {command}")
        summary = _required_non_empty_string(entry, "summary")
        important_rules = _string_list(entry.get("important_rules", []), "important_rules")
        option_groups_payload = entry.get("option_groups", [])
        if not isinstance(option_groups_payload, list):
            raise ValueError(f"option_groups must be a list for {command}")
        option_groups = [
            CommandLookupOptionGroup(
                name=_required_non_empty_string(group, "name"),
                items=_string_list(group.get("items", []), "items"),
            )
            for group in option_groups_payload
            if isinstance(group, dict)
        ]
        if len(option_groups) != len(option_groups_payload):
            raise ValueError(f"Invalid option_groups for {command}")
        reviewed_entries.append(
            ReviewedCommandLookupEntry(
                command=command,
                summary=summary,
                important_rules=important_rules,
                option_groups=option_groups,
            )
        )
        seen_commands.add(command)
    return reviewed_entries


def build_command_lookup_entries(
    source_text: str,
    targets: list[CommandLookupTarget],
    reviewed_entries: list[ReviewedCommandLookupEntry],
) -> list[CommandLookupEntry]:
    """Build lookup entries for selected commands from source text."""
    reviewed_by_command = {entry.command: entry for entry in reviewed_entries}
    lines = source_text.splitlines()
    chapter_start, chapter_end = _find_chapter_15_bounds(lines)
    headings = _chapter_15_headings(lines, chapter_start, chapter_end)

    lookup_entries: list[CommandLookupEntry] = []
    for target in targets:
        extracted = _extract_section(lines, headings, target.section, chapter_end)
        reviewed = reviewed_by_command.get(target.command)
        if reviewed is None:
            raise ValueError(f"Missing reviewed command lookup entry for {target.command}")
        lookup_entries.append(
            CommandLookupEntry(
                command=target.command,
                aliases=target.aliases,
                kind=target.kind,
                section=extracted.section,
                title=extracted.title,
                start_line=extracted.start_line,
                end_line=extracted.end_line,
                summary=reviewed.summary,
                syntax_lines=_extract_syntax_lines(extracted.text, target.command, extracted.title),
                important_rules=reviewed.important_rules,
                option_groups=reviewed.option_groups,
                raw_text=_clean_raw_text(extracted.text, extracted.title),
                parent_command=target.parent_command,
            )
        )
    return lookup_entries


def _chapter_15_headings(
    lines: list[str],
    chapter_start: int,
    chapter_end: int,
) -> list[tuple[int, str, str]]:
    headings: list[tuple[int, str, str]] = []
    for index in range(chapter_start, chapter_end):
        match = SECTION_HEADING_RE.match(lines[index])
        if match is None:
            continue
        headings.append((index, match.group(1), match.group(2).strip()))
    return headings


def _extract_section(
    lines: list[str],
    headings: list[tuple[int, str, str]],
    target_section: str,
    chapter_end: int,
) -> _ExtractedSection:
    for offset, (start_index, section, title) in enumerate(headings):
        if section != target_section:
            continue
        next_start = chapter_end
        for next_index, next_section, _ in headings[offset + 1 :]:
            if next_section.startswith(f"{target_section}."):
                continue
            next_start = next_index
            break
        return _ExtractedSection(
            section=section,
            title=title,
            start_line=start_index + 1,
            end_line=next_start,
            text="\n".join(lines[start_index:next_start]).rstrip(),
        )
    raise ValueError(f"Unable to find command lookup section {target_section}")


def _clean_raw_text(text: str, title: str) -> str:
    lines = text.splitlines()
    cleaned: list[str] = []
    skip_repeated_title = False

    for line in lines:
        stripped = line.strip()
        if PAGE_HEADER_RE.match(stripped) or COMMANDS_HEADER_RE.match(stripped):
            skip_repeated_title = True
            continue
        if skip_repeated_title and stripped == title:
            skip_repeated_title = False
            continue
        if stripped:
            skip_repeated_title = False
        cleaned.append(line.rstrip())
    return "\n".join(_trim_blank_lines(cleaned)).strip()


def _extract_syntax_lines(text: str, command: str, title: str) -> list[str]:
    lines = _trim_blank_lines(_clean_raw_text(text, title).splitlines())
    syntax_lines: list[str] = []
    saw_heading = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if syntax_lines:
                continue
            continue
        if not saw_heading and SECTION_HEADING_RE.match(stripped):
            saw_heading = True
            continue
        if syntax_lines and UNDERLINE_RE.match(stripped):
            continue
        if _is_syntax_line(stripped, command):
            syntax_lines.append(stripped)
            continue
        if syntax_lines and GROUP_LABEL_RE.match(stripped):
            continue
        if syntax_lines:
            break
    return syntax_lines


def _trim_blank_lines(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def _is_syntax_line(stripped: str, command: str) -> bool:
    if stripped.startswith("["):
        return True
    if stripped.startswith(command):
        return True
    underscored = command.replace(" ", "_")
    if underscored != command and stripped.startswith(underscored):
        return True
    return False


def _required_non_empty_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_non_empty_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("optional string value must be non-empty when present")
    return value.strip()


def _string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} entries must be non-empty strings")
        result.append(item.strip())
    return result
