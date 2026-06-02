# Contributor And Workflow Docs Design

## Goal

Clarify the repository's documentation split for development workflow by:

- adding a human-oriented `CONTRIBUTING.md`
- introducing a workflow source-of-truth document
- reducing `AGENTS.md` to agent-facing technical guidance and workflow entry
  points

## Scope

- Create a contributor guide focused on day-to-day repository participation.
- Add a dedicated workflow policy document under `docs/`.
- Move workflow-policy details out of `AGENTS.md` while keeping its technical
  repository guidance intact.
- Explicitly adopt Conventional Commits in contributor-facing workflow
  documentation.
- Add simple repository templates for issues and pull requests.
- Keep project-specific runtime and source-policy details aligned with the
  existing `README.md`.
- Record the current Superpowers-oriented documentation flow for non-trivial
  changes.

## Non-goals

- Do not change repository behavior, packaging, or tests.
- Do not rewrite `README.md` unless the new workflow split requires a direct
  reference update.
- Do not perform a broader issue cleanup or release-process overhaul here.

## Design

The repository should use three documents with distinct roles:

- `docs/development-workflow.md` as the source of truth for workflow policy
- `CONTRIBUTING.md` as the human-oriented participation guide
- `AGENTS.md` as the agent-oriented technical boundary and workflow entry point

`CONTRIBUTING.md` should act as a practical entry point for human contributors.
It should explain how to work in the repository and where to look for deeper
project guidance without becoming the source of truth for workflow rules.

The document should:

- summarize repository scope so contributors do not broaden it accidentally
- point contributors to `README.md`, `AGENTS.md`, `docs/source-policy.md`, and
  the workflow source-of-truth document
- document branch, commit, verification, PR, and release expectations
- describe the current expectation that substantial work is planned through
  Superpowers specs and plans rather than GitHub issues

The workflow source-of-truth document should define:

- what belongs in GitHub issues
- when specs and plans are required
- what qualifies as a minor-change exception
- that commit subjects follow Conventional Commits
- when issues close
- which documents must be checked for workflow-impacting changes

`AGENTS.md` should keep only:

- repository scope boundaries
- source-policy boundaries
- documentation consistency expectations that affect agent judgment
- verification and change-discipline guidance that affects implementation
  choices
- a short reference to the workflow source-of-truth document

Simple GitHub templates should be added to support the workflow:

- an issue template for reporting concrete problems
- a pull request template that prompts for summary, verification, and links to
  issue/spec/plan

## Expected Impact

- Human contributors get an obvious place to start.
- Workflow expectations gain a clear source of truth instead of being spread
  across agent guidance and contributor guidance.
- Agent guidance becomes smaller and more focused on technical boundaries.
- Superpowers planning records remain separate from the final workflow policy.
