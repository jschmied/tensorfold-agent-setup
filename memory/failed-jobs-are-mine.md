---
name: failed-jobs-are-mine
description: Failed/blocked dispatcher jobs are my job to triage and fix, never an item for the user's attention
metadata:
  type: feedback
---
2026-11-08, user on the dashboard: "failed queue jobs are handled by you, not my attention".
**Why:** the user's attention is for decisions (go/no-go, posting, direction), not job plumbing.
**How to apply:** user-facing lists ("needs your go" on [[spark-dash]], status replies) show only decisions. Every FAIL/QUIET/
TIMEOUT/blocked job: the owning agent fixes it; if its agent is gone, I triage it myself (see [[analyze-failures-early]])
and only mention it when it changes a result or needs a decision.
