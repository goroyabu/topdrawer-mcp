# Superpowers Documentation Index Design

## Goal

Add a top-level guide for reading this repository's Superpowers documents so
agents do not confuse historical specs and plans with current implementation
status.

## Problem

The repository now keeps both roadmap/design notes and focused implementation
records under `docs/superpowers/`. Without an entry point, a later agent may
read one focused historical spec and infer that already-completed work is still
future work.

## Intended Behavior

`docs/superpowers/README.md` should be the entry point for this directory. It
should explain:

- what specs and plans are for
- which roadmap/design notes currently provide high-level guidance
- which focused specs/plans are historical records
- how to verify current implementation status from code, tests, git history,
  and merged pull requests

`AGENTS.md` should point agents to that README without duplicating the full
guide.

## Non-Goals

- Do not rewrite existing historical specs or plans.
- Do not use the README as a live task tracker.
- Do not change the repository workflow policy source of truth in
  `docs/development-workflow.md`.

## Expected Impact

Future agents should have a stable reading order:

1. Read repository workflow and agent guidance.
2. Read `docs/superpowers/README.md`.
3. Read current roadmap/design notes for direction.
4. Use older focused specs and plans as historical context.
5. Check code, tests, commits, and merged pull requests for current
   implementation status.
