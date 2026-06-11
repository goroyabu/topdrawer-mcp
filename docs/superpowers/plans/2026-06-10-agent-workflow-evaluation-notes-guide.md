# Agent Workflow Evaluation Notes Guide

## Summary

Add a lightweight Markdown note for judging manual workflow-validation runs
during the current `1.0` readiness discussion.

This document is not intended to create a permanent per-run record. It is a
shared guide for what to examine and what kinds of observations are worth
writing down when a scenario run exposes ambiguity, detours, or release
blocking behavior.

The note should stay separate from each scenario bundle so the bundles remain
stable as reusable inputs:

- `input.top`
- `prompt.md`
- `expected.md`

## Implementation Steps

1. Add a shared Markdown evaluation-notes guide under
   `tests/fixtures/workflow_validation/`.
2. Keep it focused on viewpoints rather than a required fill-in form.
3. Include both:
   - qualitative observations
   - lightweight detour indicators
4. Do not change existing scenario directories or the asset-layout test.

## Guide Requirements

The guide should cover:

- scenario context
- outcome judgment
- surface usage
- trial-and-error / detour indicators
- recovery behavior
- render/result notes when applicable
- runtime-triage notes when applicable
- follow-up observations

## Verification

- confirm the guide sits outside scenario directories
- confirm the existing asset-layout test still reflects the scenario bundle
  contract
- manually inspect the guide for clarity and realistic use during fresh
  sessions
