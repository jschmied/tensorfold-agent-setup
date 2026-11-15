---
name: usage-self-management
description: Check and manage Claude's own 5-hour / 7-day usage budget before spending it — read the current %, the hourly burn rate and the projection to reset, then pick how much parallelism (subagents, workflows, forks) the budget allows. Use before launching subagents or a workflow, at the start of a long autonomous run, when an hourly watch fires, and whenever the user asks about usage, limits or credits.
---

# Usage self-management

## Instruments

| What | Command |
|---|---|
| Verdict (fast) | `python3 ~/.claude/usage-report.py --json` → `state`, `d7`, `h5`, `rate_pct_per_h`, `allowed_pct_per_h`, `projected_d7_at_reset` |
| Overview | `python3 ~/.claude/usage-report.py` (24 h hourly) · `--days 7 --tokens` (daily table + where tokens went, main vs subagent) |
| Raw snapshot | `cat ~/.claude/usage-now.json` (written on every status line refresh) |

Where the data comes from:
- **% history:** `~/.claude/statusline-command.sh` appends to `~/.claude/usage-history.jsonl` when a value changes, otherwise every 10 min, and only while a Claude Code UI is refreshing. History starts 2026-10-27.
- **Token fallback:** `usage-report.py` reads the transcripts in `~/.claude/projects/**.jsonl` and weights each token type (input 1, output 5, 1 h cache write 2, cache read 0.1). It calibrates those units against the current % since the 7-day window opened. Baseline 2026-10-27: **9.3 M units per 1 %**.
  - It only sees **this machine**. mac-agent and cloud sessions use the same account but aren't counted, so treat token rates as a lower bound.
  - A stale snapshot (`sample_age_s` > 1 h) means no UI was refreshing. Trust it less.

## Judge by the hourly delta, not the absolute %

A high 7-day % with a low burn is fine. A low % with a fast burn is not. The question is always: **does the current rate run out before the reset?**

`allowed_pct_per_h` = (100 − d7) / hours to reset. Compare the 6 h rate with it:

| state | condition | what to do |
|---|---|---|
| ok | projected at reset ≤ 100 % | Normal work. Subagents in parallel when the work is truly independent. |
| careful | projected 100–125 % | Run subagents one at a time and prefer inline work. No workflows. Tell the user in one line. |
| throttle | projected > 125 % | No new subagents/workflows/forks. Finish running work, keep turns short, tell the user the numbers and the reset time. |
| stop | d7 ≥ 95 % or h5 ≥ 95 % | Only finish what is in flight. Ask before anything new that costs tokens. |

The 5-hour window resets often. Near its limit, pause until `h5_reset_in` rather than downgrading the plan.

## What costs what (measured, 2026-10-21 … 10-27)

- **Subagents dominate.** They were 85–95 % of daily units on heavy days: Sun 10-25 193 of 201 M, Mon 10-26 200 of 219 M. A day with several parallel research/fix agents ran about 200 M units, about 21 % of the week, so about 0.9 %/h. A peak hour was 23 M, about 2.5 %/h.
- **The main thread alone** runs about 7–19 M units a day, roughly 1–2 % a day.
- **The cost of a subagent** is its context re-read on every tool call. Long investigative agents (100+ tool calls) are the expensive ones. Give them a narrow brief and a word cap on the report.

## Habits

1. Before launching ≥2 agents or any workflow, run `--json` and act on `state`.
2. In the hourly watch, add the 7-day % and 6 h rate to the line only when the state is not `ok`.
3. When the user says usage is draining, run `--days 7 --tokens` and show the daily table. The subagent column usually explains it.
4. Never stop work silently over usage. State the numbers and the reset time, then carry on at the allowed level.

## User override (2026-10-27)
At THROTTLE (projection 101 %), the user said "do the fixes" and then "let all tasks run". Four agents ran: review fixes, #1353 fixes, the LFM2 port, `fact_swiglu`.

The user decides the trade, so give the numbers and the reset time, then follow their call. Don't pause running work on my own. "Throttle" means: don't START extras unasked, and report the projection at each hourly watch.

## User budget (2026-10-27 evening)
The user said "we used 7% today thats ok": about 7 % a day is an acceptable burn even when the projection says throttle. Treat about 7 %/day (about 0.3 %/h averaged) as within budget, report it, and don't pause or decline work below that.

## User budget raised (2026-11-07)
"raise usage limits, 100/7 is 14% a day": the budget is now **about 14 %/day (about 0.6 %/h)**, the full week spread evenly. It replaces the 7 %/day above. At or below that rate, keep working normally, with parallel subagents where the work is independent, even if `state` says careful. Above it, report the numbers and slow down. The 98 % stop rule still holds.

## User priority at throttle (2026-10-28, 85 % used, 106 % projected)
"review responses first, let other agents finish, then decide based on leftover usage."
1. Reviewer replies and asks come first: post the agents' reply drafts, and handle small reviewer asks.
2. Running agents finish; start no new ones.
3. Then report the leftover usage and let the user decide what's next. #1293 and #1222 wait for that.

## User stop line (2026-10-28, at 90 %)
"3a jetzt, bei 95% stoppen" — #1293 step 3a runs on mac-agent despite throttle; HARD STOP at 7-day 95 %: commit verified work, push to fork, report, start nothing new. Check `d7` at every hourly watch while it runs.

## User override (2026-11-08)
"usage is not critical since we have plenty left and consumption is not linear." With d7 around 22 % and days to reset, a
projection in the 80s from a few busy hours is not a reason to hold work. Don't pause or limit subagents for "careful";
start work the user asked for. Report the numbers only when asked or when d7 itself gets high (≥ 80 %).

## User override (2026-11-09): don't throttle by projection
At 42 % with a 94.6 % projection the user said: "dont considder throtteling we are at 42 % only, rules are to tight".
The projection bands (careful/throttle) no longer limit parallelism or new agents. Run agents in parallel freely.
Only the absolute levels count: at d7 ≥ 90 % tell the user once; at ≥ 98 % only watch + PR replies (memory
`usage-limit-99`). Don't mention usage in status updates below that unless asked.
