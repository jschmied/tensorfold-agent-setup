---
name: tf-pr-skill-handover
description: TF PR work goes through the tf-pr skill; agents must end POSTED/READY/BLOCKED, pr-ready.py before every push/post
metadata:
  type: feedback
---
Every TensorFold PR agent brief includes the tf-pr skill's finish-condition block (`~/.claude/skills/tf-pr/SKILL.md` §3). Run `python3 ~/notes/watch/pr-ready.py --pr N` before any push, body PATCH or reply. When an agent returns READY, or "waiting" with its gates done, the main session pushes and posts at once.

**Why:** on 2026-11-11 the user asked "we get asked many times for changes, what can we do proactive?" and then "build both". Two weeks of review held 58 ask comments on 34 PRs, mostly the same few asks: rebase, a stale body head, refusal ordering, seeded/resume/concurrency, equality against main, a planted control. Separately, agents finished and never pushed: #2705 sat for 9.5 h and #1503 for 20 h, twice.

**How to apply:** ship the evidence defaults in the first post. At the 2 h watch, any open ask older than 2 h with no running job for it is a stall; finish it yourself. Related: [[open-asks-ledger]], [[pr-replies-first]], [[watch-read-every-comment]].
