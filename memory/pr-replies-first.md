---
name: pr-replies-first
description: Standing order 2026-11-06 — work needed for a PR or issue reply goes ahead of all other work, including in the GPU queue
metadata:
  type: feedback
---

PR and issue replies come before other work, and so do the jobs a reply depends on.

**Why:** user, 2026-11-06: "standing order: priorize pr/issue replies before other work", after #2011's contract sat behind statewalk A/B jobs.

**How to apply:** jobs that a pending reply waits on get prio 20+ in the dispatcher (README: blocking jobs 20+), ahead of ledger, HY and A/B work. Park waiting timing jobs if they'd drain the job's lane. Agents' briefs say so. Posting rules are unchanged: reviewer asks are the standing go, anything else still needs the user's go. Related: [[watch-read-every-comment]], [[gb10-job-dispatcher]].
