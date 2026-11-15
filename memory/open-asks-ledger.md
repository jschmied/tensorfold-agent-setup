---
name: open-asks-ledger
description: "Reviewer asks are tracked by ~/notes/watch/open-asks.py (in hourly.py), not in my context; mark handled by comment id"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-10T18:44:19.442Z
---

Every non-self comment after our last reply on an open thread involving jschmied stays listed by
`python3 ~/notes/watch/open-asks.py` until marked: `NOTE="..." python3 ~/notes/watch/open-asks.py done <comment_id>...`.
hourly.py prints it (OPEN-ASKS N). Mark only after reading the comment in full and either answering it or naming where it is tracked.

**Why:** 11-10: #2705 (asks 10:17, answered 19:5x) and #2729 (asks 10:17, open at 20:00) were delivered by gh-live
during a burst of ~15 ashhart comments and then lost: in-context tracking, plus an agent that finished work but never pushed/posted.
User: "why do we keep loosing mentions".

**How to apply:** at every watch, OPEN-ASKS must be 0 or each line owned by a running agent/user decision. Agents answering
asks mark their comment ids done themselves. Agent briefs: never end the turn while a job is pending — wait in a foreground loop.
Related: [[watch-read-every-comment]], [[pr-replies-first]].
