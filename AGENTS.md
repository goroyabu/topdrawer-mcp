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
