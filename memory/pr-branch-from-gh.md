---
name: pr-branch-from-gh
description: "Take a PR's branch from `gh pr view --json headRefName`, never from a local worktree's branch name; one worktree per PR"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-08T20:09:58.081Z
---

2026-10-08: rebasing vllm#58835 I fetched `pr/ple-cold-fill-rb` (the local worktree's branch) — the PR's head is
`pr/ple-cold-fill`. The fetch failed before the `&&`-chained `reset --hard` ran, so nothing was lost, but a reset on
the wrong branch would have discarded that worktree's work.

**Why:** local branch names drift (rebase copies, "-rb", "-merge"); the PR's head is the only truth.
**How to apply:** `gh pr view N --json headRefName,headRefOid`; create a fresh worktree from the fork's head for each
PR (`git worktree add -B <head> <dir> FETCH_HEAD`); never `reset --hard` an existing worktree to update it. For vLLM
PRs with conflicts, merge main (no force push), sign off (`-s`), and note that local venvs cannot import current main —
verification is compile + static import check, CI runs the suite. Related: [[verify-before-push]].
