---
name: gh-live-monitor
description: Live GitHub feed for TF threads: Monitor on ~/notes/watch/gh-live.py (notifications API, every 5 min; user: "5 min is enough"), re-arm on expiry
metadata:
  type: project
---
2026-11-08, user asked for faster mentions/asks. Webhooks impossible (no admin on ashhart/TensorFold, no public endpoint).
Instead: `Monitor python3 -u ~/notes/watch/gh-live.py 2>&1` (timeout 1800000, re-arm every expiry, like the agent-chat one).
It polls /notifications (every 5 min, conditional 304s are free), prints one line per new non-self comment on threads
we are subscribed to (our PRs/issues, mentions, participated); `TAGGED` prefix when @jschmied is in the body. State in
~/.config/gh-live/seen.json. Lines are truncated: read the full comment before acting. The 2 h watch ([[watch-read-every-comment]]) stays as the backstop
(it covers threads we are not subscribed to).

**Fix 2026-11-09:** the old version read only each thread's `latest_comment_url`, and under `| head -n 1` a second event in the same poll was marked seen and then lost on the broken pipe. #2638 asks (christopherowen 14:51, ashhart 16:48) sat ~3 h unseen. Now it reads every issue comment, review comment and review body per thread since the last poll (`polled` in seen.json). Re-arm command: `timeout 3h python3 -u ~/notes/watch/gh-live.py --once 2>&1 | head -n 1` (`--once` exits after the first line, so later events stay unseen for the next run). Backup .bak-1109.
