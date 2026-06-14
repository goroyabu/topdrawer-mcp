from __future__ import annotations

import os
from functools import cache
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.resources.base import Resource
from mcp.server.fastmcp.resources.templates import ResourceTemplate

from topdrawer_mcp.artifacts import get_artifact_manager
from topdrawer_mcp.command_lookup import CommandLookupEntry
from topdrawer_mcp.command_lookup import load_command_lookup_index
from topdrawer_mcp.command_lookup import lookup_command_entry
from topdrawer_mcp.reverse_lookup import ReverseLookupResult
from topdrawer_mcp.reverse_lookup import reverse_lookup_command_candidates
from topdrawer_mcp.render import generate_topdrawer_png as generate_topdrawer_png_core
from topdrawer_mcp.render import generate_topdrawer_postscript as generate_topdrawer_postscript_core
from topdrawer_mcp.render import RenderResult
from topdrawer_mcp.render import render_topdrawer_input
from topdrawer_mcp.render import render_topdrawer_source_text
from topdrawer_mcp.runtime_info import RuntimeInfoResult
from topdrawer_mcp.runtime_info import get_runtime_info
from topdrawer_mcp.sample_catalog import SampleCatalogEntry
from topdrawer_mcp.sample_catalog import SampleCatalogListResult
from topdrawer_mcp.sample_catalog import get_sample_catalog_entry
from topdrawer_mcp.sample_catalog import list_sample_catalog_entries
from topdrawer_mcp.script_scan import ScriptScanResult
from topdrawer_mcp.script_scan import scan_topdrawer_script_file
from topdrawer_mcp.script_scan import scan_topdrawer_script_text


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MANUAL_PATH = ROOT_DIR / "data" / "topdrawer.txt"


class ArtifactOutputResource(Resource):
    """Dynamic artifact output resource that updates MIME type per artifact."""

    artifact_id: str

    async def read(self) -> str | bytes:
        manager = get_artifact_manager()
        record = manager.load_artifact(self.artifact_id)
        self.mime_type = record.output_mime_type
        return manager.read_output(self.artifact_id)


class ArtifactOutputTemplate(ResourceTemplate):
    """Custom template for artifact output resources with per-artifact MIME types."""

    async def create_resource(self, uri: str, params: dict[str, Any], context: Any = None) -> Resource:
        return ArtifactOutputResource(
            uri=uri,  # type: ignore[arg-type]
            name=self.name,
            title=self.title,
            description=self.description,
            mime_type=self.mime_type,
            icons=self.icons,
            annotations=self.annotations,
            meta=self.meta,
            artifact_id=params["artifact_id"],
        )


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
                    "Set TOPDRAWER_MANUAL_PATH or create data/topdrawer.txt. "
                    "You can inspect the current runtime with get_server_runtime_info."
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


def generate_topdrawer_png(
    input_path: str | None = None,
    script: str | None = None,
    base_dir: str | None = None,
    output_path: str | None = None,
    overwrite: bool = False,
    dpi: int = 160,
    padding: int = 12,
    crop: bool = True,
    background: str = "white",
) -> RenderResult:
    """Generate a PNG image from a Topdrawer file path or inline script."""
    return generate_topdrawer_png_core(
        input_path=input_path,
        script=script,
        base_dir=base_dir,
        output_path=output_path,
        overwrite=overwrite,
        dpi=dpi,
        padding=padding,
        crop=crop,
        background=background,
    )


def generate_topdrawer_postscript(
    input_path: str | None = None,
    script: str | None = None,
    base_dir: str | None = None,
    output_path: str | None = None,
    overwrite: bool = False,
) -> RenderResult:
    """Generate PostScript from a Topdrawer file path or inline script."""
    return generate_topdrawer_postscript_core(
        input_path=input_path,
        script=script,
        base_dir=base_dir,
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


def reverse_lookup_commands(query: str, limit: int = 5) -> ReverseLookupResult:
    """Return ranked canonical command headings for a short natural-language query."""
    return reverse_lookup_command_candidates(query, limit=limit)


def get_server_runtime_info() -> RuntimeInfoResult:
    """Return resolved runtime/config information for manual and render features."""
    return get_runtime_info()


def scan_topdrawer_script(script: str) -> ScriptScanResult:
    """Scan inline Topdrawer script text for recognized command occurrences."""
    return scan_topdrawer_script_text(script)


def scan_topdrawer_file(input_path: str) -> ScriptScanResult:
    """Scan one Topdrawer script file for recognized command occurrences."""
    return scan_topdrawer_script_file(input_path)


def _command_path_parts(entry: CommandLookupEntry) -> tuple[str, ...]:
    """Return the canonical resource path parts for one reviewed command entry."""
    command_parts = entry["command"].lower().split()
    parent_command = entry["parent_command"]
    if entry["kind"] == "set-subcommand" and parent_command:
        parent_parts = parent_command.lower().split()
        return tuple(parent_parts + command_parts[len(parent_parts) :])
    if entry["kind"] == "modifier" and parent_command:
        return (*parent_command.lower().split(), *command_parts)
    return tuple(command_parts)


def _command_resource_uri(entry: CommandLookupEntry) -> str:
    """Return the canonical resource URI for one reviewed command entry."""
    return "resource://commands/" + "/".join(_command_path_parts(entry))


@cache
def _command_resource_path_map() -> dict[str, CommandLookupEntry]:
    """Return the canonical command-resource path map."""
    index = load_command_lookup_index()
    path_map: dict[str, CommandLookupEntry] = {}
    for entry in index["entries"]:
        uri = _command_resource_uri(entry)
        path = uri.removeprefix("resource://commands/")
        existing = path_map.get(path)
        if existing is not None:
            raise ValueError(
                "Duplicate command resource path "
                f"{path!r} for {existing['command']!r} and {entry['command']!r}"
            )
        path_map[path] = entry
    return path_map


def command_index_resource() -> dict[str, Any]:
    """Return a discovery index for reviewed command entries."""
    index = load_command_lookup_index()
    return {
        "schema_version": index["schema_version"],
        "source_name": index["source_name"],
        "entry_count": index["entry_count"],
        "entries": [
            {
                "command": entry["command"],
                "aliases": entry["aliases"],
                "kind": entry["kind"],
                "parent_command": entry["parent_command"],
                "section": entry["section"],
                "title": entry["title"],
                "uri": _command_resource_uri(entry),
            }
            for entry in index["entries"]
        ],
    }


def command_resource(command_path: str) -> CommandLookupEntry:
    """Return one reviewed command entry for a canonical command resource path."""
    normalized_path = "/".join(part for part in command_path.strip("/").lower().split("/") if part)
    entry = _command_resource_path_map().get(normalized_path)
    if entry is None:
        raise ValueError(f"Unknown command lookup entry: {command_path!r}")
    return lookup_command_entry(entry["command"])


def command_resource_top_level(command: str) -> CommandLookupEntry:
    """Return one reviewed top-level command entry for a canonical resource path."""
    return command_resource(command)


def command_resource_nested(parent: str, command: str) -> CommandLookupEntry:
    """Return one reviewed nested command entry for a canonical resource path."""
    return command_resource(f"{parent}/{command}")


def artifact_manifest_resource(artifact_id: str) -> dict[str, Any]:
    """Return the manifest for one generated artifact bundle."""
    return get_artifact_manager().read_manifest(artifact_id)


def artifact_output_resource(artifact_id: str) -> bytes | str:
    """Return the primary output for one generated artifact bundle."""
    return get_artifact_manager().read_output(artifact_id)


def artifact_source_resource(artifact_id: str) -> str:
    """Return the execution-time Topdrawer source for one generated artifact bundle."""
    return get_artifact_manager().read_source(artifact_id)


def artifact_metadata_resource(artifact_id: str) -> dict[str, Any]:
    """Return structured metadata for one generated artifact bundle."""
    return get_artifact_manager().read_metadata(artifact_id)


def inspect_topdrawer_script(
    script_text: str | None = None,
    input_path: str | None = None,
    goal: str | None = None,
) -> str:
    """Guide an agent through inspecting an existing Topdrawer script."""
    has_script_text = bool(script_text and script_text.strip())
    has_input_path = bool(input_path and input_path.strip())
    if has_script_text == has_input_path:
        raise ValueError("Provide exactly one of script_text or input_path.")

    source_line = (
        f"Use `scan_topdrawer_script` on the provided inline script text."
        if has_script_text
        else f"Use `scan_topdrawer_file` on `{input_path}`."
    )
    goal_line = f"Goal: {goal.strip()}\n\n" if goal and goal.strip() else ""
    return (
        f"{goal_line}"
        "Inspect the Topdrawer script with this flow:\n"
        f"1. {source_line}\n"
        "2. Review the returned normalized command names and line numbers.\n"
        "3. Call `lookup_command` for the commands relevant to the current task.\n"
        "4. Call `search_manual` only if `lookup_command` does not provide enough context.\n"
        "5. Summarize the important commands, any ambiguities, and the next recommended action.\n"
    )


def discover_topdrawer_command(query: str, context: str | None = None) -> str:
    """Guide an agent through discovering the right Topdrawer command."""
    stripped_query = query.strip()
    if not stripped_query:
        raise ValueError("query must be a non-empty string")

    context_line = f"Context: {context.strip()}\n\n" if context and context.strip() else ""
    return (
        f"{context_line}"
        f"Find the best Topdrawer command for: {stripped_query}\n\n"
        "1. Call `reverse_lookup_commands` with the key words or phrase.\n"
        "2. Call `lookup_command` for the best returned candidates.\n"
        "3. Call `search_manual` only if the reverse lookup or command guidance still leaves ambiguity.\n"
        "4. Summarize the best match and note any ambiguity between candidates.\n"
    )


def create_server() -> FastMCP:
    """Create the MCP server and register its tools."""
    server = FastMCP("topdrawer-mcp")
    server.add_tool(search_manual)
    server.add_tool(generate_topdrawer_png, structured_output=True)
    server.add_tool(generate_topdrawer_postscript, structured_output=True)
    server.add_tool(render_topdrawer_file, structured_output=True)
    server.add_tool(render_topdrawer_script, structured_output=True)
    server.add_tool(list_manual_samples, structured_output=True)
    server.add_tool(get_manual_sample, structured_output=True)
    server.add_tool(lookup_command, structured_output=True)
    server.add_tool(reverse_lookup_commands, structured_output=True)
    server.add_tool(get_server_runtime_info, structured_output=True)
    server.add_tool(scan_topdrawer_script, structured_output=True)
    server.add_tool(scan_topdrawer_file, structured_output=True)
    server.resource(
        "resource://commands/index",
        name="command_index_resource",
        title="Command index",
        description="Reviewed Topdrawer command index for resource discovery.",
        mime_type="application/json",
    )(command_index_resource)
    server.resource(
        "resource://commands/{command}",
        name="command_resource_top_level",
        title="Command entry",
        description="One reviewed top-level Topdrawer command entry by canonical resource path.",
        mime_type="application/json",
    )(command_resource_top_level)
    server.resource(
        "resource://commands/{parent}/{command}",
        name="command_resource_nested",
        title="Command entry",
        description="One reviewed nested Topdrawer command entry by canonical resource path.",
        mime_type="application/json",
    )(command_resource_nested)
    server.resource(
        "resource://artifacts/{artifact_id}",
        name="artifact_manifest_resource",
        title="Generated artifact manifest",
        description="Manifest for one generated Topdrawer artifact bundle.",
        mime_type="application/json",
    )(artifact_manifest_resource)
    server._resource_manager._templates["resource://artifacts/{artifact_id}/output"] = ArtifactOutputTemplate(
        uri_template="resource://artifacts/{artifact_id}/output",
        name="artifact_output_resource",
        title="Generated artifact output",
        description="Primary output content for one generated Topdrawer artifact bundle.",
        mime_type="application/octet-stream",
        fn=artifact_output_resource,
        parameters={
            "type": "object",
            "properties": {"artifact_id": {"title": "Artifact Id", "type": "string"}},
            "required": ["artifact_id"],
        },
        context_kwarg=None,
    )
    server.resource(
        "resource://artifacts/{artifact_id}/source",
        name="artifact_source_resource",
        title="Generated artifact source",
        description="Execution-time Topdrawer source for one generated artifact bundle.",
        mime_type="text/plain",
    )(artifact_source_resource)
    server.resource(
        "resource://artifacts/{artifact_id}/metadata",
        name="artifact_metadata_resource",
        title="Generated artifact metadata",
        description="Structured metadata for one generated Topdrawer artifact bundle.",
        mime_type="application/json",
    )(artifact_metadata_resource)
    server.prompt(
        name="inspect_topdrawer_script",
        title="Inspect Topdrawer script",
        description="Review an existing Topdrawer script using scan, lookup, and manual search.",
    )(inspect_topdrawer_script)
    server.prompt(
        name="discover_topdrawer_command",
        title="Discover Topdrawer command",
        description="Find the most likely Topdrawer command from a phrase or user intent.",
    )(discover_topdrawer_command)
    return server


def main() -> None:
    """Run the MCP server using FastMCP's default stdio transport."""
    create_server().run()


if __name__ == "__main__":
    main()
