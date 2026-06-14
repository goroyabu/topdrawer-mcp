# Development Workflow

## Source of Truth

This document is the source of truth for repository development workflow.

- `AGENTS.md` provides repository-specific agent guidance and points agents to
  this document for workflow policy.
- `CONTRIBUTING.md` provides human-oriented contribution steps and points
  contributors to this document for workflow policy.

When workflow rules change, update this file first.

## Issue Policy

GitHub issues are for problems that need to be fixed.

Issues may cover:

- bugs
- implementation and documentation mismatches
- workflow inconsistencies
- other concrete problems that require correction

Issues should not be used as the main place to keep:

- requirements definitions
- feature planning notes
- implementation plans
- idea backlogs or concept memos

## Superpowers Documentation Policy

For non-trivial changes, use Superpowers documentation before implementation.

- Record intended behavior and requirements in `docs/superpowers/specs/`.
- Record implementation steps in `docs/superpowers/plans/`.
- Use GitHub issues to track the problem being solved, not the implementation
  plan itself.

For this repository, the expected design flow for non-minor work is:

1. Identify the concrete problem.
2. Record the intended change in a spec.
3. Review and approve the spec direction before proceeding.
4. Record the implementation approach in a plan.
5. Implement, verify, and document the change.

The intent is to keep design work ahead of implementation work.

For non-trivial changes, do not treat the implementation plan as the place
where the change is first defined. The spec should already capture the intended
behavior and design direction before the plan is written.

## Minor Change Exception

The only changes that do not require spec/plan documentation are:

- typo-only edits
- comment-only edits
- link-only edits
- formatting-only edits

All other changes require spec/plan documentation before implementation.

## Contribution Flow

For normal development work:

1. Start from `main`.
2. Create a focused topic branch.
3. Prepare the required spec/plan documents unless the change qualifies as a
   minor-change exception.
4. Review the spec and confirm the design direction before implementation.
5. Implement the change.
6. Run the relevant verification steps.
7. Update any required documentation.
8. Open a pull request and link the related issue when applicable.

Keep changes narrow and reviewable.

## Release Flow

For repository releases such as `1.0.0`, use this sequence:

1. Confirm that the intended release scope is already complete on `main`.
2. Create a focused release branch from `main`.
3. Bump the package version in `pyproject.toml`.
4. Update `uv.lock` when the editable project entry records the package
   version, so the lockfile stays consistent with `pyproject.toml`.
5. Run the relevant verification for the release-preparation branch.
6. Open and merge a pull request containing the version bump and any release
   workflow documentation updates.
7. After the pull request is merged, create the release tag and GitHub Release
   from the merged `main` state.
8. Sync local branches and clean up the release branch after the release work
   is complete.

Keep release changes narrow. Do not mix unrelated feature work into the
release-preparation branch.

## Issue Close Policy

Issues close when the corresponding change is merged to `main`.

Before a change is ready to merge, all of the following must already be true:

- the implementation is complete for the intended fix
- the relevant verification has been run successfully
- the necessary documentation updates are included

## Documentation Check Requirements

For every change, check whether updates are needed in:

- this document
- `AGENTS.md`

Also check `README.md` when a change affects:

- runtime behavior
- setup instructions
- MCP tool surface

## Record of Change Intent

Use each record for one purpose:

- issue: the problem to be fixed
- spec: the intended behavior or design
- plan: the implementation approach
- commit message: the implementation history

Do not use commit messages as the primary home for requirements or planning.
Use Conventional Commits for commit subjects.
