# Contributing to PyConfigre

Everything you need to contribute effectively — setup, branching, issues, PRs, and the automation that keeps it all in sync.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Git Hooks](#git-hooks)
3. [Branch Naming](#branch-naming)
4. [Working with Issues](#working-with-issues)
5. [Opening a PR](#opening-a-pr)
6. [What the Automation Does](#what-the-automation-does)
7. [Release Process](#release-process)
8. [Useful Queries](#useful-queries)
9. [Troubleshooting](#troubleshooting)

---

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (package manager)

### Install
```bash
git clone https://github.com/aditya-barik/PyConfigre.git
cd PyConfigre
```

### Create and Activate Virtual Environment, Install `dev` Dependencies
```bash
uv sync --extra dev
```

### Run Tests
```bash
pytest
```

### Run Linting and Type Checks
```bash
ruff check src/ tests/
mypy src/
```

---
## Git Hooks

Two opt-in local git hooks enforce branch naming conventions at different points:

- **`post-checkout`** — warns immediately when you create a branch with a non-standard name. Cannot block the operation but gives instant feedback.
- **`commit-msg`** — blocks commits on branches with non-standard names. This is the hard enforcement gate.

Both hooks read from `.github/config/pr-labeling.json`, the same source of truth as the CI validation workflow.

### Setup (one-time)

Run the setup script using `uv` — works on Windows, macOS, and Linux:

```bash
uv run python scripts/setup-hooks.py
```

This configures git to use the hooks in `.githooks/` and sets the executable bit on each hook file.

> **Note:** Ensure `git` is on your system PATH (check with `git --version` or `Get-Command git` in PowerShell). Also ensure `uv` is installed — if not, follow the official guide at https://docs.astral.sh/uv/getting-started/installation/. Both are required for the script to work correctly.

### What you will see

On branch creation with a bad branch name (`post-checkout` — warning only):
```
===============================================================================
  ⚠️  BRANCH NAMING WARNING
===============================================================================

  Current Branch Name  :  bad_branch_name
  Expected Branch Name :  <prefix>/issue-N_<slug>
  Valid prefixes       :  fix/, feature/, docs/, refactor/, ci/, test/

===============================================================================
  🔧 Fix now:  git branch -m bad_branch_name <prefix>/issue-N_<slug>
===============================================================================
  💡 TIP: Haven't created a GitHub issue yet? No worries!
     Create one first, then use that issue number in your branch name.
     This keeps your work tracked and makes reviews much smoother.

  ℹ️  Heads up: Commits on this branch will be blocked until you rename it.
  📖 Check out .github/CONTRIBUTING.md for the full scoop on branch naming.
===============================================================================
```

On commit with a bad branch name (`commit-msg` — blocks the commit):
```
===============================================================================
  ❌  COMMIT BLOCKED — BRANCH NAME ISSUE
===============================================================================

  Current Branch Name  :  bad_branch_name
  Expected Branch Name :  <prefix>/issue-N_<slug>
  Valid prefixes       :  fix/, feature/, docs/, refactor/, ci/, test/

===============================================================================
  🔧 Fix now:  git branch -m bad_branch_name <prefix>/issue-N_<slug>
===============================================================================
  💡 TIP: Starting fresh? Create a GitHub issue first, then branch from it.
     This keeps your work organized and code reviews straightforward.

  📖 Check out .github/CONTRIBUTING.md for our branch naming conventions.
===============================================================================
```

Both hooks pass silently on `main`, `dev`, and `HEAD`. The hooks are **opt-in** — they are never enforced automatically on the runner.

---

## Branch Naming

Branch name prefixes drive automatic PR labelling. Use them consistently. If your branch name doesn't match any prefix — for example when working from a fork or a hotfix branch with a non-standard name — the automation falls back to matching the PR title pattern instead.

See `.github/config/pr-labeling.json` for the full mapping. Adding a new convention is a one-line change to that file.

### Branch Name Prefixes (Primary)

| Prefix | Type Label Applied | Example Branch |
|---|---|---|
| `fix/` | `type:bug` | `fix/issue-N_env-parser-crash` |
| `feature/` | `type:feature` | `feature/issue-N_schema-inference` |
| `docs/` | `type:docs` | `docs/issue-N_update-readme` |
| `refactor/` | `type:refactor` | `refactor/issue-N_move-deep-merge` |
| `ci/` | `type:ci` | `ci/issue-N_add-coverage-badge` |
| `test/` | `type:test` | `test/issue-N_loader-edge-cases` |

### PR Title Patterns (Fallback)

Used only when the branch name does not match any prefix above.

| PR Title Must Contain | Type Label Applied | Example PR Title |
|---|---|---|
| `[Fix]` | `type:bug` | `[Fix] Correct double-underscore env parsing` |
| `[Feature]` | `type:feature` | `[Feature] Add schema inference to RawConfigBuilder` |
| `[Docs]` | `type:docs` | `[Docs] Update README with nested config examples` |
| `[Refactor]` | `type:refactor` | `[Refactor] Move _deep_merge to module level` |
| `[CI]` | `type:ci` | `[CI] Add Python 3.14 to test matrix` |
| `[Test]` | `type:test` | `[Test] Add edge cases for TOML loader` |
| `[Release]` | `type:release` | `[Release] vX.Y.Z` |

> **Priority:** Branch prefix is always checked first. PR title pattern is only used as a fallback. If neither matches, no type label is applied — only `status:review` is added.
>
> **Note:** `[Release]` is the only pattern without a corresponding branch prefix — release PRs always originate from the `dev` branch directly.

---

## Working with Issues

### Issue Document Format

Before opening a GitHub issue, create a Markdown file in `planned-issues/` using the template below. This keeps intent, rationale, and scope in version control and makes it easy to review planned work before acting on it.

```markdown
# Issue N — <Short Title>

**Branch:** `<prefix>/issue-N_<slug>`
**Labels:** `type:...` · `area:...`
**Depends on:** *(optional)*

---

## Summary

<!-- One or two sentences describing the problem or goal and why it matters. -->

---

## What to Change/Solve/Update/Evolve

<!-- Bullet list of concrete changes. Include before/after snippets where helpful. -->

---

## Scope of Changes

**Files touched:**
- `path/to/file` *(new file / modified)*

**Acceptance criteria:**
- <!-- Observable, verifiable outcome 1 -->
- <!-- Observable, verifiable outcome 2 -->
```

See `planned-issues/` for real examples.

---

### Creating an Issue

1. Go to **Issues → New issue**
2. Use a descriptive title with a type prefix: `[Fix] Description`, `[Feature] Description`, etc.
3. Apply labels (pick one from each relevant category):

   **Type** (required):
   `type:bug` · `type:feature` · `type:docs` · `type:refactor` · `type:ci` · `type:test` · `type:release`

   **Priority** (recommended):
   `priority:critical` · `priority:high` · `priority:medium` · `priority:low`

   **Status** (set manually at creation; automation updates it when a PR opens):
   `status:backlog` · `status:in-progress` · `status:blocked`

   **Area** (optional, multiple allowed):
   `area:core` · `area:loaders` · `area:tests` · `area:ci-cd` · `area:docs`

4. Assign a **Milestone** — pick the target release (e.g. `vX.Y.Z`) or `Backlog` if not yet scheduled
5. Assign the issue to yourself if you're picking it up

### Label Definitions

| Label | Meaning |
|---|---|
| `type:bug` | Incorrect or broken behaviour |
| `type:feature` | New functionality |
| `type:docs` | Documentation, docstrings, examples |
| `type:refactor` | Code restructure with no behaviour change |
| `type:ci` | Workflows, automation, CI/CD |
| `type:test` | Tests or test infrastructure |
| `type:release` | Release PR merging `dev` into `main` for a versioned release |
| `priority:critical` | Blocks a release |
| `priority:high` | Must be done before the next release |
| `priority:medium` | Should be done in the current milestone |
| `priority:low` | Can be deferred |
| `status:backlog` | Not yet assigned to a milestone or sprint |
| `status:in-progress` | Actively being worked on |
| `status:blocked` | Waiting on a dependency or decision |
| `status:review` | A PR is open — set automatically by automation |
| `status:merged` | PR was merged — set automatically on merge |
| `status:closed` | PR was closed without merging — set automatically |
| `area:core` | ConfigBuilder, exceptions, core API |
| `area:loaders` | File loaders, environment variable loader |
| `area:tests` | Test suite and infrastructure |
| `area:ci-cd` | GitHub Actions, workflows |
| `area:docs` | README, CHANGELOG, examples |

---

## Opening a PR

### Step 1 — Create your branch
```bash
git checkout -b fix/issue-N_your-bug-description
# or feature/, docs/, refactor/, ci/, test/
```

### Step 2 — Make changes and push
```bash
git add .
git commit -m "fix: describe your change"
git push origin fix/issue-N_your-bug-description
```

### Step 3 — Open the PR and link the issue

In the PR description, include one of:
```
Closes #42
Fixes #42
Resolves #42
```

This is required for the automation to sync labels and milestones to the issue and for GitHub to close the issue automatically when the PR merges.

**Recommended PR description format:**
```markdown
## Description
Brief explanation of what changed and why.

## Checklist
- [ ] Tests added or updated
- [ ] CHANGELOG updated
- [ ] Documentation updated (if applicable)

---

Closes #42

```

### Step 4 — Automation handles the rest

Once the PR is open, the `PR and Issue Lifecycle` workflow runs automatically. See [What the Automation Does](#what-the-automation-does) below.

---

## What the Automation Does

All automation is driven by two config files in `.github/config/` and two workflows:

### `sync-labels.yml`

Triggers on: push to `main` when `labels.json` changes, or manual dispatch.

- Reads `.github/config/labels.json`
- Creates any missing labels
- Updates existing labels to match the config (name, colour, description)
- Never deletes labels

To run manually: **Actions → Sync Labels → Run workflow**

### `pr-lifecycle.yml`

Triggers on: every PR event (opened, reopened, synchronize, closed).

**On PR opened / updated:**

1. Reads `labels.json` and verifies all labels exist (creates missing ones)
2. Reads `pr-labeling.json` and detects the type label from the branch name or PR title
3. Applies `status:review` + the detected type label to the PR
4. Syncs those same labels to the linked issue (requires `Closes #N` in PR body)
5. Syncs the milestone between PR and issue — resolves conflicts by posting a comment

**On PR closed or merged:**

1. Removes `status:review` from the PR and linked issue
2. Adds `status:merged` (if merged) or `status:closed` (if closed without merging)

---

## Release Process

1. Merge all PRs for the milestone to `dev`
2. Update `CHANGELOG.md` on `dev` — move `[Unreleased]` entries under the new version heading and add the comparison link at the bottom
3. Open a PR from `dev` → `main` with title `[Release] vX.Y.Z — short description`
4. Close the milestone at https://github.com/aditya-barik/PyConfigre/milestones
5. After merging, Tag and push:
    ```bash
    git tag vX.Y.Z
    git push origin vX.Y.Z
    ```
6. Create a GitHub Release from the tag, paste the CHANGELOG entries as release notes

---

## Useful Queries
```
# All bugs assigned to you
is:issue label:type:bug assignee:@me

# Everything in the current milestone
is:issue milestone:vX.Y.Z

# High priority open issues
is:issue label:priority:high is:open

# Blocked issues
is:issue label:status:blocked

# All open PRs awaiting review
is:pr label:status:review is:open

# Backlog
is:issue milestone:Backlog
```

---

## Troubleshooting

**Workflow didn't run on my PR**
- Confirm the workflow is enabled: Actions → PR and Issue Lifecycle → Enable workflow
- Check that `.github/workflows/pr-lifecycle.yml` exists on `main`

**Labels didn't sync to the linked issue**
- Confirm the PR body contains exactly `Closes #N`, `Fixes #N`, or `Resolves #N`
- Check the Actions tab → PR and Issue Lifecycle → latest run → `label-pr` job logs

**No type label was applied**
- Confirm your branch name starts with a recognised prefix (`fix/`, `feature/`, etc.)
- If not, add `[Fix]`, `[Feature]`, etc. to the PR title as a fallback
- See `.github/config/pr-labeling.json` for all recognised prefixes and patterns

**Milestone conflict comment appeared on my PR**
- Your PR and the linked issue have different milestones assigned
- Decide which is correct, update the other to match
- Push an empty commit to re-trigger the workflow:
  ```bash
    git commit --allow-empty -m "ci: resolve milestone conflict"
    git push
  ```
