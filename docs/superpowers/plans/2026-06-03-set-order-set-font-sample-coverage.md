# SET ORDER And SET FONT Sample Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `SET ORDER` and `SET FONT` resolvable through `lookup_command` using narrow reviewed guidance derived from existing manual text plus sample-informed notes.

**Architecture:** Keep the runtime MCP surface unchanged and extend only the tracked command lookup target list plus the reviewed guidance data that is merged into the generated lookup index at runtime. Validate the behavior through unit tests at both command-lookup and server layers.

**Tech Stack:** Python, pytest, tracked JSON lookup metadata

---

### Task 1: Add failing lookup tests

**Files:**
- Modify: `tests/unit/test_command_lookup.py`
- Modify: `tests/unit/test_server.py`

- [ ] Add tests asserting the default runtime lookup payload includes `SET ORDER` and `SET FONT`.
- [ ] Add server-level tests asserting `lookup_command("SET ORDER")` and `lookup_command("SET FONT")` resolve as `set-subcommand` entries.
- [ ] Run the targeted tests and confirm they fail before changing lookup data.

### Task 2: Extend tracked lookup target data

**Files:**
- Modify: `data/lookup/command-lookup-targets.json`

- [ ] Add `SET FONT` with section `15.64.28`.
- [ ] Add `SET ORDER` with section `15.64.39`.
- [ ] Keep the naming and kind aligned with the existing `SET ...` targets.

### Task 3: Add reviewed guidance entries

**Files:**
- Modify: `data/lookup/command-lookup-reviewed.json`

- [ ] Add a thin reviewed entry for `SET ORDER` focused on column interpretation, error-bar patterns, symbol-column patterns, and `DUMMY` column skipping.
- [ ] Add a thin reviewed entry for `SET FONT` focused on later text/annotation appearance and common `DUPLEX` use in manual samples.
- [ ] Keep both entries concise and valid without placeholder detail.

### Task 4: Verify runtime lookup behavior

**Files:**
- Reuse: `tests/unit/test_command_lookup.py`
- Reuse: `tests/unit/test_server.py`

- [ ] Run targeted command lookup and server unit tests and confirm they pass.
- [ ] Run the full Python unit suite and confirm it stays green.

### Task 5: Final review

**Files:**
- Review: `data/lookup/command-lookup-targets.json`
- Review: `data/lookup/command-lookup-reviewed.json`
- Review: `docs/superpowers/specs/2026-06-03-set-order-set-font-sample-coverage-design.md`

- [ ] Confirm that only `SET ORDER` and `SET FONT` were implemented from the uncovered sample-scoped set.
- [ ] Confirm that manual sample metadata and tool surface were left unchanged.
