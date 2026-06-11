# Agent Workflow Validation Scenario Assets

## Summary

Add a first batch of manual evaluation assets for deciding whether the current
MCP surface is stable enough to support a future `1.0` release judgment.

The assets should live under `tests/fixtures/workflow_validation/` and should
cover one primary scenario for each validation family:

- existing script repair
- ambiguous goal discovery
- recovery and misstep handling
- environment and runtime triage

## Implementation Steps

1. Create one scenario directory per validation family.
2. For each scenario, add exactly:
   - `input.top`
   - `prompt.md`
   - `expected.md`
3. Keep prompts realistic and user-facing rather than test-label-like.
4. Keep `expected.md` focused on:
   - scenario intent
   - expected workflow
   - required MCP surface elements
   - success criteria
5. Add a light unit test that protects the asset layout and minimum content
   expectations without turning the scenarios into automated agent evaluation.

## Verification

- run the new workflow-asset unit test
- confirm all four scenario directories exist with the expected three files
- confirm the `expected.md` files mention workflow and success criteria

## Defaults

- first batch is evaluation assets only, not automated end-to-end tests
- each scenario uses exactly three files unless a later scenario proves that
  extra files are necessary
