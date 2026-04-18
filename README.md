# topdrawer-mcp

Minimal MCP server for searching a local Topdrawer manual text file.

The server exposes one MCP tool, `search_manual`, which performs
case-insensitive substring search and returns line-numbered snippets.

## Scope

This repository is responsible for:

- reading a local plain-text Topdrawer manual
- exposing simple manual search through an MCP stdio server

This repository is not responsible for:

- building or packaging the `td` executable itself
- maintaining the upstream Topdrawer source tree
- preprocessing complex manual formats into structured indexes
- maintaining command, section, or generated search indexes

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

## Run

VS Code starts the server with `uv --directory ${workspaceFolder} run
topdrawer-mcp` in `.vscode/mcp.json`.

From the repository root:

```bash
uv run topdrawer-mcp
```

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
