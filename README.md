# topdrawer-mcp

MCP server project for agent-facing access to the Topdrawer manual.

This repository is intended to provide a documentation-oriented MCP server that
helps agents look up Topdrawer commands, sections, and related reference
material without depending on a specific working directory.

## Scope

This repository is responsible for:

- fetching canonical Topdrawer manual sources independently
- preprocessing those sources into search-oriented indexes
- exposing manual lookup through an MCP server

This repository is not responsible for:

- building or packaging the `td` executable itself
- maintaining the upstream Topdrawer source tree
- broad editor integration work in the initial phase

## Canonical sources

The initial source set is expected to center on:

- `topdrawer.doc` as the primary manual source
- `topdrawer4.0.hlp` as a compact companion reference
- `contents.html` as a structure/index map

Generated HTML fragments are intentionally out of scope for the initial phase.

## Status

This repository is in the planning/bootstrap phase.

The first milestones are:

1. define canonical source selection
2. define preprocessing/indexing rules
3. add a minimal documentation MCP server
4. expand manual coverage in phases

## Related repositories

- `topdrawer-cmake`: reproducible CMake-based build/install/test workflow for `td`

This repository should remain loosely coupled to build-oriented repositories.
It should fetch or manage its own manual inputs rather than depending on a
specific local build tree.
