---
name: usage-limit-99
description: 7-day usage limit is 99 % (2026-10-29); work stops at 98 %, the last 1 % is reserved for the scheduled watch and PR replies
metadata:
  type: feedback
---
On 2026-10-29 the user set the 7-day limit to 99 %, with the last 1 % reserved for the scheduled watch job and PR (reviewer) replies. Their words: "neues Limit 99%, 1% für scheduled job and PR antworten".

**How to apply:**
- Ordinary work (builds, cloud verifications, new tasks) runs until the 7-day usage reaches **98 %**. Then finish what is in flight and start nothing new.
- From 98 % to 99 %: only the watch runs and replies to reviewer asks on our PRs.
- At 99 %: stop. This replaces the watch prompt's older ≥95 % HARD STOP and the earlier 98 % raise.
- The mac-agent stop message is sent at 98 %.
- **2026-10-30:** at 8 % weekly with "throttle" projection 134 %, user: "we are at 8%, there is plenty headroom". Don't hold back work or agents on the projection alone; report it in the watch line only.
