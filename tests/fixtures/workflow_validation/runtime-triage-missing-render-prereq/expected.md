# Environment And Runtime Triage: missing render prerequisite

## Intent

The script itself is expected to be basically valid. The scenario is about
diagnosing runtime prerequisites rather than misreading the script as the root
cause.

## Expected Workflow

1. Attempt the intended render or inspect the render path.
2. Use `get_server_runtime_info` when external prerequisites are suspect.
3. Separate script validity from missing or misconfigured runtime dependencies.
4. Recommend the next corrective action within repository scope.

## Required Surface Elements

- render tool
- `get_server_runtime_info`

## Success

Success means the agent:

- identifies that the render prerequisite is missing or misconfigured
- does not misdiagnose the script as the primary problem
- points to the next runtime check or configuration step

## Evaluation Setup Note

Run this scenario in a session where `td` or `gs` is intentionally unavailable,
or where the corresponding executable path is pointed at an invalid location.

The verified first-pass setup for this repository is to force a broken
Ghostscript path through the MCP server configuration, for example by using the
fixture at `tests/fixtures/workflow_validation_support/runtime_configs/mcp-broken-gs.json`
or an equivalent `mcp_servers.topdrawermcp.env.GS_EXECUTABLE_PATH=/nonexistent/gs`
override when launching the fresh session.

When running through `codex exec`, prefer a direct config override such as:

- `-c 'mcp_servers.topdrawermcp.env.GS_EXECUTABLE_PATH="/nonexistent/gs"'`

This has been verified to affect the fresh-session MCP server, unlike changing
only the parent shell environment before launch.
