# Agent Workflow Validation For v1 Design

## Goal

Define a spec-level validation approach for deciding whether the current MCP
surface is stable enough to treat as a `1.0` agent-facing workflow.

The purpose of this validation is not only to check that individual tools work,
but to check that a fresh agent session can use the full surface coherently:

- tools
- resources
- prompts

The central question is whether an agent can reliably reach the intended user
goal with the current discovery, lookup, scan, and render flow.

## Status Level

This topic is at evaluation-design level.

- The current `0.2.0` release already provides a coherent MCP surface.
- The remaining question is whether that surface is stable and complete enough
  in real workflow usage to justify a `1.0` release.
- This document defines the candidate validation scenarios for that judgment.

This is not yet a test implementation plan. It is a design for what kinds of
workflow validation should exist.

## Recommended Validation Approach

The recommended approach is a workflow-completeness validation set rather than
only narrow unit-style behavior checks.

The validation should be run from fresh sessions where the agent must discover
and use the current MCP surface, rather than relying on hidden prior knowledge
or out-of-band repository familiarity.

The focus should be on:

- whether the agent can choose the right surface element at each step
- whether it can recover from mistakes
- whether it can handle vague or underspecified user requests
- whether it can distinguish script problems from runtime/environment problems

## Scenario Families

### 1. Existing Script Repair

This family tests the strongest intended workflow of the current surface.

The agent is given an existing `.top` file containing one or more problems and
is asked to produce a corrected result.

Representative scenario types:

- script contains an obvious command typo or unsupported command spelling
- script uses a relevant command incorrectly and needs lookup-guided correction
- script renders, but the output does not match the intended result
- script requires the agent to inspect commands before deciding how to change it

Expected workflow:

1. inspect the script with `scan_topdrawer_file`
2. identify relevant commands
3. consult `lookup_command` or command resources
4. use `search_manual` only when the reviewed command guidance is insufficient
5. propose or apply the correction
6. render or otherwise verify the corrected result when appropriate

What this family is meant to measure:

- whether the current scan/lookup/render surface supports the primary repair
  use case with low ambiguity
- whether command-centered guidance is enough for realistic small fixes

### 2. Ambiguous Goal Discovery

This family tests whether the current surface is usable when the user does not
name the Topdrawer command directly.

Representative scenario types:

- "make this polar"
- "connect the points with a line"
- "add a title"
- "show error bars"
- "make the output look like points instead of a curve"

Expected workflow:

1. use `discover_topdrawer_command` prompt or equivalent prompt-guided flow
2. use `search_manual` with words from the request
3. extract likely command candidates
4. confirm the best candidate with `lookup_command`
5. continue to script editing or explanation

What this family is meant to measure:

- whether the current discovery flow is good enough without a dedicated
  reverse-lookup tool
- whether vague user wording still leads to the relevant command family
- where the current surface still forces too much guesswork

### 3. Recovery And Misstep Handling

This family tests robustness when the agent initially chooses the wrong path.

Representative scenario types:

- the agent first looks up the wrong command
- manual search returns several plausible but different matches
- scan results are not enough by themselves to explain the needed fix
- the agent starts from an incorrect assumption and must recover

Expected workflow:

1. make an initial attempt using the visible MCP surface
2. encounter ambiguity or contradiction
3. recover by switching to a better lookup/search path
4. continue toward a correct explanation or change

What this family is meant to measure:

- whether the current surface is resilient rather than only happy-path capable
- whether resources, prompts, and tools together make recovery practical

### 4. Environment And Runtime Triage

This family tests whether the agent can distinguish script logic problems from
runtime and environment problems.

Representative scenario types:

- `td` is unavailable
- `gs` is unavailable
- render output exists but does not match expectations because of device/output
  behavior
- relative-path or base-directory assumptions cause render failure

Expected workflow:

1. attempt the intended render or inspection flow
2. use `get_server_runtime_info` when runtime prerequisites are suspect
3. separate:
   - script problems
   - runtime configuration problems
   - external dependency availability problems
4. recommend the next corrective action within repository scope

What this family is meant to measure:

- whether runtime triage is understandable to the agent
- whether the server surface is sufficient for troubleshooting without turning
  the repository into an installer

## Success Criteria

This validation should judge more than binary task completion.

The key success dimensions are:

- `goal reachability`
  - the agent gets to the intended outcome or correct diagnosis
- `surface selection`
  - the agent chooses appropriate tools, resources, and prompts at each stage
- `recovery ability`
  - the agent can recover from initial wrong assumptions or poor first choices
- `ambiguity handling`
  - vague user wording still leads to a useful command-discovery path
- `runtime separation`
  - the agent can distinguish content problems from environment problems

The results should be interpreted qualitatively as well as quantitatively.

For example, these are important observations:

- where the agent hesitates
- where it overuses `search_manual`
- where the prompt/resource surface does or does not help
- where the current discovery flow feels incomplete

## Non-Goals

- Do not treat this as a general model-quality benchmark.
- Do not treat this as a pixel-perfect render regression design.
- Do not require full manual coverage before considering `1.0`.
- Do not couple this work to a decision about immediate render-device-control
  implementation.

## Candidate Next Step

If this validation direction is accepted, the next work should define the
concrete fixtures and task prompts needed for each scenario family.

That next step should answer questions such as:

- which `.top` files should be intentionally broken
- which vague user requests should be represented
- which runtime-failure cases should be simulated
- how the pass/fail or observed-outcome notes should be recorded
