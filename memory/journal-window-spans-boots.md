---
name: journal-window-spans-boots
description: journalctl --since "-N min" spans server restarts, so a pre-change boot's log lines get counted as the post-change result; scope to the boot's start timestamp
metadata:
  type: feedback
---

`journalctl -u <unit> --since "-30 min"` is a **rolling window, not a boot**. When a job restarts
the server to change one variable, that window still contains the previous boot's lines.

**2026-09-20:** a verification job counted the `could be identified as the draft` warning this way
and reported "2 occurrences — vllm#55390 does not fix it". Scoped per boot the truth was the
opposite:

| boot | warnings |
|---|---|
| 11:32 pre-patch | 2 |
| 11:58 with #55390 | **0** |
| 12:13 with #55390 | **0** |

The patch worked; the window had caught the pre-patch boot. I reported the wrong verdict to the
user before catching it.

**How to apply:** capture `START=$(date '+%Y-%m-%d %H:%M:%S')` immediately before
`systemctl start`, then grep with `--since "$START"`. `--boot` does not help here, because a
service restart is not a reboot. Same rule for any per-arm counter read out of the journal.

**Why:** an A/B whose two arms share log lines is not an A/B. Related:
[[no-cause-without-counterfactual]], [[ds41-ab-within-arm-drift]], [[spec-ab-clip-per-prompt]].
