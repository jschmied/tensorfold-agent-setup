---
name: usage-self-management
description: Check Claude's own 5-hour / 7-day usage budget and act on the user's standing limits — read the current %, the burn rate and the reset time, and know the few absolute levels that change what work may start. Use when the user asks about usage, limits or credits, at the 2 h watch, and before a very large fan-out (workflow, many agents).
---

# Usage self-management

## Instruments

| What | Command |
|---|---|
| Verdict (fast) | `python3 ~/.claude/usage-report.py --json` → `d7`, `h5`, `h5_reset_in`, `rate_pct_per_h`, `projected_d7_at_reset` |
| Overview | `python3 ~/.claude/usage-report.py` (24 h hourly) · `--days 7 --tokens` (daily table, main vs subagent) |
| Raw snapshot | `cat ~/.claude/usage-now.json` (written on every status line refresh) |

Data: `statusline-command.sh` appends the % to `~/.claude/usage-history.jsonl` while a UI refreshes; without one the
snapshot goes stale (`sample_age_s` > 1 h: trust it less). The token fallback reads this machine's transcripts
only (weights: input 1, output 5, 1 h cache write 2, cache read 0.1), so mac-agent and cloud sessions on the same
account are missing: token rates are a lower bound.

## The rules (user, standing; the latest of several overrides, 10-27 … 11-09)

| level | what to do |
|---|---|
| d7 < 90 % | **Work normally.** Parallel subagents freely; the projection (`state` careful/throttle) does **not** limit work. Don't mention usage in status updates unless asked. |
| d7 ≥ 90 % | Tell the user once, with d7, the burn rate and the reset time. Keep working. |
| d7 ≥ 98 % or h5 near its limit | Only the watch and PR/reviewer replies. h5: wait for `h5_reset_in` rather than stopping for good. |

The budget is ~14 %/day (100 % over 7 days, user 11-07); consumption is not linear, so a few busy hours projecting
over 100 % are no reason to hold work (user 11-08/11-09: "rules are too tight").

When usage is genuinely short, the user's order is: reviewer replies first, let running agents finish, start
nothing new, then report the leftover and let the user decide (10-28). The user decides every trade: give the
numbers and the reset time, then follow their call. Never stop work silently over usage.

## What costs what (measured 10-21 … 10-27)

- Subagents are 85–95 % of a heavy day (≈200 M units ≈ 21 % of the week with several parallel agents).
- The main thread alone: ≈ 1–2 % a day.
- A subagent's cost is its context re-read per tool call: long investigations (100+ calls) are the expensive ones.
  Narrow brief, word cap on the report.

## Habits

1. Before a workflow or a fan-out of many agents, run `--json` once.
2. At the 2 h watch, add d7 to the line only at ≥ 90 %.
3. When the user says usage is draining: `--days 7 --tokens`, show the daily table; the subagent column explains it.
