# Superpowers Documentation

## Purpose

This directory records design intent, requirements analysis, roadmap notes, and
implementation plans created through the Superpowers workflow.

These documents help explain why changes were made and how work was planned.
They are not, by themselves, authoritative implementation-status tables.

## How To Read This Directory

Start with current roadmap/design notes when you need project direction. Use
focused specs and plans as historical context for specific changes.

Specs record intent, requirements, design decisions, roadmap notes, or open
questions at the time they were written.

Plans record an implementation approach for a specific change. They are not
guaranteed to be updated after the work is complete.

Do not infer that work is incomplete only because an older spec or plan
describes it as future work.

Use roadmap/design notes for current direction, and use older focused
specs/plans as historical context.

## Current Guidance Documents

These documents are the current high-level design references for active
roadmap or design topics:

- `docs/superpowers/specs/2026-06-03-preprocessing-and-structured-lookup-roadmap-design.md`
- `docs/superpowers/specs/2026-06-03-coverage-expansion-roadmap-design.md`
- `docs/superpowers/specs/2026-06-03-tabular-data-flow-design.md`
- `docs/superpowers/specs/2026-06-06-v0.2-release-followups-design.md`
- `docs/superpowers/specs/2026-06-06-render-device-control-design.md`
- `docs/superpowers/specs/2026-06-07-agent-workflow-validation-for-v1-design.md`

They should be read before older focused specs when deciding how a topic should
move forward.

## Historical Specs And Plans

Focused specs and plans record the intent and implementation approach for a
specific change at the time that change was planned.

Historical focused specs include:

- `docs/superpowers/specs/2026-06-02-contributing-guide-design.md`
- `docs/superpowers/specs/2026-06-03-set-order-set-font-sample-coverage-design.md`

Historical plans include:

- `docs/superpowers/plans/2026-06-02-contributing-guide.md`
- `docs/superpowers/plans/2026-06-03-set-order-set-font-sample-coverage.md`

Other focused specs and plans should usually be treated the same way unless a
document is explicitly being used as current guidance for an active topic.

These documents may describe work that has since been completed, extended, or
superseded by later design decisions. Treat them as records of the decision
process, not as a live backlog or an authoritative implementation-status table.

## How To Determine Current Implementation Status

To determine current implementation status, inspect the implementation files,
tests, git history, and merged pull requests.

For command lookup work, for example, check the tracked lookup data, runtime
code, and unit tests rather than relying on one older focused spec.

Use Superpowers documents to understand intent and constraints. Use the repo
state to determine what is currently implemented.

## When To Add New Documents

Add a new spec when a non-trivial change needs to record intent, requirements,
roadmap direction, or design decisions.

Add a new plan when an approved change needs implementation steps that another
agent or engineer can execute.

In the usual Superpowers flow, the spec comes first and captures the approved
design direction. The plan follows after that and translates the approved spec
into implementation steps.

Keep broad roadmap, requirements-analysis, and design-exploration topics in
`docs/superpowers/specs/` until they become concrete enough to track as GitHub
issues or implementation plans.
