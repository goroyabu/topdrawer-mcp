# Repository Agent Guidance

## Scope

This repository maintains an MCP server and supporting preprocessing pipeline
for agent-facing access to the Topdrawer manual.

Focus on documentation ingestion, indexing, source traceability, and manual
lookup behavior. Do not turn this repository into a build/install wrapper for
`td` itself.

## Versioning Policy

- Keep project/package version metadata aligned with release tags.
- Use Git tags in the form `vX.Y.Z`.
- Prefer full semantic versions.
- Use patch releases for small maintenance fixes, documentation corrections,
  and indexing quality improvements.
- Use minor releases for meaningful user-facing milestones such as:
  - MCP tool/interface additions
  - preprocessing/index schema changes
  - major coverage expansions
- If the project is still pre-1.0, prefer small focused releases and keep scope
  clear in each tag.

## Development Workflow

- Do not commit directly to `main` for normal development work.
- Start work from a new topic branch created from `main`.
- Merge changes into `main` through a pull request.
- Prefer deleting merged topic branches when no longer needed.

## Branch and PR Policy

- Keep pull requests focused on one coherent change.
- Separate preprocessing/index changes from server behavior changes when
  practical.
- Before merging, confirm that required checks pass.
- Keep PR titles and labels useful for generated release notes.
- Apply a release-note label when practical, such as `build`, `docs`, `data`,
  `mcp`, `index`, or `release`.

## Issue-Driven Follow-up

- Capture manual coverage expansion and source-policy changes as GitHub issues.
- Before starting new work, review open issues first.
- Keep each pull request aligned with one issue or one small related group of
  issues where practical.
- Do not silently broaden scope; record expansion explicitly in issues.

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

- Treat `topdrawer.doc` as the primary manual source unless repository policy
  changes.
- Treat `topdrawer4.0.hlp` as a compact companion reference.
- Treat `contents.html` as a structure/index aid.
- Do not ingest the full generated `html/*.html` tree in the initial phase
  unless an issue explicitly expands scope.
- Keep source acquisition deterministic and reproducible.
- Prefer explicit source metadata such as version, origin URL, and checksums
  when practical.

## Indexing and Traceability Policy

- Preserve traceability from indexed entries back to canonical manual sections.
- Prefer small, inspectable preprocessing outputs over opaque pipelines.
- Keep parsing, normalization, and MCP-serving concerns separated.
- When schema or indexing behavior changes, document compatibility impact.
- Avoid lossy transformations unless they are deliberate and recorded.

## Documentation Consistency Rules

- Keep README focused on repository purpose, source policy, setup, and phased
  coverage.
- Update documentation when canonical sources, indexing schema, MCP tools, or
  supported setup flow changes.
- Record phase boundaries and coverage growth explicitly.
- Keep examples consistent with the currently supported MCP surface.

## Packaging and Verification

- Keep the repository runnable from a clean environment using documented setup.
- Prefer lightweight reproducible local setup over undocumented assumptions.
- If source fetching or indexing behavior changes, verify the documented flow
  from source acquisition through index generation.
- Keep generated artifacts out of version control unless intentionally tracked.

## Change Discipline

- Do not mix broad manual-coverage expansion with unrelated refactors.
- Prefer narrow, reviewable changes over large undocumented rewrites.
- Do not silently broaden scope from “lookup support” into unrelated assistant
  features unless issues and repository policy are updated first.
- Preserve the distinction between:
  - source acquisition
  - preprocessing/index generation
  - MCP server behavior
  - downstream/editor integrations
