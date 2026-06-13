# topdrawer-mcp

Minimal MCP server for searching a local Topdrawer manual text file and
rendering existing Topdrawer input files through an external `td` executable.

The server exposes MCP tools, resources, and prompts for manual search,
command lookup, script inspection, and render workflows.

Tools:

- `search_manual` for case-insensitive substring search with line-numbered snippets
- `lookup_command` for structured command guidance by canonical name or unique alias
- `get_server_runtime_info` for resolved manual/render runtime configuration
- `scan_topdrawer_script` for extracting recognized commands from inline script text
- `scan_topdrawer_file` for extracting recognized commands from an existing `.top` file
- `generate_topdrawer_png` for generating PNG output from an existing file or inline script
- `generate_topdrawer_postscript` for generating PostScript output from an existing file or inline script
- `render_topdrawer_file` for rendering an existing Topdrawer input file to PNG
- `render_topdrawer_script` for rendering inline Topdrawer script text to PNG
- `list_manual_samples` for listing curated sample metadata with optional filters
- `get_manual_sample` for fetching one curated sample metadata entry by id

Resources:

- `resource://commands/index` for reviewed command discovery metadata
- `resource://commands/{command}` for one reviewed top-level canonical command entry
- `resource://commands/{parent}/{command}` for one reviewed nested canonical command entry
- dynamic `resource://artifacts/{artifact_id}` manifests returned by generation tools
- dynamic `resource://artifacts/{artifact_id}/output`, `/source`, and `/metadata` child resources for retained artifacts

Prompts:

- `inspect_topdrawer_script` for reviewing an existing script with `scan_topdrawer_*`, `lookup_command`, and `search_manual`
- `discover_topdrawer_command` for finding the most likely command from a phrase or user intent

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

To use `generate_topdrawer_png` and the compatibility render tools, install `td` and Ghostscript (`gs`) so both are
available on `PATH`. You can override the executable paths with:

```bash
TD_EXECUTABLE_PATH=/path/to/td GS_EXECUTABLE_PATH=/path/to/gs uv run topdrawer-mcp
```

When running through an MCP client, pass `TOPDRAWER_MANUAL_PATH` and
`TD_EXECUTABLE_PATH` (and optionally `GS_EXECUTABLE_PATH`) through the client's
environment configuration rather than editing repository defaults.

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

### `generate_topdrawer_png`

Input:

```json
{
  "input_path": "examples/error-bars.top",
  "script": null,
  "base_dir": null,
  "output_path": "/tmp/output.png",
  "overwrite": false,
  "dpi": 160,
  "padding": 12,
  "crop": true,
  "background": "white"
}
```

Provide exactly one of `input_path` or `script`. `base_dir` is used only for
inline script input. `output_path` is optional and is no longer the canonical
handoff; the tool always returns an `artifact_id` and `resource_uri` for the
generated artifact bundle. When `output_path` is omitted, the server still uses
an internal temp path while creating the retained artifact. `dpi` defaults to
`160`, `padding` defaults to `12` points, `crop` defaults to `true`, and
`background` accepts `white` or `transparent`.

With `crop=true`, the server trims to the PostScript BoundingBox and applies
`padding`. With `crop=false`, the server renders the original PostScript page
size and ignores `padding`.

Success result shape:

```json
{
  "success": true,
  "format": "png",
  "message": "Generated PNG successfully.",
  "artifact_id": "tdart_20260613_123456_abcd1234",
  "resource_uri": "resource://artifacts/tdart_20260613_123456_abcd1234",
  "metadata": {
    "source_kind": "input_path",
    "dpi": 160,
    "background": "white",
    "crop_applied": true,
    "output_path_overridden": false,
    "normalized_device_config": {
      "device": "POSTSCRIPT",
      "output_key": "FILE",
      "output_value": "/tmp/topdrawer-mcp-render-ps/render.ps"
    }
  }
}
```

Read `resource_uri` first to obtain the artifact manifest, then follow its
`output`, `source`, and `metadata` URIs as needed. Generated artifacts are
temporary and are not listed in normal `resources/list`. The `/output`
resource keeps the same URI shape for every format, while its MIME type is
artifact-specific such as `image/png` or `application/postscript`. The
retained `/source` resource stores the execution-time Topdrawer script the
server actually ran.

### `generate_topdrawer_postscript`

Input:

```json
{
  "input_path": "examples/error-bars.top",
  "script": null,
  "base_dir": null,
  "output_path": "/tmp/output.ps",
  "overwrite": false
}
```

Provide exactly one of `input_path` or `script`. `base_dir` is used only for
inline script input. `output_path` is optional and remains supplemental only;
the canonical result is the returned artifact manifest URI.

Success result shape:

```json
{
  "success": true,
  "format": "postscript",
  "message": "Generated PostScript successfully.",
  "artifact_id": "tdart_20260613_123457_efgh5678",
  "resource_uri": "resource://artifacts/tdart_20260613_123457_efgh5678",
  "metadata": {
    "source_kind": "script",
    "output_path_overridden": false,
    "normalized_device_config": {
      "device": "POSTSCRIPT",
      "output_key": "FILE",
      "output_value": "/tmp/topdrawer-mcp-render-out/render.ps"
    }
  }
}
```

### `get_server_runtime_info`

Returns structured read-only runtime information for:

- the manual-search source path
- the tracked command-lookup source files
- the resolved `td` and `gs` executables used for rendering

### `scan_topdrawer_script`

Input:

```json
{
  "script": "set window x 0 13 y 0 10\nset limits x 0 to 5 y 0 to 6\nplot axis\ntitle top \"Example\"\ncase \"GGGGGGG\"\nplot\n"
}
```

Returns a structured first-pass scan of inline Topdrawer script text:

- recognized covered commands with line numbers
- normalized command names and command kinds

### `scan_topdrawer_file`

Input:

```json
{
  "input_path": "examples/sample.top"
}
```

Returns the same command-discovery scan as `scan_topdrawer_script`, but reads
the script from an existing file path. The scanner also recognizes `READ`.

Example Topdrawer input:

```text
set symbol 1P
set order y x dx dy
100 1 0.5 10
144 2 0.5 12
196 3 0.5 14
plot
```

Use `generate_topdrawer_png` or `generate_topdrawer_postscript` for new work
when you already have a `.top` file on disk.

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

### Compatibility render tools

`render_topdrawer_file` and `render_topdrawer_script` remain available during
the transition to the format-centered surface. They continue to generate PNG
output and delegate to the newer PNG-generation core.

### `lookup_command`

Input:

```json
{
  "command": "SYMBOL"
}
```

Looks up one reviewed command-guidance entry by canonical command name or a
unique alias. This tool returns structured command metadata only. Use
`search_manual` for free-text manual search.

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

## MCP Resources

### `resource://commands/index`

Returns JSON discovery metadata for all reviewed command entries. Each entry
includes:

- `command`
- `aliases`
- `kind`
- `parent_command`
- `section`
- `title`
- `uri`

### `resource://commands/{command}`

Returns one reviewed top-level command entry as JSON for a canonical resource
path.

### `resource://commands/{parent}/{command}`

Returns one reviewed nested command entry as JSON for a canonical resource
path. Aliases remain supported by `lookup_command`, but these resource
templates expect canonical paths only.

Examples:

- `resource://commands/title`
- `resource://commands/set/order`
- `resource://commands/title/case`

## MCP Prompts

### `inspect_topdrawer_script`

Prompt arguments:

- `script_text` optional
- `input_path` optional
- `goal` optional

The prompt requires exactly one of `script_text` or `input_path` and guides the
agent through:

```text
scan_topdrawer_file | scan_topdrawer_script -> lookup_command -> search_manual if needed
```

### `discover_topdrawer_command`

Prompt arguments:

- `query` required
- `context` optional

This prompt guides the agent through the current phrase-to-command workflow:

```text
search_manual -> extract candidates -> lookup_command
```

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
