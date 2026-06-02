# Contributor And Workflow Docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split development workflow documentation cleanly across `docs/development-workflow.md`, `CONTRIBUTING.md`, and `AGENTS.md`.

**Architecture:** Add a workflow source-of-truth document, align the contributor guide to reference it, trim `AGENTS.md` down to agent-facing technical guidance, and add simple GitHub templates that reinforce the documented workflow. Keep implementation limited to documentation and template files and avoid changing runtime behavior.

**Tech Stack:** Markdown, git workflow conventions, existing repository docs

---

### Task 1: Capture the documentation-split design record

**Files:**
- Create: `docs/superpowers/specs/2026-06-02-contributing-guide-design.md`

- [ ] **Step 1: Write the design record**

Write a design note that states:

```markdown
# Contributor And Workflow Docs Design

## Goal
Clarify the split between workflow policy, contributor steps, and agent guidance.
```

- [ ] **Step 2: Verify the design record exists**

Run: `sed -n '1,120p' docs/superpowers/specs/2026-06-02-contributing-guide-design.md`
Expected: the file prints a goal, scope, non-goals, and design summary.

### Task 2: Add the workflow source-of-truth document

**Files:**
- Create: `docs/development-workflow.md`

- [ ] **Step 1: Draft the workflow policy document**

Create a Markdown document with sections for:

```markdown
# Development Workflow

## Source of Truth
## Issue Policy
## Superpowers Documentation Policy
## Minor Change Exception
## Contribution Flow
## Issue Close Policy
## Documentation Check Requirements
## Record of Change Intent
```

- [ ] **Step 2: Align the workflow policy with the agreed repository rules**

Ensure the document states that:

```text
- issues are for concrete problems that need correction
- non-trivial changes require specs and plans
- typo/comment/link/formatting-only edits are the only minor-change exception
- commit subjects follow Conventional Commits
- issues close when the change merges to main after verification and doc updates
```

- [ ] **Step 3: Verify the rendered content**

Run: `sed -n '1,260p' docs/development-workflow.md`
Expected: the document reads as the workflow source of truth rather than a contributor checklist.

### Task 3: Add and align the contributor guide

**Files:**
- Create: `CONTRIBUTING.md`
- Reference: `README.md`
- Reference: `AGENTS.md`
- Reference: `docs/development-workflow.md`
- Reference: `docs/source-policy.md`

- [ ] **Step 1: Draft the contributor guide**

Create a Markdown document with sections for:

```markdown
# Contributing to topdrawer-mcp

## Repository Scope
## Before You Start
## Planning Changes
## Development Workflow
## Testing and Verification
## Commits
## Pull Requests
## Releases
## Related Documents
```

- [ ] **Step 2: Align the guide with existing repository rules**

Ensure the document states that contributors should:

```text
- keep the repository focused on the minimal MCP/manual-search/render scope
- work on topic branches instead of `main`
- verify relevant tests before merging
- use Conventional Commits
- treat docs/development-workflow.md as the workflow source of truth
```

- [ ] **Step 3: Verify the rendered content**

Run: `sed -n '1,240p' CONTRIBUTING.md`
Expected: the guide reads as a coherent human-facing contribution document.

### Task 4: Reduce AGENTS.md to agent-facing guidance

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Remove human-oriented workflow duplication**

Trim or move sections so that `AGENTS.md` keeps:

```text
- repository scope boundaries
- canonical source policy boundaries
- documentation consistency expectations relevant to agent judgment
- packaging/verification/change-discipline guidance relevant to implementation
- a short pointer to docs/development-workflow.md
```

- [ ] **Step 2: Verify the reduced guide**

Run: `sed -n '1,220p' AGENTS.md`
Expected: the file reads as agent guidance, not a mixed contributor handbook.

### Task 5: Add simple GitHub templates

**Files:**
- Create: `.github/ISSUE_TEMPLATE/issue.md`
- Create: `.github/pull_request_template.md`

- [ ] **Step 1: Add a simple issue template**

Create a Markdown issue template with sections for:

```markdown
## Summary
## Current Behavior
## Expected Behavior
## Evidence
## Notes
```

- [ ] **Step 2: Add a simple pull request template**

Create a Markdown pull request template with sections for:

```markdown
## Summary
## Verification
## Related
```

- [ ] **Step 3: Verify the templates**

Run: `sed -n '1,200p' .github/ISSUE_TEMPLATE/issue.md && printf '\n---\n' && sed -n '1,200p' .github/pull_request_template.md`
Expected: both templates are present and read as simple workflow prompts.

### Task 6: Final verification

**Files:**
- Verify: `AGENTS.md`
- Verify: `CONTRIBUTING.md`
- Verify: `docs/development-workflow.md`
- Verify: `.github/ISSUE_TEMPLATE/issue.md`
- Verify: `.github/pull_request_template.md`
- Verify: `docs/superpowers/specs/2026-06-02-contributing-guide-design.md`
- Verify: `docs/superpowers/plans/2026-06-02-contributing-guide.md`

- [ ] **Step 1: Check git status**

Run: `git status --short`
Expected: only the intended documentation updates appear.

- [ ] **Step 2: Run a focused documentation sanity check**

Run: `python3 - <<'PY'
from pathlib import Path
for path in [
    Path("AGENTS.md"),
    Path("CONTRIBUTING.md"),
    Path("docs/development-workflow.md"),
    Path(".github/ISSUE_TEMPLATE/issue.md"),
    Path(".github/pull_request_template.md"),
    Path("docs/superpowers/specs/2026-06-02-contributing-guide-design.md"),
    Path("docs/superpowers/plans/2026-06-02-contributing-guide.md"),
]:
    assert path.exists(), path
    text = path.read_text(encoding="utf-8")
    assert text.strip(), path
print("docs-ok")
PY`
Expected: `docs-ok`
