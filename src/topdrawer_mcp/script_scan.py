from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from typing import TypedDict

from topdrawer_mcp.command_lookup import CommandLookupKind
from topdrawer_mcp.command_lookup import load_command_lookup_index

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MANUAL_PATH = ROOT_DIR / "data" / "topdrawer.txt"
_SET_HEADING_RE = re.compile(r"^\s*15\.64\.(\d+)\s+([A-Za-z_][A-Za-z0-9_ ]*)\s*$")
_SUPPLEMENTAL_COMMANDS: tuple[tuple[str, CommandLookupKind], ...] = (("READ", "command"),)
_SET_SUBCOMMAND_ALIASES = frozenset({"LABEL"})


class ScannedCommand(TypedDict):
    """One recognized command occurrence within a Topdrawer script."""

    line: int
    raw: str
    normalized: str
    kind: CommandLookupKind


class ScriptScanResult(TypedDict):
    """Structured scanner result for one Topdrawer script."""

    commands: list[ScannedCommand]


class _CommandMatcher(TypedDict):
    name: str
    normalized: str
    kind: CommandLookupKind
    token_count: int


def scan_topdrawer_script_text(script: str) -> ScriptScanResult:
    """Scan one inline Topdrawer script for recognized command occurrences."""
    if not script.strip():
        raise ValueError("script must be a non-empty string")

    matchers = _command_matchers()
    commands: list[ScannedCommand] = []

    for line_number, raw_line in enumerate(script.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or _is_comment_line(stripped):
            continue

        matched = _match_command(stripped, matchers)
        if matched is None:
            continue

        commands.append(
            {
                "line": line_number,
                "raw": stripped,
                "normalized": matched["normalized"],
                "kind": matched["kind"],
            }
        )

    return {"commands": commands}


def scan_topdrawer_script_file(input_path: str) -> ScriptScanResult:
    """Scan one Topdrawer script file for recognized command occurrences."""
    stripped_path = input_path.strip()
    if not stripped_path:
        raise ValueError("input_path must be a non-empty string")

    candidate = Path(stripped_path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    resolved = candidate.resolve()

    try:
        script = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise OSError(f"Unable to read Topdrawer script file: {resolved}") from exc
    return scan_topdrawer_script_text(script)


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

    for name, kind in _SUPPLEMENTAL_COMMANDS:
        normalized_name = _normalize_name(name)
        key = (normalized_name, normalized_name)
        if key in seen:
            continue
        seen.add(key)
        matchers.append(
            {
                "name": name,
                "normalized": normalized_name,
                "kind": kind,
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


@lru_cache(maxsize=1)
def _known_set_subcommand_names() -> frozenset[str]:
    names: set[str] = set()
    for line in DEFAULT_MANUAL_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _SET_HEADING_RE.match(line)
        if not match:
            continue
        names.add(_normalize_name(match.group(2)).split()[0])
    names.discard("INTRODUCTION")
    names.discard("OPTIONS")
    return frozenset(names)


def _normalize_name(value: str) -> str:
    return " ".join(value.replace("_", " ").strip().upper().split())


def _is_comment_line(line: str) -> bool:
    return line.startswith("!") or line.startswith("#")
