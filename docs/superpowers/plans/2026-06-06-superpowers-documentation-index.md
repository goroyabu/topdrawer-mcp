# Superpowers Documentation Index Implementation Plan

**Goal:** Add a top-level Superpowers reading guide and a short `AGENTS.md`
pointer so future agents can distinguish current guidance from historical
specs and plans.

## Task 1: Add the Superpowers README

Create `docs/superpowers/README.md` with sections for:

- purpose
- reading order
- current guidance documents
- historical specs and plans
- current implementation status checks
- when to add new documents

The README must state that specs and plans are not authoritative
implementation-status tables.

## Task 2: Add the agent-facing pointer

Update `AGENTS.md` under `Issue And Superpowers Boundaries`.

The pointer should tell agents to read `docs/superpowers/README.md` before
interpreting individual Superpowers specs or plans, and to check code, tests,
commits, or merged pull requests before deciding implementation status.

## Task 3: Verify the documentation-only change

Run documentation checks:

- confirm `docs/superpowers/README.md` exists
- confirm `AGENTS.md` references `docs/superpowers/README.md`
- run `git diff --check`

No code tests are required for this documentation-only change.
