# Topdrawer Manual Source Policy

This document defines how this repository treats Topdrawer manual inputs,
generated manual data, and future preprocessing work.

## Current Runtime Contract

The MCP server reads one plain-text manual file at runtime:

```text
data/topdrawer.txt
```

`TOPDRAWER_MANUAL_PATH` may point the server at a replacement plain-text manual.
The runtime server should stay simple: it should read one plain-text file or an
explicitly configured replacement unless the repository intentionally changes
that contract.

## Source Categories

### Canonical Source

The preferred canonical upstream source for future preprocessing is:

```text
topdrawer.doc
```

This file is expected to contain the main manual content, including the command
reference material needed for later structured lookup work.

### Companion Source

The compact help file may be used as a companion reference:

```text
topdrawer4.0.hlp
```

Use it to cross-check command names, headings, and compact help text where it
improves confidence, but do not treat it as the primary source when it conflicts
with `topdrawer.doc`.

### Deferred Sources

HTML outputs such as `contents.html` and generated `html/*.html` files are
deferred by default. They may be useful as structure references, but they should
not drive the initial preprocessing pipeline unless the source policy is updated.

The current expectation is that the HTML content largely duplicates the manual
or help sources. Prefer avoiding another source format until it provides a clear
benefit.

## Tracked Files

The repository currently tracks:

```text
data/topdrawer.txt
```

This keeps the MCP server runnable from a clean checkout.

The repository should not normally track raw upstream source files or generated
preprocessing artifacts. In particular, keep these paths out of version control
unless a later policy change explicitly says otherwise:

```text
data/raw/
data/index/
build/
```

The long-term goal is to fetch or otherwise provide upstream manual sources
outside normal version control, then generate runtime data from those sources in
a deterministic way.

## Generated Data Location

Generated runtime data may continue to live under `data/` when it is useful to
the MCP server. Use subdirectories to keep generated artifacts distinct from the
checked-in baseline manual, for example:

```text
data/index/
```

Because generated artifacts are not tracked by default, preprocessing commands
must be deterministic and documented enough that a clean checkout can reproduce
them when the required upstream sources are available.

## Preprocessing Direction

Preprocessing should stay small. The current first pass reads the canonical
source and produces stable metadata for selected manual sections.

The current implementation adds a small build-time CLI:

```text
topdrawer-mcp-preprocess
```

It extracts top-level Chapter 15 command sections from `topdrawer.doc` and
writes a deterministic command index.

Chapter 15 command material remains the primary structured lookup target, but
it is large. The current preprocessing pass is intentionally limited to
top-level command sections before any broader expansion.

Useful early outputs include:

- command names
- section identifiers or headings
- source line or section references
- extracted text blocks for selected commands

The current generated output is:

```text
data/index/command-index.json
```

Do not add broad generated-HTML ingestion, source acquisition machinery, or full
command coverage in the first preprocessing pass.

## Relationship to MCP Tools

`search_manual` remains the plain-text fallback tool.

Future structured tools such as `lookup_section`, `lookup_command`, and
`list_commands` should use deterministic preprocessing outputs rather than
parsing raw manual sources at request time.
