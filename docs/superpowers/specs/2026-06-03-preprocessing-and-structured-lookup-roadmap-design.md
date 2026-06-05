# Preprocessing And Structured Lookup Roadmap Design

## Goal

Capture the current state and next design questions for manual preprocessing
and structured lookup work, so roadmap-style GitHub issues can be closed
without losing the remaining intent.

## Status Level

This topic is not at a single maturity level.

- Implemented foundation:
  - deterministic preprocessing CLI
  - command index generation
  - reviewed command lookup generation
  - runtime `lookup_command`
- Open design/roadmap work:
  - whether additional generated artifacts are needed
  - whether `lookup_section` should be added
  - whether `list_commands` should be added

This document is therefore a roadmap/design note, not an implementation-ready
spec for one immediate feature.

## Current State

The repository already includes a small deterministic preprocessing layer.

Implemented pieces:

- `topdrawer-mcp-preprocess`
- extraction of top-level Chapter 15 command entries
- generation of command-oriented index outputs
- reviewed command lookup support used by runtime `lookup_command`

The runtime server currently exposes:

- `search_manual`
- `lookup_command`

The runtime does not currently expose:

- `lookup_section`
- `list_commands`

The repository policy already constrains preprocessing to stay small,
deterministic, and aligned with canonical source policy.

## Why This Still Matters

The earlier preprocessing issue was originally framed as "add the pipeline,"
but the pipeline now exists in first-pass form. The remaining work is no longer
about introducing preprocessing from scratch. It is about deciding whether
additional structured lookup capabilities justify additional generated data.

This topic should remain separate from:

- broad manual ingestion
- full parser work
- turning the repository into a database-backed manual system
- runtime parsing of raw upstream sources at request time

## Remaining Questions

### 1. Structured lookup surface

The main remaining structured lookup questions are:

- Should the runtime expose `lookup_section`?
- Should the runtime expose `list_commands`?
- If yes, what is the narrowest useful interface for each?

### 2. Additional preprocessing artifacts

Before adding more runtime tools, decide whether the current generated data is
enough. If not, define the minimum additional artifacts needed, for example:

- a section-oriented index
- a command listing payload
- stable cross-references between command sections and headings

### 3. Scope boundaries

Any future preprocessing expansion must preserve the current repository
boundaries:

- deterministic and regenerable outputs
- no broad HTML ingestion by default
- no source acquisition machinery expansion without explicit policy change
- no runtime dependence on parsing raw upstream source documents

## Recommended Direction

Treat preprocessing and structured lookup as two connected layers:

1. Preprocessing should generate only the smallest data needed by a concrete
   runtime lookup problem.
2. Runtime tools should be introduced only when their interface is clearly
   useful and stable.

That implies:

- do not expand preprocessing just because more indexing is possible
- do expand preprocessing when a specific runtime tool requires a missing,
  stable artifact

## Entry Granularity Policy

Structured lookup entries should follow the manual's documented
section/subsection boundaries.

- A command or modifier gets its own lookup entry only when it appears as its
  own manual section or subsection.
- Phrases that are documented only inside a parent command section should not
  become standalone lookup entries.
- When such a phrase matters for sample-scoped guidance, its behavior should be
  documented under the parent command's reviewed guidance instead.
- If a parent command does not yet have a lookup entry, the parent entry may be
  introduced first, but only with reviewed content justified by the currently
  targeted subsection scope.

Under this rule, `SET POLAR` qualifies as its own entry because it has a
documented subsection, while `PLOT AXES`, `PLOT TITLE`, and `TITLE DATA` do
not qualify as standalone entries.

## Deferred Topic: Command Abbreviation Support

The Topdrawer manual allows commands and options to be abbreviated to the
shortest unique form, with commands generally abbreviable to three
characters.

The current runtime `lookup_command` surface does not implement general
abbreviation resolution. It resolves canonical command names plus a small
curated alias set only.

General abbreviation support is deferred because it would require design work
around:

- how abbreviation forms are generated and stored
- how ambiguous abbreviations are detected and reported
- whether abbreviation support should apply to commands only or also to
  modifiers and set-subcommands
- how this behavior interacts with curated aliases and command naming policy

Until that work is designed, abbreviation-like support should be added only as
explicit curated aliases when justified by a concrete workflow need.

The current `DELETE` work intentionally does not add `DEL` alias support yet.

## Candidate Next Tasks

These are the first candidates that could be promoted into standalone issues:

- define the minimum payload needed for `lookup_section`
- define whether `list_commands` is worthwhile as a stable MCP surface
- identify whether either tool requires a new generated index beyond the
  current command lookup inputs

If those questions are not yet answerable, they should stay in design/spec
space rather than issue space.

## Relationship To Existing Issues

- `#3` should no longer act as a generic "add the preprocessing pipeline"
  tracker, because the first-pass pipeline already exists.
- `#12` remains the concrete follow-up issue for structured runtime tools that
  are still actually missing.
- Coverage-expansion and broader roadmap themes belong in separate planning
  documents rather than here.

## Exit Criteria For This Roadmap Note

This note can stay as long as preprocessing/structured lookup direction remains
an active design topic. Concrete implementation work should move out into:

- issue(s) when a specific missing task is clear
- plan documents when an approved implementation path exists
