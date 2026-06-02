# Coverage Expansion Roadmap Design

## Goal

Capture the existing roadmap intent behind manual-coverage expansion, so
roadmap-style GitHub issues can be closed without losing the principles,
priority order, and promotion rules that were previously spread across them.

## Status Level

This topic is primarily at roadmap and requirements-analysis level.

- Some first-pass coverage already exists:
  - plain-text manual search
  - reviewed command lookup
  - manual-sample metadata
  - lightweight script scanning
- The remaining work is mostly about:
  - where to expand next
  - why certain manual areas should be prioritized
  - when a roadmap theme is mature enough to become a concrete issue

This document is therefore a roadmap/design note, not an implementation-ready
spec for one immediate feature.

## Current State

The repository already supports a narrow but useful MCP surface around the
Topdrawer manual and existing Topdrawer scripts.

Implemented baseline:

- `search_manual` for broad plain-text search
- `lookup_command` for reviewed command lookup
- sample metadata lookup
- lightweight script scanning for command structure
- narrow rendering of existing Topdrawer input files

The repository does not yet aim for broad, uniform structured coverage across
the full manual. Coverage is intentionally uneven and guided by immediate
practical value.

## Guiding Principles Inferred From Existing Issues

The earlier roadmap issues consistently point to the same operating principles.

### 1. Expand in stages, not all at once

The repository should not try to convert the entire manual into a fully
structured system in one pass. Coverage grows in small reviewable stages.

### 2. Prefer practical agent utility over theoretical completeness

Coverage should expand first where it improves real agent behavior:

- safer edits
- better interpretation of sample scripts
- more reliable lookup for high-value commands

This is more important than broad topical completeness.

### 3. Keep the runtime surface narrow and maintainable

The project should remain a small MCP server with a limited, understandable
tool surface. New coverage should not imply a large parser, database, or
general-purpose manual platform.

### 4. Preserve plain-text search as the fallback baseline

Structured or semi-structured guidance can expand over time, but
`search_manual` remains the universal fallback. Coverage expansion supplements
search; it does not replace it.

### 5. Promote concrete gaps, not vague ambitions

Roadmap themes should become issues only when they represent a specific
missing task. Broad future intentions belong in roadmap/spec space until they
can be turned into concrete work.

## Theme Buckets

The existing roadmap issues naturally cluster into three coverage themes.

### 1. Core Command Coverage

This theme covers command families that most directly affect script reading,
editing, and explanation.

Examples include:

- plotting commands
- data-flow-adjacent commands
- command structures that appear in sample scripts

This theme is the closest to day-to-day agent usefulness.

### 2. Devices And Data Basics

This theme covers operational topics that matter when working with Topdrawer
input/output behavior and data entry conventions.

Examples include:

- device/output basics
- input/data conventions
- related manual sections that help agents reason about file behavior

This is useful, but typically follows core command coverage.

### 3. Layout And Styling

This theme covers appearance and presentation topics.

Examples include:

- layout controls
- styling topics
- formatting-oriented manual areas

This is still valuable, but tends to matter after the agent can already reason
about command structure and baseline data flow.

## Why This Order

The order is not arbitrary. It follows from the repository's purpose.

### Core commands first

Core command coverage comes first because it most directly improves:

- interpretation of sample files
- safe script modification
- command-level explanation
- command lookup quality

### Devices and data basics second

Devices and data basics come after core commands because they are useful for
runtime and file-behavior reasoning, but are less central than understanding
the script's main command structure.

### Layout and styling later

Layout and styling should generally follow because they improve expressiveness
and presentation, but they are less foundational than understanding what the
script does and how its data or output flow works.

## Promotion Rules For New Issues

Coverage roadmap items should move into GitHub issues only when they cross
from intent into concrete work.

A roadmap theme is ready to become an issue when all of the following are
true:

- a specific gap is identified
- the gap maps to a bounded repository change
- the expected runtime or data surface is narrow enough to describe clearly
- success can be verified without reopening the entire roadmap question

Good examples of promotable issues:

- add reviewed lookup support for a specific command family
- add a narrow sample-guidance data payload for a concrete script pattern
- add one missing manual-derived artifact required by an approved lookup tool

Bad examples that should stay in roadmap/spec space:

- expand coverage more broadly
- support more of the manual
- improve styling coverage someday

## Non-Goals

This roadmap does not imply:

- full structured coverage of the Topdrawer manual
- complete parser-driven understanding of all syntax
- a database-backed manual exploration system
- broad source-ingestion machinery
- immediate issue creation for every future topic mentioned here

## Relationship To Existing Issues

This note absorbs the roadmap intent that was previously spread across:

- `#1`
- `#5`
- `#6`
- `#7`
- `#35`

Those issues are better treated as roadmap/design material than as open
implementation tasks.

Concrete runtime gaps that are already specific enough should remain separate
issues. Structured lookup follow-up work, for example, belongs with issue
`#12`, not in this roadmap note.

## Exit Criteria For This Roadmap Note

This note remains useful as long as coverage expansion is primarily governed by
theme-level prioritization and promotion rules.

Individual parts of this roadmap should move out into standalone issues or
plans only when:

- a concrete gap is selected
- the scope is bounded
- the resulting task is reviewable on its own
