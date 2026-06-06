# Script Command Scan Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Narrow the scan tools so they primarily return recognized script command occurrences for downstream command lookup.

**Architecture:** Keep the existing command-matching logic, but remove the scanner's lightweight diagnostics and count summary from the v1 tool contract. Preserve the file-vs-inline entry points and keep the output centered on matched command occurrences only.

**Tech Stack:** Python 3.11+, pytest, FastMCP tool wrappers

---

### Task 1: Lock the simplified scan contract in tests

**Files:**
- Modify: `tests/unit/test_script_scan.py`
- Modify: `tests/unit/test_server.py`

- [ ] **Step 1: Write the failing tests for scan-only command discovery**

```python
def test_scan_topdrawer_script_detects_known_commands():
    result = scan_topdrawer_script_text(
        "\n".join(
            [
                "set window x 0 13 y 0 10",
                "set limits x 0 to 5 y 0 to 6",
                "plot axis",
                'title top "Example"',
                'case "GGGGGGG"',
                "plot",
            ]
        )
        + "\n"
    )

    assert result == {
        "commands": [
            {
                "line": 1,
                "raw": "set window x 0 13 y 0 10",
                "normalized": "SET WINDOW",
                "kind": "set-subcommand",
            },
            {
                "line": 2,
                "raw": "set limits x 0 to 5 y 0 to 6",
                "normalized": "SET LIMITS",
                "kind": "set-subcommand",
            },
            {
                "line": 3,
                "raw": "plot axis",
                "normalized": "PLOT",
                "kind": "command",
            },
            {
                "line": 4,
                "raw": 'title top "Example"',
                "normalized": "TITLE",
                "kind": "command",
            },
            {
                "line": 5,
                "raw": 'case "GGGGGGG"',
                "normalized": "CASE",
                "kind": "modifier",
            },
            {
                "line": 6,
                "raw": "plot",
                "normalized": "PLOT",
                "kind": "command",
            },
        ]
    }
```

- [ ] **Step 2: Run the targeted tests to verify they fail for the expected reason**

Run: `uv run --extra test pytest tests/unit/test_script_scan.py tests/unit/test_server.py -q`
Expected: FAIL because the current scan result still includes `summary` and `checks`.

- [ ] **Step 3: Update server-level expectations to the simplified output**

```python
def test_scan_topdrawer_script_uses_script_scan_helper(monkeypatch: pytest.MonkeyPatch):
    expected = {"commands": []}
    monkeypatch.setattr(server, "scan_topdrawer_script_text", lambda script: expected)
    assert server.scan_topdrawer_script("plot\n") == expected
```

- [ ] **Step 4: Re-run the targeted tests after implementation**

Run: `uv run --extra test pytest tests/unit/test_script_scan.py tests/unit/test_server.py -q`
Expected: PASS

### Task 2: Simplify the scan implementation

**Files:**
- Modify: `src/topdrawer_mcp/script_scan.py`

- [ ] **Step 1: Remove scan summary/check result types from the public contract**

```python
class ScriptScanResult(TypedDict):
    """Structured scanner result for one Topdrawer script."""

    commands: list[ScannedCommand]
```

- [ ] **Step 2: Return only recognized commands from text scanning**

```python
def scan_topdrawer_script_text(script: str) -> ScriptScanResult:
    if not script.strip():
        raise ValueError("script must be a non-empty string")

    matchers = _command_matchers()
    commands: list[ScannedCommand] = []

    for line_number, raw_line in enumerate(script.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or _is_comment_line(stripped):
            continue

        matched = _match_command(stripped, matchers)
        if matched is None:
            continue

        commands.append(
            {
                "line": line_number,
                "raw": stripped,
                "normalized": matched["normalized"],
                "kind": matched["kind"],
            }
        )

    return {"commands": commands}
```

- [ ] **Step 3: Remove now-unused helper logic for counts and lightweight checks**

```python
# Delete:
# - ScriptScanSummary
# - ScriptScanCheck
# - _case_adjacency_checks(...)
# - _unknown_set_subcommand_checks(...)
```

- [ ] **Step 4: Run focused scan tests**

Run: `uv run --extra test pytest tests/unit/test_script_scan.py -q`
Expected: PASS

### Task 3: Align user-facing docs with the simplified scan behavior

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update scan tool descriptions to describe command discovery only**

```markdown
Returns a structured first-pass scan of inline Topdrawer script text:

- recognized covered commands with line numbers
- normalized command names and command kinds
```

- [ ] **Step 2: Remove wording that promises lightweight rule checks or unknown `SET` warnings**

```markdown
Returns the same command-discovery scan as `scan_topdrawer_script`, but reads
the script from an existing file path.
```

- [ ] **Step 3: Run the full relevant verification suite**

Run: `uv run --extra test pytest`
Expected: PASS
