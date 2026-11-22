---
name: start-unlocked-steps-standing-go
description: "Standing go (11-09): when a merge unblocks an already-planned step, start it myself without asking"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-09T06:15:51.655Z
---

User 2026-11-09: "in future start unlocked planned steps by yourself" (after I asked whether to start #2444 P3 reclaim and
#548 step 4 part 2 once #2528/#2580 merged).

**Why:** the steps were already planned and on the goal list; asking only delayed them.

**How to apply:** on each merge (gh-live / 2 h watch), grep ledgers (`~/notes/ledger/*/PLAN*.md`, STATUS.md, tasks.json)
AND ~/notes/dash/tasks.json "planned" cards' `after` lists (missed F2 on 11-09 by grepping ledgers only) for steps waiting on that PR; dash cards use keys group/key/owners/prefixes/now/next (not id/state); start them (agent or job, prio below DSpine), add the dash card, tell the user in one line.
Covers PLANNED steps only — new ideas, posting/PRs outside existing standing gos, downloads, and model swaps still need
a go. Respect usage state ([[usage-self-management]]) and the sharing check ([[tf-shared-code-across-families]]).

**11-22 (user): "start by yourself when ressources free".** Approved steps wait in a queue file (current:
~/notes/ledger/rebase-1122/NEXT.md) and start without asking once the GPU queue is light and disk ≥ 50 GB.
