# Repository Agent Guidance

## Scope

This repository maintains a minimal MCP server for agent-facing plain-text
search over the Topdrawer manual and narrow runtime rendering of existing
Topdrawer input files.

Focus on simple manual search behavior, narrow render behavior, MCP stdio
compatibility, and a small maintainable Python package layout. Do not turn this
repository into a build/install wrapper for `td` itself.

## Versioning Policy

- Keep project/package version metadata aligned with release tags.
- Use Git tags in the form `vX.Y.Z`.
- Prefer full semantic versions.
- Use patch releases for small maintenance fixes, documentation corrections,
  and search behavior improvements.
- Use minor releases for meaningful user-facing milestones such as:
  - MCP tool/interface additions
  - manual data format changes
  - broader documented setup support
- If the project is still pre-1.0, prefer small focused releases and keep scope
  clear in each tag.

## Development Workflow

- Do not commit directly to `main` for normal development work.
- Start work from a new topic branch created from `main`.
- Merge changes into `main` through a pull request.
- Prefer deleting merged topic branches when no longer needed.

## Branch and PR Policy

- Keep pull requests focused on one coherent change.
- Before merging, confirm that required checks pass.
- Keep PR titles and labels useful for generated release notes.
- Apply a release-note label when practical, such as `build`, `docs`, `data`,
  `mcp`, or `release`.

## Release Workflow

When preparing a release:

1. Merge the release PR into `main`.
2. Confirm that CI on `main` passes.
3. Update project/package version metadata if needed.
4. Verify version-sensitive documentation if needed.
5. Tag the release with the matching `vX.Y.Z` tag.
6. Create the GitHub Release from the tag using generated notes.

## Release Notes Policy

- Use GitHub's generated release notes by default.
- Keep release-note categories aligned with labels actually used in pull
  requests.
- Treat release-note generation as a repository workflow concern, not a README
  concern, unless user-facing setup or usage changes.

## Commit Message Policy

- Use a short imperative subject in the form `<area>: <summary>`.
- Keep the subject readable in `git log --oneline`.
- Prefer stable areas such as `mcp`, `index`, `data`, `docs`, `build`,
  `release`, or `meta`.
- For changes spanning multiple areas, choose the area that best represents the
  main user-facing outcome.
- Wrap the body at a readable width when adding details.
- In the body, explain why the change matters, not just what files changed.

Recommended template:

```text
<area>: <summary>

- Reason or outcome 1
- Reason or outcome 2
- Optional note about coverage, indexing, or release alignment
```

## Canonical Source Policy

The MCP server reads a single plain-text manual file by default:
`data/topdrawer.txt`.

Keep the current runtime contract simple: the server should search one
plain-text file or an explicitly configured replacement.

Use `docs/source-policy.md` for canonical manual source decisions, companion
source decisions, and generated data expectations. Small build-time
preprocessing additions are acceptable when they stay within the documented
source policy and an agreed issue scope. Do not add broad preprocessing,
structured indexing, command extraction, or source acquisition machinery
outside that scope.

## Documentation Consistency Rules

- Keep README focused on repository purpose, manual text location, render
  prerequisites, setup, and the supported MCP tools.
- Update documentation when the manual text location, MCP tool surface, or
  supported setup flow changes.
- Keep examples consistent with the currently supported MCP surface.

## Packaging and Verification

- Keep the repository runnable from a clean environment using documented setup.
- Prefer lightweight reproducible local setup over undocumented assumptions.
- Use `pyproject.toml` for the Python package entrypoint.
- Keep generated artifacts out of version control unless intentionally tracked.

## Change Discipline

- Prefer narrow, reviewable changes over large undocumented rewrites.
- Do not silently broaden scope from simple plain-text search into unrelated
  assistant features unless repository policy is updated first.
- Preserve the distinction between:
  - manual data
  - MCP server behavior
  - downstream/editor configuration
