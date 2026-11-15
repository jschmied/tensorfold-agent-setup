---
name: watch-tagged-check
description: hourly.py prints TAGGED lines for unanswered comments on threads that involve us; answer them (user 2026-11-04)
metadata:
  type: feedback
---
`~/notes/watch/hourly.py` has a TAGGED block. It searches `involves:jschmied` updated since the last run and prints every comment, inline review comment or review by someone else after our own last word. On our own threads it prints all of them; on other people's threads, only those that contain `@jschmied`.

**Why:** the user asked to "add check if we are tagged to regular watch job" (2026-11-04). The static NUMS list missed new PRs (#2113, #2115, #2127, #2164), and the notification feed missed tags.

**How to apply:** at every watch, triage the TAGGED lines.
- Replying to tags on our PRs and RFCs is covered by the standing go (re-read the thread first, see [[posting-check-thread-state-first]]).
- A plain "thanks, it's ours now" needs no reply.
