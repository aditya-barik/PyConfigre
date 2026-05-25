# GitHub Configuration Files

All configuration files for PyConfigre's GitHub automation live here.
One location, one source of truth. Update here — everything else follows.

---

## Files

### `labels.json`

Defines every label used across the repository: name, colour, and description.

**Read by:** `sync-labels.yml` (creates/updates labels on push or manual trigger) and
`pr-lifecycle.yml` (verifies labels exist before applying them on each PR event).

**To add or change a label:**
1. Edit this file
2. Push to `main` — `sync-labels.yml` runs automatically and syncs to GitHub
3. Or trigger `sync-labels.yml` manually from the Actions tab

**Format:**
```json
{
  "labels": [
    {
      "name": "type:bug",
      "color": "B01726",
      "description": "Something isn't working / Incorrect behavior"
    }
  ]
}
```

---

### `pr-labeling.json`

Maps branch name prefixes and PR title patterns to type labels.
Controls how `pr-lifecycle.yml` automatically labels PRs when they are opened.

**Read by:** `pr-lifecycle.yml` — the `Detect Type Label` step.

**To add a new branch convention:**
1. Add one entry to `branch_name_prefixes` — that's it, no workflow changes needed
2. Optionally add a matching entry to `pr_title_patterns` for PRs opened from forks
   or branches that don't follow the naming convention

**Priority:** Branch name prefix is checked first. PR title pattern is the fallback.

**Format:**
```json
{
  "branch_name_prefixes": [
    { "prefix": "fix/", "label": "type:bug" }
  ],
  "pr_title_patterns": [
    { "pattern": "[Fix]", "label": "type:bug" }
  ]
}
```

---

## Adding a New Configuration File

When a new automation needs configuration:

1. Create the JSON file here with a clear, kebab-case name (e.g., `release-policy.json`)
2. Add an entry to this README describing it
3. Reference it from the relevant workflow using `fs.readFileSync('.github/config/<file>', 'utf8')`
4. Commit the config file, workflow change, and README update together
