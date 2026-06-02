# Tabular Data Flow Design

## Goal

Capture the design questions around turning tabular input into Topdrawer
scripts, so the earlier design-oriented issue can be closed without losing the
problem statement, constraints, and decision points.

## Status Level

This topic is primarily at requirements-analysis and design-decision level.

- The repository already supports:
  - manual search
  - reviewed command lookup
  - sample metadata lookup
  - lightweight script scanning
  - narrow rendering of existing Topdrawer input files
- The repository does not yet support:
  - taking tabular input directly and turning it into Topdrawer input
  - a dedicated MCP surface for tabular-to-Topdrawer generation
  - a defined preprocessing path for tabular plotting inputs

This document is therefore a design note, not an implementation-ready spec for
one immediate feature.

## Current State

The current repository is built around understanding and rendering existing
Topdrawer material.

Current strengths:

- search and lookup over manual-derived data
- inspection of existing script structure
- rendering existing `.top` inputs through external `td`

Current gap:

- there is no approved flow for starting from tabular data and arriving at a
  Topdrawer script or rendered output

This means the repository currently helps most with:

- understanding manual guidance
- inspecting existing scripts
- rendering files that already exist

It does not yet help with creating those files from higher-level tabular input.

## Problem To Solve

The core question is not simply "should CSV be supported?" It is narrower:

- when an agent has structured table-like data and wants a Topdrawer plot, what
  responsibility belongs inside this repository?
- what should remain outside the repository as agent-side transformation or
  user-provided script authoring?

This distinction matters because the repository is intentionally narrow and
should not silently become a general plotting platform.

## Candidate Approaches

### 1. Agent-Side Transformation Only

In this model, the repository stays focused on manual search, lookup, script
inspection, and rendering. Tabular-to-Topdrawer transformation happens outside
the MCP server.

Pros:

- preserves the narrow runtime surface
- avoids introducing a pseudo-plotting API
- keeps responsibility for plot construction outside the server

Cons:

- less reusable structure for agents
- more repeated transformation logic outside the repo
- weaker repository-level conventions for supported plotting flows

### 2. Narrow Helper Surface

In this model, the repository adds one or more very small helpers for turning a
strictly limited tabular input shape into a Topdrawer script fragment or full
script.

Pros:

- creates a reusable, documented narrow path
- can reduce repeated agent-side prompt logic
- can make a first-pass plotting workflow more reliable

Cons:

- risks broadening scope into a plotting system
- requires a much tighter definition of supported inputs and outputs
- may create pressure for more chart types and formatting controls

## Recommended Direction

If this topic is revisited, prefer the narrowest possible version of approach
2, and only if a concrete repeated workflow justifies it.

That means:

- do not add broad "plot arbitrary table data" functionality
- do not add a generic charting abstraction
- do consider a helper only if it targets a single constrained workflow with a
  stable input shape

If no such constrained workflow can be defined, leave the transformation
outside the repository.

## Constraints And Non-Goals

Any future tabular-data flow must preserve the repository's existing
boundaries.

Constraints:

- keep the MCP surface narrow
- avoid turning the repository into a plotting platform
- avoid introducing a large schema or transformation DSL
- keep any supported transformation deterministic and reviewable
- preserve compatibility with the repository's existing manual/search/render
  focus

Non-goals:

- arbitrary CSV-to-chart conversion
- a full declarative plotting API
- automatic support for many chart families at once
- replacing direct script authoring for general Topdrawer use

## First-Pass Scope Questions

If the repository ever adds a tabular-data helper, the first-pass scope should
be explicitly narrowed before implementation begins.

Questions that must be answered first:

- Is the target only one plotting family, such as a simple `PLOT` flow?
- Is the input shape limited to a single x/y series?
- Does the output include only minimal labels and defaults?
- Is styling intentionally deferred?
- Is the output a script fragment, a full `.top` file, or something else?

Without those limits, this topic is too broad to become a safe issue.

## Open Questions

The remaining design questions are:

- What concrete user or agent workflow justifies repository support here?
- Is there a recurring transformation pattern that is stable enough to support?
- Should the repository ever own this conversion, or only document examples?
- If a helper is added, what is the smallest supported interface?
- What should be validated versus left to downstream `td` execution?

## Promotion Rules For New Issues

This topic should move from design/spec space into issue space only when:

- a concrete tabular-input workflow is selected
- the supported input shape is explicitly bounded
- the resulting Topdrawer output form is defined
- the work can be implemented without broadening the repository beyond its
  stated scope

Good candidates for a future issue:

- add a helper for one constrained x/y plotting workflow
- add documentation and examples for one explicitly supported transformation
  shape

Bad candidates that should stay in design/spec space:

- support CSV plotting in general
- accept arbitrary tables and infer chart structure
- add a generic plotting interface to the MCP server

## Relationship To Existing Issue

This note absorbs the design-oriented intent behind `#26`.

`#26` is better treated as a design question than as an always-open
implementation task, because the main unresolved work is still about deciding:

- whether repository support is appropriate at all
- where the responsibility boundary belongs
- what a safe first-pass scope would be

Concrete implementation work should be tracked separately only after those
decisions are made.

## Exit Criteria For This Design Note

This note remains useful until one of the following becomes true:

- the repository decides to keep all tabular-data transformation outside its
  scope
- a narrow supported workflow is defined clearly enough to become a concrete
  issue and then an implementation plan
