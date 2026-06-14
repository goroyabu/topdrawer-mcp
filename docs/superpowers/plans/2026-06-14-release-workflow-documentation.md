# Release Workflow Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document the repository's release-preparation flow and land it in the same pull request as the `1.0.0` version bump.

**Architecture:** Keep the implementation narrow. Add one focused spec, one focused plan, and one short `Release Flow` section in `docs/development-workflow.md`. Reuse the existing release branch and verification work already completed for the `1.0.0` bump.

**Tech Stack:** Markdown documentation, git, uv

---

## File Structure

- Create: `docs/superpowers/specs/2026-06-14-release-workflow-documentation-design.md`
  - Records why release workflow documentation is being added and what it must cover.
- Create: `docs/superpowers/plans/2026-06-14-release-workflow-documentation.md`
  - Records the bounded implementation approach for the documentation update.
- Modify: `docs/development-workflow.md`
  - Add the reusable release flow steps.

### Task 1: Record the release-workflow design

**Files:**
- Create: `docs/superpowers/specs/2026-06-14-release-workflow-documentation-design.md`

- [ ] **Step 1: Write the focused spec**

Capture:

- why the repository needs an explicit release flow
- the minimum recurring steps that must be documented
- the decision that `uv.lock` follows `pyproject.toml` when the editable package
  entry records the project version

- [ ] **Step 2: Review the spec for scope**

Check that the spec stays focused on repository release documentation and does
not drift into automation or broad process redesign.

### Task 2: Record the implementation approach

**Files:**
- Create: `docs/superpowers/plans/2026-06-14-release-workflow-documentation.md`

- [ ] **Step 1: Write the focused plan**

Capture:

- the exact files touched
- the intended `Release Flow` section in `docs/development-workflow.md`
- the expectation that this documentation lands with the `1.0.0` version bump

- [ ] **Step 2: Review the plan for consistency**

Check that the plan matches the spec and stays limited to documentation changes.

### Task 3: Update the workflow document

**Files:**
- Modify: `docs/development-workflow.md`

- [ ] **Step 1: Add the `Release Flow` section**

Document the normal repository release order:

1. confirm release readiness on `main`
2. create a release branch
3. bump version in `pyproject.toml`
4. refresh `uv.lock` when needed for the editable project entry
5. run verification
6. open and merge the release-preparation pull request
7. create tag and GitHub Release from merged `main`
8. sync local branches afterward

- [ ] **Step 2: Keep the section concise**

Avoid duplicating existing contribution flow text. The new section should be a
small release-specific addendum.

### Task 4: Verify and prepare the branch

**Files:**
- Modify: `docs/development-workflow.md`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

- [ ] **Step 1: Run formatting-integrity verification**

Run:

```bash
git diff --check
```

Expected:

```text
[no output]
```

- [ ] **Step 2: Re-run repository verification for the release-preparation branch**

Run:

```bash
env UV_CACHE_DIR=.uv-cache uv run pytest -q
```

Expected:

```text
... passed ...
```

- [ ] **Step 3: Commit the release-preparation branch**

```bash
git add docs/development-workflow.md docs/superpowers/specs/2026-06-14-release-workflow-documentation-design.md docs/superpowers/plans/2026-06-14-release-workflow-documentation.md pyproject.toml uv.lock
git commit -m "docs: add release workflow guidance"
```
