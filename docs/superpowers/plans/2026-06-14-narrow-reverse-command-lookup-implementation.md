# Narrow Reverse Command Lookup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a narrow reverse-lookup MCP tool that maps a short query string to a small ranked list of command headings, so agents can move from vague wording into `lookup_command` without going straight to broad manual search.

**Architecture:** Add one focused reverse-lookup core module that builds ranked command candidates from the existing command lookup index, then expose it through one structured MCP tool in `server.py`. Keep the result shape narrow (`query` plus ordered candidate command headings), prefer reviewed/high-value entries in ranking, and update prompt/docs/tests so the new flow becomes `reverse lookup -> lookup_command -> search_manual if still needed`.

**Tech Stack:** Python, FastMCP, pytest, existing command lookup index data

---

## File Structure

- Create: `src/topdrawer_mcp/reverse_lookup.py`
  - One focused reverse-lookup core over existing command index entries.
- Modify: `src/topdrawer_mcp/server.py`
  - Register the new MCP tool and update prompt guidance text.
- Create: `tests/unit/test_reverse_lookup.py`
  - Core ranking and validation tests for the new reverse-lookup module.
- Modify: `tests/unit/test_server.py`
  - Tool registration and server-level behavior tests.
- Modify: `tests/integration/test_inspector_cli.py`
  - Inspector coverage for tool listing/call behavior and prompt text.
- Modify: `README.md`
  - Document the new tool and the intended discovery flow.
- Modify: `tests/fixtures/workflow_validation/ambiguous-goal-polar-or-error-bars/expected.md`
  - Reflect the new preferred discovery flow.
- Modify: `tests/fixtures/workflow_validation/unsupported-direct-function-plot/expected.md`
  - Reflect the new preferred discovery flow.

## Public Surface Target

- Tool name: `reverse_lookup_commands`
- Structured result shape:

```python
class ReverseLookupResult(TypedDict):
    query: str
    commands: list[str]
```

- Input parameters:

```python
def reverse_lookup_commands(query: str, limit: int = 5) -> ReverseLookupResult:
    ...
```

- Behavior:
  - reject empty query
  - default `limit=5`
  - clamp `limit` to `1..20`
  - search all known command entries from `load_command_lookup_index()`
  - prefer reviewed/high-value command entries in ranking
  - return canonical command headings only

### Task 1: Add failing reverse-lookup tests

**Files:**
- Create: `tests/unit/test_reverse_lookup.py`
- Modify: `tests/unit/test_server.py`

- [ ] **Step 1: Write the failing core tests**

```python
from __future__ import annotations

import pytest

from topdrawer_mcp.reverse_lookup import reverse_lookup_command_candidates


def test_reverse_lookup_rejects_empty_query():
    with pytest.raises(ValueError, match="query must be a non-empty string"):
        reverse_lookup_command_candidates("   ")


def test_reverse_lookup_finds_set_polar_first():
    result = reverse_lookup_command_candidates("polar")
    assert result["commands"]
    assert result["commands"][0] == "SET POLAR"


def test_reverse_lookup_returns_join_for_points_and_line():
    result = reverse_lookup_command_candidates("points and line")
    assert "JOIN" in result["commands"]


def test_reverse_lookup_prefers_default_limit_of_five():
    result = reverse_lookup_command_candidates("set")
    assert len(result["commands"]) <= 5


def test_reverse_lookup_honors_explicit_limit():
    result = reverse_lookup_command_candidates("set", limit=2)
    assert len(result["commands"]) <= 2
```

- [ ] **Step 2: Run the new core test file to verify failure**

Run:

```bash
uv run pytest -q tests/unit/test_reverse_lookup.py
```

Expected:

```text
E   ModuleNotFoundError: No module named 'topdrawer_mcp.reverse_lookup'
```

- [ ] **Step 3: Add failing server-level tests**

```python
def test_create_server_registers_reverse_lookup_tool():
    tool_names = {
        tool.name for tool in asyncio.run(server.create_server().list_tools())
    }
    assert "reverse_lookup_commands" in tool_names


def test_reverse_lookup_commands_returns_ranked_candidates():
    result = server.reverse_lookup_commands("polar")
    assert result["query"] == "polar"
    assert result["commands"][0] == "SET POLAR"


def test_discover_topdrawer_command_prompt_mentions_reverse_lookup():
    prompt = asyncio.run(
        server.create_server().get_prompt(
            "discover_topdrawer_command",
            {"query": "polar"},
        )
    )
    message_text = "\n".join(
        block.text
        for message in prompt.messages
        for block in message.content
        if hasattr(block, "text")
    )
    assert "reverse_lookup_commands" in message_text
    assert "lookup_command" in message_text
```

- [ ] **Step 4: Run the targeted server tests to verify failure**

Run:

```bash
uv run pytest -q tests/unit/test_server.py -k "reverse_lookup or discover_topdrawer_command_prompt_mentions_reverse_lookup"
```

Expected:

```text
FAILED ... assert 'reverse_lookup_commands' in tool_names
FAILED ... AttributeError: module 'topdrawer_mcp.server' has no attribute 'reverse_lookup_commands'
```

- [ ] **Step 5: Commit the failing-test checkpoint**

```bash
git add tests/unit/test_reverse_lookup.py tests/unit/test_server.py
git commit -m "test: define reverse command lookup behavior"
```

### Task 2: Implement the reverse-lookup core

**Files:**
- Create: `src/topdrawer_mcp/reverse_lookup.py`
- Test: `tests/unit/test_reverse_lookup.py`

- [ ] **Step 1: Add the reverse-lookup result type and normalization helpers**

```python
from __future__ import annotations

from typing import TypedDict

from topdrawer_mcp.command_lookup import CommandLookupEntry
from topdrawer_mcp.command_lookup import load_command_lookup_index


class ReverseLookupResult(TypedDict):
    query: str
    commands: list[str]


def _normalize_query(value: str) -> str:
    normalized = " ".join(value.casefold().split())
    if not normalized:
        raise ValueError("query must be a non-empty string")
    return normalized


def _query_terms(value: str) -> list[str]:
    return [term for term in _normalize_query(value).split(" ") if term]
```

- [ ] **Step 2: Implement a scored candidate matcher over existing command entries**

```python
def _entry_text_fields(entry: CommandLookupEntry) -> list[str]:
    fields = [
        entry["command"],
        *entry["aliases"],
        entry["title"],
        entry["summary"],
        entry["section"],
    ]
    parent = entry["parent_command"]
    if parent:
        fields.append(parent)
    return [field.casefold() for field in fields if field.strip()]


def _score_entry(entry: CommandLookupEntry, query: str, terms: list[str]) -> int:
    score = 0
    command_text = entry["command"].casefold()
    alias_texts = [alias.casefold() for alias in entry["aliases"]]
    title_text = entry["title"].casefold()
    summary_text = entry["summary"].casefold()
    parent_text = (entry["parent_command"] or "").casefold()
    section_text = entry["section"].casefold()

    if query in command_text:
        score += 100
    if any(query in alias for alias in alias_texts):
        score += 90
    if query in title_text:
        score += 60
    if query in summary_text:
        score += 50

    for term in terms:
        if term in command_text:
            score += 20
        if any(term in alias for alias in alias_texts):
            score += 18
        if term in title_text:
            score += 12
        if term in summary_text:
            score += 10
        if term in parent_text:
            score += 4
        if term in section_text:
            score += 2

    if score > 0 and entry["summary"].strip():
        score += 5

    return score
```

- [ ] **Step 3: Add reviewed/high-value ranking preference and public API**

```python
def reverse_lookup_command_candidates(
    query: str,
    limit: int = 5,
) -> ReverseLookupResult:
    normalized_query = _normalize_query(query)
    clamped_limit = max(1, min(limit, 20))
    terms = _query_terms(query)

    index = load_command_lookup_index()
    scored: list[tuple[int, str]] = []
    for entry in index["entries"]:
        score = _score_entry(entry, normalized_query, terms)
        if entry["summary"].strip():
            score += 3
        if score > 0:
            scored.append((score, entry["command"]))

    scored.sort(key=lambda item: (-item[0], item[1]))

    commands: list[str] = []
    seen: set[str] = set()
    for _, command in scored:
        if command in seen:
            continue
        seen.add(command)
        commands.append(command)
        if len(commands) >= clamped_limit:
            break

    return {"query": normalized_query, "commands": commands}
```

- [ ] **Step 4: Run the reverse-lookup unit tests to verify they pass**

Run:

```bash
uv run pytest -q tests/unit/test_reverse_lookup.py
```

Expected:

```text
.....                                                                    [100%]
```

- [ ] **Step 5: Commit the core implementation**

```bash
git add src/topdrawer_mcp/reverse_lookup.py tests/unit/test_reverse_lookup.py
git commit -m "feat: add narrow reverse command lookup core"
```

### Task 3: Expose the MCP tool and update prompts/docs/tests

**Files:**
- Modify: `src/topdrawer_mcp/server.py`
- Modify: `tests/unit/test_server.py`
- Modify: `tests/integration/test_inspector_cli.py`
- Modify: `README.md`
- Modify: `tests/fixtures/workflow_validation/ambiguous-goal-polar-or-error-bars/expected.md`
- Modify: `tests/fixtures/workflow_validation/unsupported-direct-function-plot/expected.md`

- [ ] **Step 1: Add the server wrapper and register the new tool**

```python
from topdrawer_mcp.reverse_lookup import ReverseLookupResult
from topdrawer_mcp.reverse_lookup import reverse_lookup_command_candidates


def reverse_lookup_commands(query: str, limit: int = 5) -> ReverseLookupResult:
    """Return ranked command-heading candidates for a short query string."""
    return reverse_lookup_command_candidates(query, limit=limit)
```

Register it in `create_server()`:

```python
server.add_tool(reverse_lookup_commands, structured_output=True)
```

- [ ] **Step 2: Update the discovery prompt text to use the new middle layer**

Replace the `discover_topdrawer_command` body with guidance like:

```python
return (
    "You are choosing the best Topdrawer command for a user request.\n"
    f"Query: {query.strip()}\n"
    f"Context: {context_text}\n\n"
    "Suggested workflow:\n"
    "1. Call `reverse_lookup_commands` with the key word or short phrase.\n"
    "2. Inspect the returned candidate command headings.\n"
    "3. Call `lookup_command` for the best candidates.\n"
    "4. Call `search_manual` only if the candidate lookup still does not provide enough context.\n"
    "5. Summarize the best command path and any remaining ambiguity.\n"
)
```

- [ ] **Step 3: Add integration and server tests for tool exposure and behavior**

Add inspector coverage like:

```python
def test_inspector_lists_reverse_lookup_tool(write_manual):
    payload = run_inspector("tools/list")
    names = {tool["name"] for tool in payload["tools"]}
    assert "reverse_lookup_commands" in names


def test_inspector_calls_reverse_lookup_tool(write_manual):
    payload = run_inspector(
        "tools/call",
        {"name": "reverse_lookup_commands", "arguments": {"query": "polar"}},
    )
    structured = payload["structuredContent"]
    assert structured["commands"][0] == "SET POLAR"
```

- [ ] **Step 4: Update README and workflow-validation expectations**

Add README tool documentation:

```md
### `reverse_lookup_commands`

Input:

```json
{
  "query": "polar",
  "limit": 5
}
```

Returns a small ranked list of command headings that should usually be checked
next with `lookup_command`.
```

Update the workflow-validation expected files so the preferred discovery flow
becomes:

```text
reverse_lookup_commands -> lookup_command -> search_manual if needed
```

- [ ] **Step 5: Run the full targeted verification set**

Run:

```bash
uv run pytest -q tests/unit/test_reverse_lookup.py tests/unit/test_server.py tests/integration/test_inspector_cli.py
```

Expected:

```text
... all selected tests pass ...
```

- [ ] **Step 6: Commit the public-surface integration**

```bash
git add src/topdrawer_mcp/server.py tests/unit/test_server.py tests/integration/test_inspector_cli.py README.md tests/fixtures/workflow_validation/ambiguous-goal-polar-or-error-bars/expected.md tests/fixtures/workflow_validation/unsupported-direct-function-plot/expected.md
git commit -m "feat: add reverse command lookup tool"
```

## Self-Review Checklist

- Spec coverage:
  - narrow reverse-lookup tool: covered in Tasks 1-3
  - all known commands with reviewed-preferred ranking: covered in Task 2
  - candidate-only result shape: covered in Tasks 2-3
  - default limit `5` with caller override: covered in Tasks 1-3
  - updated discovery flow in prompts/docs: covered in Task 3
- Placeholder scan:
  - no `TODO`, `TBD`, or deferred implementation placeholders remain
- Type consistency:
  - `ReverseLookupResult`, `reverse_lookup_command_candidates`, and
    `reverse_lookup_commands` names are consistent across tasks

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-14-narrow-reverse-command-lookup-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
