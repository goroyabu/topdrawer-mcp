# SET ORDER And SET FONT Sample Coverage Design

## Goal

Add sample-scoped reviewed command coverage for `SET ORDER` and `SET FONT`
without widening the current MCP surface or changing manual sample metadata.

## Scope

This change adds only two new reviewed command lookup entries:

- `SET ORDER`
- `SET FONT`

The goal is to make them resolvable through `lookup_command` with useful,
sample-relevant guidance.

## Non-Goals

- Do not add new MCP tools.
- Do not change `list_manual_samples` or `get_manual_sample`.
- Do not expand `data/samples/catalog.json`.
- Do not implement the other uncovered sample-scoped commands in this batch.

## Intended Behavior

`lookup_command("SET ORDER")` should return a narrow reviewed entry that
explains how later input columns are interpreted as X, Y, errors, symbols, or
ignored placeholders.

`lookup_command("SET FONT")` should return a narrow reviewed entry that explains
how later titles, annotations, and similar text-bearing elements inherit the
selected font.

## Authoring Direction

The reviewed text should stay thin but valid.

For `SET ORDER`, emphasize the sample-driven patterns:

- `X Y DX DY`
- `X Y SYMBOL`
- `... DUMMY ... X`

For `SET FONT`, emphasize repeated `DUPLEX` use in manual samples as a display
precondition for later titles, annotations, and symbol/text showcase scripts.

Examples may be adapted from sample structure, but should avoid verbatim reuse
of sample literals.

## Constraints

- Keep the current `lookup_command` tool shape unchanged.
- Use the existing deterministic command lookup generation path.
- Keep guidance practical and sample-scoped rather than attempting full manual
  transcription.
