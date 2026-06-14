# Release Workflow Documentation Design

## Goal

Add a small release-specific section to the repository workflow so version bump
and release steps are documented in one stable place instead of being inferred
from conversation history.

## Problem

The repository has a documented development flow, but it does not yet describe
how a release should be prepared and completed.

That leaves several recurring decisions undocumented:

- when to create a release branch
- when to bump the package version
- whether `uv.lock` should be updated with the version bump
- when verification should run relative to the version bump
- how pull request, merge, tag, and GitHub Release steps should be ordered

## Intended Behavior

`docs/development-workflow.md` should gain a short `Release Flow` section that
documents the repository's normal release sequence:

1. confirm the release scope is ready on `main`
2. create a focused release branch
3. bump the package version in `pyproject.toml`
4. update `uv.lock` when the editable project entry reflects the package
   version
5. run the relevant verification
6. open and merge a pull request for the release-preparation change
7. create the tag and GitHub Release from the merged state
8. sync local branches after the release

The documented flow should stay narrow and practical. It should not become a
general release-management handbook.

## Non-Goals

- Do not add CI/CD automation in this change.
- Do not add packaging or publishing instructions beyond the repository's
  current tag and GitHub Release flow.
- Do not duplicate the same release steps across README and AGENTS unless a
  later change creates a user-facing need.

## Expected Impact

Future version bumps should no longer depend on memory of previous release
conversations. Agents and maintainers should have one repository workflow
document that covers both normal development and the release-preparation flow.
