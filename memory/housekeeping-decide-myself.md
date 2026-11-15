---
name: housekeeping-decide-myself
description: "Worktree/disk housekeeping on Spark and Mac — decide from our goals myself, don't ask the user line by line (11-14)"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-14T11:59:28.868Z
---

User 2026-11-14: "assess itself whats worth to keep, you know our goals" — after I relayed mac-agent's per-worktree keep/remove list.

**Why:** the user doesn't want to adjudicate every worktree; the goals (#2251 unification, #2460 building blocks, #2444 KV roadmap, Mac capacity/speed, open PRs) decide it.

**How to apply:** keep open-PR and live-task trees; push unposted work that still serves a goal to the fork before removing its tree; save scratch diffs/source to ~/notes/attic/; remove merged/closed trees. Never rm -rf, never --force, never delete branches. Check tool users first ([[worktree-cleanup-check-users]]). Report a summary after, don't ask before. mac-agent has the same standing rule (chat #477).
