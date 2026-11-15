---
name: overnight-queue-skill
description: Unattended overnight work on the GB10 uses the `overnight-queue` skill — runner + watchdog + cron heartbeat; the heartbeat is the layer that matters
metadata:
  type: feedback
---

Long unattended runs go through the **`overnight-queue` skill**, not ad-hoc scripts. Third time this
was rebuilt from scratch (2026-09-14), so it is a skill now: `~/.claude/skills/overnight-queue/`,
with working `runner.sh` and `watchdog.sh` in its `scripts/`.

**Why:** the failure is never the part people build. A runner and a watchdog were written; the queue
still drained at 01:33 and the box sat idle until 08:04 — **6.5 h** — because nothing decides what to
run next when the queue empties. That layer is a `CronCreate` heartbeat, and it is the one to build
first. Second-worst: the runner marked a *failed* job `.done` and moved on, so a failure was invisible
until morning.

**How to apply:** copy the two scripts, write `jobs/NN-name.sh`, start both detached with `setsid`,
then arm a 30-minute heartbeat whose prompt says to read results, queue more work, clear `.failed`
after fixing the cause, and commit what is verified. The skill's Traps section lists the six ways the
plumbing has silently broken (unbracketed `pkill` killing my own shell, sentinels a tool also prints,
`ls` globbed once, `pgrep -c` exit codes, editing a script the watchdog may spawn, stale sentinels in
an appended log) — read it before debugging a stalled queue.

Related: [[long-jobs-need-detach]], [[gb10-oom-protection]], [[queue-chain-check-before-restart]],
[[verify-before-push]].
