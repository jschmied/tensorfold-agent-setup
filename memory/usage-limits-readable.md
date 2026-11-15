---
name: usage-limits-readable
description: "Claude's 5-hour/7-day usage limits are readable at ~/.claude/usage-now.json (written by the status line script)"
metadata:
  node_type: memory
  type: reference
  modified: 2026-10-27T10:27:30.774Z
---

`cat ~/.claude/usage-now.json` gives `{at, session, rate_limits:{five_hour:{used_percentage,resets_at}, seven_day:{...}}}`. The `resets_at` times are epoch seconds.

It is written by `~/.claude/statusline-command.sh` on every status line refresh (added 2026-10-27 at the user's request: "can you make it readable for you"). Check `at` for staleness.

Use it before launching subagent fan-outs or workflows. Full procedure: the `usage-self-management` skill (`~/.claude/usage-report.py --json` → state ok/careful/throttle/stop by the hourly delta vs the budget to reset; history in `~/.claude/usage-history.jsonl` since 2026-10-27; token backfill from transcripts, 9.3 M weighted units ≈ 1 %).
