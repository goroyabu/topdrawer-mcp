# topdrawer-mcp

Minimal MCP server for searching a local Topdrawer manual text file and
rendering existing Topdrawer input files through an external `td` executable.

The server exposes MCP tools for manual search, render, and sample metadata
discovery:

- `search_manual` for case-insensitive substring search with line-numbered snippets
- `render_topdrawer_file` for rendering an existing Topdrawer input file to PNG
- `render_topdrawer_script` for rendering inline Topdrawer script text to PNG
- `list_manual_samples` for listing curated sample metadata with optional filters
- `get_manual_sample` for fetching one curated sample metadata entry by id

## Scope

This repository is responsible for:

- reading a local plain-text Topdrawer manual
- exposing simple manual search through an MCP stdio server
- executing an already-installed `td` binary to render an existing input file
- executing inline Topdrawer script text through the same rendering pipeline

This repository is not responsible for:

- building or packaging the `td` executable itself
- maintaining the upstream Topdrawer source tree
- rewriting user-provided `.top` files in place
- broad manual preprocessing beyond the currently agreed source-policy scope

## Data

By default, the server reads:

```text
data/topdrawer.txt
```

The file is treated as plain UTF-8 text. The server does not parse Topdrawer
commands, sections, generated HTML, or source manifests.

You can override the manual path with:

```bash
TOPDRAWER_MANUAL_PATH=/path/to/manual.txt
```

See [docs/source-policy.md](docs/source-policy.md) for how this repository
treats canonical manual sources, companion sources, and future generated data.

## Preprocess

An optional build-time preprocessing CLI exists for small, deterministic index
generation tasks. The current first pass extracts top-level Chapter 15 command
sections from `topdrawer.doc`.

Run it from the repository root:

```bash
uv run topdrawer-mcp-preprocess
```

You can override the source file path with:

```bash
TOPDRAWER_DOC_SOURCE_PATH=/path/to/topdrawer.doc uv run topdrawer-mcp-preprocess
```

## Run

VS Code starts the server with `uv --directory ${workspaceFolder} run
topdrawer-mcp` in `.vscode/mcp.json`.

`${workspaceFolder}` is a VS Code substitution and is not portable to other MCP
clients. Outside VS Code, use an absolute repository path, for example:

```bash
uv --directory /absolute/path/to/topdrawer-mcp run topdrawer-mcp
```

From the repository root:

```bash
uv run topdrawer-mcp
```

To use `render_topdrawer_file`, install `td` and Ghostscript (`gs`) so both are
available on `PATH`. You can override the `td` executable path with:

```bash
TD_EXECUTABLE_PATH=/path/to/td uv run topdrawer-mcp
```

When running through an MCP client, pass `TOPDRAWER_MANUAL_PATH` and
`TD_EXECUTABLE_PATH` through the client's environment configuration rather than
editing repository defaults.

VS Code starts the server through:

```text
.vscode/mcp.json
```

## MCP Tools

### `search_manual`

Input:

```json
{
  "query": "BARGRAPH",
  "limit": 5,
  "context_lines": 2
}
```

`limit` defaults to `5` and is clamped to `1..20`. `context_lines` defaults to
`2` and is clamped to `0..10`.

### `render_topdrawer_file`

Input:

```json
{
  "input_path": "examples/error-bars.top",
  "output_path": "/tmp/output.png",
  "overwrite": false
}
```

`input_path` may be absolute or current-working-directory-relative.
`output_path` is optional; when omitted, the server writes to a unique PNG path
under the system temp directory. `overwrite` defaults to `false`. PNG output is
rendered with an opaque white background and trimmed to the PostScript
BoundingBox with small padding.

Example Topdrawer input:

```text
set symbol 1P
set order y x dx dy
100 1 0.5 10
144 2 0.5 12
196 3 0.5 14
plot
```

Use `render_topdrawer_file` when you already have a `.top` file on disk.

### `render_topdrawer_script`

Input:

```json
{
  "script": "set symbol 1P\nset order y x dx dy\n100 1 0.5 10\n144 2 0.5 12\n196 3 0.5 14\nplot\n",
  "base_dir": "/tmp/sample-data",
  "output_path": "/tmp/output.png",
  "overwrite": false
}
```

`script` must be non-empty. `base_dir` is optional and controls how relative
paths inside the script, such as `set file input='dat'`, are resolved. When
omitted, relative references use the server's current working directory. PNG
output is rendered with an opaque white background and trimmed to the
PostScript BoundingBox with small padding.

Use `render_topdrawer_script` when the caller has inline Topdrawer text, chat
data that the agent converts into a script, or a script variant that does not
need to be saved as a persistent `.top` file first.

### `list_manual_samples`

Input:

```json
{
  "category": "histogram",
  "command": "HISTOGRAM",
  "query": "basic",
  "limit": 20
}
```

All filters are optional. `category` matches one curated sample category.
`command` matches `primary_commands` case-insensitively. `query` performs a
case-insensitive substring search over sample metadata only. This tool returns
metadata only; it does not return sample script text.

### `get_manual_sample`

Input:

```json
{
  "sample_id": "scatter-error-bars"
}
```

Returns one curated sample metadata entry by id. This tool returns metadata
only; sample script text remains out of scope for the current MCP surface.

## Test

Run the full test suite:

```bash
uv run --extra test pytest
```

Run only Python unit tests:

```bash
uv run --extra test pytest -m unit
```

Run only Inspector-based integration tests:

```bash
uv run --extra test pytest -m integration
```

The integration tests use `npx @modelcontextprotocol/inspector` and require
Node.js with `npx` available on `PATH`.
