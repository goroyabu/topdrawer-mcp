# Repository Agent Guidance

## Workflow Source

The source of truth for repository development workflow is:

`docs/development-workflow.md`

Use `CONTRIBUTING.md` for human-oriented contribution steps. Use this file for
repository-specific agent guidance, technical scope boundaries, and judgment
rules that affect implementation choices.

## Scope

This repository maintains a minimal MCP server for agent-facing plain-text
search over the Topdrawer manual and narrow runtime rendering of existing
Topdrawer input files.

Focus on simple manual search behavior, narrow render behavior, MCP stdio
compatibility, and a small maintainable Python package layout. Do not turn this
repository into a build/install wrapper for `td` itself.

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
- Check `docs/development-workflow.md` and this file for workflow-impacting
  changes.

## Packaging and Verification

- Keep the repository runnable from a clean environment using documented setup.
- Prefer lightweight reproducible local setup over undocumented assumptions.
- Use `pyproject.toml` for the Python package entrypoint.
- Keep generated artifacts out of version control unless intentionally tracked.
- Verify claims about passing behavior with actual command output before
  reporting success.

## GitHub Write Operations

- Treat GitHub MCP as read-only and use `gh` CLI for GitHub write operations.
- When creating or editing issue bodies, pull request bodies, or long comments,
  do not embed the full body directly in shell arguments.
- Write the intended Markdown content to a local temporary file first, then use
  the file-based `gh` option where available such as `--body-file`.
- If a `gh` subcommand does not accept a body file for the final action, post
  the long comment first from a temporary file and then run the final command
  separately.

## Issue And Superpowers Boundaries

- Treat GitHub issues as concrete repository tasks, bugs, or operational
  problems that are specific enough to act on directly.
- Do not keep broad roadmap, requirements-analysis, or design-exploration
  topics open as GitHub issues when they are not yet concrete tasks.
- Capture roadmap, design, and requirements material in
  `docs/superpowers/specs/`.
- Read `docs/superpowers/README.md` before interpreting individual
  Superpowers specs or plans.
- A Superpowers spec does not need to be implementation-ready. It may record
  roadmap intent, requirements analysis, or design questions when that is the
  correct current maturity level.
- Do not treat an individual Superpowers spec or plan as the source of truth
  for current implementation status without checking code, tests, commits, or
  merged pull requests.
- Promote work from spec space into issue or plan space only when the task
  becomes concrete enough to implement or verify independently.

## Change Discipline

- Prefer narrow, reviewable changes over large undocumented rewrites.
- Do not silently broaden scope from simple plain-text search into unrelated
  assistant features unless repository policy is updated first.
- Preserve the distinction between:
  - manual data
  - MCP server behavior
  - downstream/editor configuration
- Follow this file for technical boundaries and `docs/development-workflow.md`
  for repository workflow policy.
