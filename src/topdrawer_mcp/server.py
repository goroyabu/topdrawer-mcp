from __future__ import annotations

import os
from functools import cache
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from topdrawer_mcp.command_lookup import CommandLookupEntry
from topdrawer_mcp.command_lookup import lookup_command_entry
from topdrawer_mcp.render import RenderResult
from topdrawer_mcp.render import render_topdrawer_input
from topdrawer_mcp.render import render_topdrawer_source_text
from topdrawer_mcp.sample_catalog import SampleCatalogEntry
from topdrawer_mcp.sample_catalog import SampleCatalogListResult
from topdrawer_mcp.sample_catalog import get_sample_catalog_entry
from topdrawer_mcp.sample_catalog import list_sample_catalog_entries


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MANUAL_PATH = ROOT_DIR / "data" / "topdrawer.txt"


class ManualText:
    """Lazy reader and substring search helper for the plain-text manual."""

    def __init__(self, path: Path) -> None:
        """Create a manual reader for `path` without reading the file yet."""
        self.path = path
        self._lines: list[str] | None = None

    @property
    def lines(self) -> list[str]:
        """Return cached manual lines, loading the text file on first access."""
        if self._lines is None:
            try:
                text = self.path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                raise OSError(
                    f"Unable to read manual text at {self.path}. "
                    "Set TOPDRAWER_MANUAL_PATH or create data/topdrawer.txt."
                ) from exc
            self._lines = text.splitlines()
        return self._lines

    def search(self, query: str, limit: int, context_lines: int) -> list[dict[str, Any]]:
        """Find case-insensitive line matches and include surrounding context lines."""
        needle = query.casefold()
        matches: list[dict[str, Any]] = []
        lines = self.lines
        for index, line in enumerate(lines):
            if needle not in line.casefold():
                continue
            start = max(0, index - context_lines)
            end = min(len(lines), index + context_lines + 1)
            matches.append(
                {
                    "line": index + 1,
                    "start_line": start + 1,
                    "end_line": end,
                    "snippet": lines[start:end],
                }
            )
            if len(matches) >= limit:
                break
        return matches


def _manual_path() -> Path:
    """Resolve the manual path from the environment or repository default."""
    return Path(os.environ.get("TOPDRAWER_MANUAL_PATH", DEFAULT_MANUAL_PATH))


@cache
def _manual_for_path(path: str) -> ManualText:
    """Return one lazy manual reader per resolved path."""
    return ManualText(Path(path))


def _manual() -> ManualText:
    """Return the manual reader used by MCP tools."""
    return _manual_for_path(str(_manual_path()))


def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    """Parse `value` as an int and clamp it to an inclusive range."""
    parsed = int(value)
    return max(minimum, min(parsed, maximum))


def _format_matches(query: str, matches: list[dict[str, Any]]) -> str:
    """Format manual search matches as a line-numbered text response."""
    lines = [f"Found {len(matches)} matches for {query!r}."]
    for offset, match in enumerate(matches, start=1):
        lines.append("")
        lines.append(
            f"Match {offset}: line {match['line']} "
            f"(showing {match['start_line']}-{match['end_line']})"
        )
        for line_number, text in enumerate(match["snippet"], start=match["start_line"]):
            marker = ">" if line_number == match["line"] else " "
            lines.append(f"{marker} {line_number}: {text}")
    return "\n".join(lines)


def search_manual(query: str, limit: int = 5, context_lines: int = 2) -> str:
    """Search the Topdrawer manual text with case-insensitive substring matching.

    Args:
        query: Non-empty substring to search for.
        limit: Maximum number of matching lines to return. Clamped to 1..20.
        context_lines: Number of surrounding lines to include. Clamped to 0..10.
    """
    stripped_query = query.strip()
    if not stripped_query:
        raise ValueError("query must be a non-empty string")

    clamped_limit = _clamp_int(limit, minimum=1, maximum=20)
    clamped_context_lines = _clamp_int(context_lines, minimum=0, maximum=10)
    matches = _manual().search(
        stripped_query,
        limit=clamped_limit,
        context_lines=clamped_context_lines,
    )
    if not matches:
        return f"No manual matches found for {stripped_query!r}."
    return _format_matches(stripped_query, matches)


def render_topdrawer_file(
    input_path: str,
    output_path: str | None = None,
    overwrite: bool = False,
) -> RenderResult:
    """Render an existing Topdrawer input file into a PNG image.

    Args:
        input_path: Absolute or current-working-directory-relative Topdrawer input file.
        output_path: Optional PNG output path. Defaults to a unique system temp path.
        overwrite: Whether an existing output file may be replaced.
    """
    return render_topdrawer_input(
        input_path=input_path,
        output_path=output_path,
        overwrite=overwrite,
    )


def render_topdrawer_script(
    script: str,
    base_dir: str | None = None,
    output_path: str | None = None,
    overwrite: bool = False,
) -> RenderResult:
    """Render an inline Topdrawer script into a PNG image.

    Args:
        script: Topdrawer script text to render.
        base_dir: Optional directory used for relative include/input references.
        output_path: Optional PNG output path. Defaults to a unique system temp path.
        overwrite: Whether an existing output file may be replaced.
    """
    if not script.strip():
        raise ValueError("script must be a non-empty string")

    return render_topdrawer_source_text(
        script,
        base_dir=base_dir,
        output_path=output_path,
        overwrite=overwrite,
    )


def list_manual_samples(
    category: str | None = None,
    command: str | None = None,
    query: str | None = None,
    limit: int = 20,
) -> SampleCatalogListResult:
    """List curated manual-sample metadata with optional filtering.

    Args:
        category: Optional exact sample category such as ``histogram``.
        command: Optional primary command name such as ``PLOT`` or ``JOIN``.
        query: Optional case-insensitive substring query over sample metadata.
        limit: Maximum number of entries to return. Clamped to 1..20.
    """
    return {
        "samples": list_sample_catalog_entries(
            category=category,
            command=command,
            query=query,
            limit=limit,
        )
    }


def get_manual_sample(sample_id: str) -> SampleCatalogEntry:
    """Return one curated manual-sample metadata entry by id."""
    return get_sample_catalog_entry(sample_id)


def lookup_command(command: str) -> CommandLookupEntry:
    """Return one structured command guidance entry by canonical name or unique alias."""
    return lookup_command_entry(command)


def create_server() -> FastMCP:
    """Create the MCP server and register its tools."""
    server = FastMCP("topdrawer-mcp")
    server.add_tool(search_manual)
    server.add_tool(render_topdrawer_file, structured_output=True)
    server.add_tool(render_topdrawer_script, structured_output=True)
    server.add_tool(list_manual_samples, structured_output=True)
    server.add_tool(get_manual_sample, structured_output=True)
    server.add_tool(lookup_command, structured_output=True)
    return server


def main() -> None:
    """Run the MCP server using FastMCP's default stdio transport."""
    create_server().run()


if __name__ == "__main__":
    main()
