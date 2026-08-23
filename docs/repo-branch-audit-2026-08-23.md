# Repository branch audit — 2026-08-23

Audit scope: all 25 branches present in `nauda199x/lumi-hanoi`, pull-request history and current `main`.

## Result

- Branches tied to merged PRs are considered incorporated into `main`; they should not be re-merged just because squash/rebase history makes them appear divergent.
- PR #12 (`codex/create-v6-branch-and-pull-request`) is superseded by merged PR #13 and was closed during this audit.
- PR #16 (`codex/implement-github-issue-#15-for-v5.2`) is superseded by merged PR #32 and was closed during this audit.
- PR #17 was already closed as superseded by PR #32.
- `media-assets-v4-codex` contains a one-shot branch-specific importer workflow/script and is obsolete because the verified V4 media package was integrated through merged PR #8. It must not be merged into current `main`.
- `media-assets-v4` contains an obsolete staging/import script only; current verified assets are already in `main`.
- `v8-1-prestige-media-library` has no commits ahead of current `main`.
- `v8-1b-prestige-unit-layouts` is an old staging branch for the 22 Prestige WebPs that are already present in `main` through merged PR #25 and later catalogue PRs; do not re-merge it.
- `feat/floor-plan-hub-9-towers` was merged through PR #32. Its continued divergence is expected after squash merge and is not outstanding work.

## Current branch policy

New work should branch from current `main`, use one focused PR, pass `.github/workflows/repo-qa.yml`, then merge. Old Codex/staging branches should be treated as historical unless a fresh comparison proves they contain unique current-value work.
