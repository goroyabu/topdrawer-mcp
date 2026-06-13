# Fresh-Session Workflow Validation Result (2026-06-13)

Related issue: #53

## Summary

Fresh-session validation was run against the current workflow-validation
scenarios to judge whether the MCP surface is stable enough for the current
`v1.0` discussion.

Overall outcome:

- `existing-script-repair-typo`: pass
- `ambiguous-goal-polar-or-error-bars`: partial pass
- `unsupported-direct-function-plot`: pass with caveat
- `runtime-triage-missing-render-prereq`: pass

The current surface supports the strongest intended workflows, but the results
still show some friction in discovery-oriented flows and unsupported-request
handling.

## Scenario Results

### existing-script-repair-typo

- Outcome: pass
- Notes:
  - The agent identified the typo in the script and repaired it.
  - The corrected script rendered successfully.
- Surface observations:
  - `scan_topdrawer_file`
  - `search_manual`
  - `render_topdrawer_file`
- Validation takeaway:
  - The primary repair workflow is usable in a fresh session.

### ambiguous-goal-polar-or-error-bars

- Outcome: partial pass
- Notes:
  - The agent found the likely command path for making the plot polar.
  - The run stalled at a confirmation step instead of completing the edit in
    the same flow.
- Surface observations:
  - discovery flow was usable
  - command-family selection was plausible
  - autonomy was weaker than expected
- Validation takeaway:
  - The surface is good enough to guide discovery, but not yet consistently
    frictionless for vague requests.

### unsupported-direct-function-plot

- Outcome: pass with caveat
- Notes:
  - The first fresh-session attempt did not produce a usable conclusion in a
    reasonable time.
  - A narrowed follow-up prompt in a fresh session produced the expected
    diagnosis: the current MCP surface does not directly support drawing a
    Gaussian curve from a formula alone.
  - The agent correctly explained the missing capability and the closest
    supported path.
- Surface observations:
  - unsupported capability boundaries can be explained
  - unsupported-task handling may still need tighter prompting than ideal
- Validation takeaway:
  - The surface can communicate missing capability, but this path is less
    stable than the main repair/triage flows.

### runtime-triage-missing-render-prereq

- Outcome: pass
- Notes:
  - The agent distinguished runtime failure from script failure.
  - The validated reproduction path used a fresh-session MCP configuration
    override for `GS_EXECUTABLE_PATH`.
  - `get_server_runtime_info` gave the key diagnostic signal.
- Surface observations:
  - `get_server_runtime_info`
  - render failure handling
  - runtime/config separation
- Validation takeaway:
  - Runtime triage is workable when the environment failure is reproduced in a
    controlled way.

## Cross-Scenario Observations

- The strongest current path is existing-script repair with command inspection
  and render verification.
- Discovery without explicit command naming is viable, but still susceptible to
  hesitation and confirmation stalls.
- Unsupported-request explanation works, but it is not yet as robust as the
  main workflows.
- Runtime triage depends on a clearly reproducible failure setup; the
  fresh-session MCP config override is the verified method for that setup in
  this repository.

## v1.0 Discussion Impact

- This validation run is positive evidence for the current `v1.0` discussion.
- It does not by itself settle the release decision.
- The main remaining concerns from this run are:
  - autonomy and completion behavior in ambiguous discovery flows
  - stability of unsupported-request handling without prompt narrowing
