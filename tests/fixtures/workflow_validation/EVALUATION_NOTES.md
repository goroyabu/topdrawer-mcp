# Workflow Validation Evaluation Notes

This document captures the evaluation viewpoints to use when running the
workflow-validation scenarios for the current `1.0` readiness discussion.

It is not a hard test artifact and it does not need to be filled in for every
run. Treat it as a lightweight guide for what to look at and what to note when
the run reveals something important.

The scenario assets remain:

- `input.top`
- `prompt.md`
- `expected.md`

## When To Use This

Use these notes when you run a fresh-session evaluation and want a consistent
way to judge the result.

You do not need to write a formal report every time. A short memo is enough if
the run surfaces ambiguity, detours, or a likely `1.0` blocker.

## Evaluation Viewpoints

### Scenario Context

Keep these basics visible during evaluation:

- Scenario ID
- Scenario family
- User prompt used
- Intended goal in one sentence
- Any special environment setup

### Outcome

Check the high-level result first:

- Did the agent reach the intended goal?
- Was the result a clear success, a partial success, or a failure?
- If the goal was not reached, what stopped progress?

### Surface Usage

Look at how the MCP surface was used:

- Which prompts were used
- Which resources were used
- Which tools were used
- Whether the order of steps was natural or awkward

### Detour And Trial-And-Error

Watch for unnecessary loops or backtracking:

- `search_manual` call count
- `lookup_command` call count
- `scan_topdrawer_file` / `scan_topdrawer_script` call count
- Distinct command families checked
- Recovery cycles
- Overall detour level:
  - low
  - moderate
  - high

This is meant to show whether the current surface leads the agent forward
cleanly or makes it wander.

### Reasoning Quality

Check whether the workflow was sound, not just whether it eventually worked:

- Did the agent choose an appropriate first step?
- Did it rely on the MCP surface rather than hidden prior knowledge?
- Did it explain the reasoning clearly enough to audit?
- Where did it hesitate or start guessing?

### Recovery

For scenarios with a wrong first path or incomplete first diagnosis, note:

- Whether the first line of reasoning was sufficient
- What the first wrong or incomplete path was
- What triggered recovery
- Whether the recovery was successful

### Render Or Result Notes

Use this viewpoint when the scenario expects a concrete script change or render
attempt:

- Was the script changed?
- Was render attempted?
- Did render succeed?
- If render succeeded, was the result plausibly aligned with the prompt?
- If render failed, was the failure interpreted correctly?

### Runtime Triage Notes

Use this viewpoint when the scenario is mainly about environment diagnosis:

- Was `get_server_runtime_info` used?
- Did the agent distinguish:
  - script problem
  - runtime/configuration problem
  - external dependency problem
- Was the next recommended action within repository scope?

### Follow-Up Observations

When a run reveals a real issue, note only the important points:

- Surface gaps observed
- Documentation gaps observed
- Candidate improvements
- Whether this run should count as evidence for or against a `1.0` release
