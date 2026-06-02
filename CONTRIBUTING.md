# Contributing to topdrawer-mcp

## Repository Scope

This repository maintains a minimal MCP server for Topdrawer manual lookup and
narrow runtime rendering of existing Topdrawer input. Keep contributions aligned
with that scope.

Contributions should preserve these boundaries:

- keep manual search simple and maintainable
- keep render behavior narrow and runtime-focused
- keep the package layout small and understandable
- do not turn this repository into a build/install wrapper for `td`
- do not add broad preprocessing or indexing machinery outside the documented
  source-policy scope

## Before You Start

Before making changes, read:

- `docs/development-workflow.md` for the repository workflow source of truth
- `README.md` for the current runtime surface and setup flow
- `AGENTS.md` for repository-specific agent guidance and policy
- `docs/source-policy.md` for canonical manual source expectations

If you are making a non-trivial change, write or update Superpowers documents
before implementation:

- specs in `docs/superpowers/specs/`
- implementation plans in `docs/superpowers/plans/`

Use GitHub issues for concrete problems that need to be fixed. Do not use
issues as the main place to draft feature plans or requirement documents. The
workflow rules for issues, planning, and documentation live in
`docs/development-workflow.md`.

## Planning Changes

For changes beyond typo, comment, link, or formatting-only edits:

- define the intended change in a spec document
- write an implementation plan before editing code
- keep the planned change focused and reviewable

For small corrections limited to spelling, comments, links, or formatting,
normal commit history is sufficient. See `docs/development-workflow.md` for the
repository policy behind this distinction.

## Development Workflow

- Do not commit directly to `main` for normal development work.
- Start from `main` and create a focused topic branch.
- Keep each pull request scoped to one coherent change.
- Prefer deleting merged topic branches when they are no longer needed.

## Testing and Verification

Verify the relevant behavior before asking for review or merging.

- run the tests that cover the changed area
- run broader verification when the change affects shared behavior
- keep the repository runnable from a clean environment using the documented
  setup
- update documentation when the runtime surface, manual path behavior, or setup
  flow changes

When a change affects rendering or packaging behavior, verify the documented
workflow still matches the actual commands and prerequisites.

## Commits

Use Conventional Commits for commit subjects.

Use the form:

```text
<type>(<optional-scope>): <summary>
```

Common commit types include:

- `feat`
- `fix`
- `docs`
- `refactor`
- `test`
- `build`
- `chore`

When a scope is useful, prefer repository-relevant scopes such as:

- `mcp`
- `index`
- `data`
- `docs`
- `release`
- `workflow`

If you add a commit body, explain why the change matters rather than listing
files.

Example:

```text
docs(workflow): add contributor guide

- Give human contributors a single entry point for day-to-day workflow
- Preserve AGENTS.md as repository-specific agent guidance
```

## Pull Requests

Before merging a pull request:

- confirm the relevant verification steps pass
- confirm any necessary documentation updates are included
- use the repository pull request template
- keep the title and labels useful for release notes
- apply a release-note label when practical, such as `build`, `docs`, `data`,
  `mcp`, or `release`

If the pull request resolves an existing issue, link it so the issue closes when
the branch merges to `main`. Only merge once the relevant verification and
required documentation updates are already complete.

## Releases

When preparing a release:

1. Merge the release pull request into `main`.
2. Confirm CI on `main` passes.
3. Update project/package version metadata if needed.
4. Verify version-sensitive documentation if needed.
5. Tag the release with the matching `vX.Y.Z` tag.
6. Create the GitHub Release from the tag using generated notes.

Use GitHub's generated release notes by default.

## Related Documents

- `docs/development-workflow.md`: workflow source of truth
- `README.md`: runtime behavior, setup, and MCP tool surface
- `AGENTS.md`: repository-specific agent guidance
- `docs/source-policy.md`: canonical manual-source decisions
