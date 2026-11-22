---
name: watch-read-every-comment
description: The watch must list every non-self comment on every open PR of ours; never tail/grep its output. Reviewer asks sat 11 h unseen on 2026-11-06
metadata:
  type: feedback
---
Each watch: for every open PR of ours, read every comment since the last watch in full, and fetch the whole body of each; `| tail -8` on hourly.py hid asks.

**Why:** user 2026-11-06: "many merges and comments in last 8h, did you check all?" I had not. Asks unseen for up to 11 h: #1492 rebase+CHANGELOG (11-05 21:57Z), #2282 CHANGELOG + discrete-card cold load, #2283 four asks, #2011 refusals + 27B token check, #2215 body + CHANGELOG. I told the user "no new comments" and "nobody has reviewed them yet", both false.

**How to apply:** never claim "no comments" from a filtered watch. Loop `gh pr list --author jschmied --state open` → `issues/N/comments?since=` for each. Related: [[tf-project-rules-1029]].

**Also merged PRs (11-06):** ashhart asked a follow-up on merged #2232, and `gh pr list --state open` can't see that. A spot check over a hand-picked PR list missed #1850 for 1 h 40. Read the watch's TAGGED lines in full, and spot checks use the same whole list as the watch.

**11-16: issue/PR BODIES count too.** #3491 (ashhart's issue asking us for the Kolibri drafter PR) sat 9 h unseen:
open-asks.py and gh-live only saw comments. open-asks.py now lists an issue/PR opened by someone else whose body
says @jschmied and that we haven't commented on yet, as id `body-<number>` (mark with `open-asks.py done body-N`).
