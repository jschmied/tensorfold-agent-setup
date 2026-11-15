---
name: usage-no-throttle-by-projection
description: User 11-09 - don't throttle or warn on projected usage; only absolute d7 >= 90 % matters
metadata:
  type: feedback
---

Don't throttle agents or flag "careful" because of the projected weekly usage. At 42 % (projection 94.6 %) the user
said: "dont considder throtteling we are at 42 % only, rules are to tight".

**Why:** the projection bands kept slowing work and adding usage lines nobody needed.

**How to apply:** run agents in parallel freely and leave usage out of status updates. Mention it once at d7 >= 90 %.
At 98 % switch to watch + PR replies only ([[usage-limit-99]]).
