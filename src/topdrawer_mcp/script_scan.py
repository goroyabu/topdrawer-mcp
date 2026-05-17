from __future__ import annotations

from collections import Counter
from functools import lru_cache
from typing import Literal
from typing import TypedDict

from topdrawer_mcp.command_lookup import CommandLookupKind
from topdrawer_mcp.command_lookup import load_command_lookup_index


CheckSeverity = Literal["warning"]


class ScannedCommand(TypedDict):
    """One recognized command occurrence within a Topdrawer script."""

    line: int
    raw: str
    normalized: str
    kind: CommandLookupKind


class ScriptScanSummary(TypedDict):
    """Compact summary information for one scanned script."""

    counts: dict[str, int]


class ScriptScanCheck(TypedDict):
    """One lightweight rule-check finding."""

    severity: CheckSeverity
    line: int
    message: str


class ScriptScanResult(TypedDict):
    """Structured scanner result for one Topdrawer script."""

    commands: list[ScannedCommand]
    summary: ScriptScanSummary
    checks: list[ScriptScanCheck]


class _CommandMatcher(TypedDict):
    name: str
    normalized: str
    kind: CommandLookupKind
    token_count: int


def scan_topdrawer_script_text(script: str) -> ScriptScanResult:
    """Scan one inline Topdrawer script for known commands and simple rule issues."""
    if not script.strip():
        raise ValueError("script must be a non-empty string")

    matchers = _command_matchers()
    commands: list[ScannedCommand] = []
    substantive_lines: list[tuple[int, str, ScannedCommand | None]] = []

    for line_number, raw_line in enumerate(script.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if _is_comment_line(stripped):
            continue

        matched = _match_command(stripped, matchers)
        if matched is not None:
            commands.append(
                {
                    "line": line_number,
                    "raw": stripped,
                    "normalized": matched["normalized"],
                    "kind": matched["kind"],
                }
            )
            substantive_lines.append((line_number, stripped, commands[-1]))
            continue

        substantive_lines.append((line_number, stripped, None))

    checks = _case_adjacency_checks(commands, substantive_lines)
    counts = Counter(command["normalized"] for command in commands)
    summary: ScriptScanSummary = {"counts": dict(sorted(counts.items()))}
    return {"commands": commands, "summary": summary, "checks": checks}


@lru_cache(maxsize=1)
def _command_matchers() -> tuple[_CommandMatcher, ...]:
    index = load_command_lookup_index()
    matchers: list[_CommandMatcher] = []
    seen: set[tuple[str, str]] = set()

    for entry in index["entries"]:
        names = [entry["command"], *entry["aliases"]]
        for name in names:
            normalized_name = _normalize_name(name)
            key = (normalized_name, entry["command"])
            if key in seen:
                continue
            seen.add(key)
            matchers.append(
                {
                    "name": name,
                    "normalized": _normalize_name(entry["command"]),
                    "kind": entry["kind"],
                    "token_count": len(normalized_name.split()),
                }
            )

    matchers.sort(key=lambda matcher: (-matcher["token_count"], matcher["name"]))
    return tuple(matchers)


def _match_command(line: str, matchers: tuple[_CommandMatcher, ...]) -> _CommandMatcher | None:
    normalized_line = _normalize_name(line)
    for matcher in matchers:
        name = _normalize_name(matcher["name"])
        if normalized_line == name or normalized_line.startswith(f"{name} "):
            return matcher
    return None


def _case_adjacency_checks(
    commands: list[ScannedCommand],
    substantive_lines: list[tuple[int, str, ScannedCommand | None]],
) -> list[ScriptScanCheck]:
    command_by_line = {command["line"]: command for command in commands}
    checks: list[ScriptScanCheck] = []

    for command in commands:
        if command["normalized"] != "CASE":
            continue

        previous_command: ScannedCommand | None = None
        for line_number, _raw, maybe_command in substantive_lines:
            if line_number >= command["line"]:
                break
            if maybe_command is not None:
                previous_command = maybe_command
            else:
                previous_command = None

        if previous_command is None or previous_command["normalized"] not in {"TITLE", "MORE"}:
            checks.append(
                {
                    "severity": "warning",
                    "line": command["line"],
                    "message": "CASE should immediately follow TITLE or MORE.",
                }
            )
            continue

        if command_by_line[previous_command["line"]] != previous_command:
            checks.append(
                {
                    "severity": "warning",
                    "line": command["line"],
                    "message": "CASE should immediately follow TITLE or MORE.",
                }
            )

    return checks


def _normalize_name(value: str) -> str:
    return " ".join(value.replace("_", " ").strip().upper().split())


def _is_comment_line(line: str) -> bool:
    return line.startswith("!") or line.startswith("#")
