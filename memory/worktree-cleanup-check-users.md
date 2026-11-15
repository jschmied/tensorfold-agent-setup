---
name: worktree-cleanup-check-users
description: "Before removing TF worktrees, grep job scripts, ledger tools and running processes for the path — a merged PR's worktree can still be a tool dependency"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-12T19:10:36.995Z
---

On 11-12 I removed 113 "clean, idle, merged-PR" worktrees. One was ~/git/tf-conformance (#2467 merged), whose
`tools/conformance.py` a running agent's conf.py still used: the q3r conformance run lost its kit mid-run at ~18:15
and had to switch to main's copy (5 of 6 #2620 cells ran on the old kit, said so in the PR body).

**Why:** my check only grepped dispatcher q/ and run/ JSON. Jobs call `.sh` scripts and ledger tools (`~/notes/ledger/*/tools`,
`*/jobs/*.sh`) that name worktree paths, and processes may have a cwd inside them.

**How to apply:** before `git worktree remove`, also `grep -rl <dir> ~/notes/ledger/*/tools ~/notes/ledger/*/jobs ~/notes/jobs/*.sh`
and check `ls -l /proc/*/cwd` for the path; skip any hit. Prefer removing only while no agent is running, or ask the
running agents first. Related: [[failed-jobs-are-mine]], [[disk-swap-standing-go]].
