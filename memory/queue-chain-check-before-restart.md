---
name: queue-chain-check-before-restart
description: Before (re)starting any runner unit, grep every runner's wait list for mutual waits — the stack1/plewait deadlock happened TWICE (4 h lost, then again on a restart)
metadata:
  type: feedback
---

Runner units on the box wait on each other by name (`systemctl is-active --quiet <unit> || break` loops). Restarting a unit
re-enters its wait list, and if any queued unit waits on it while it waits on that unit, both sit idle forever with the GPU free.
This happened 2026-09-05 18:25–22:17 (plewait ↔ stack1) and AGAIN at 22:45 when I restarted stack1 unchanged after fixing a patch.

**Why:** the box is the only measurement resource; a silent mutual wait looks exactly like "still running" and costs hours.

**How to apply:** before any `systemd-run` of a runner: `grep -n 'is-active' /opt/llm/runners/*.sh` and check that no unit in
the new unit's wait list has the new unit in ITS wait list. When restarting a unit that others wait on, freeze the waiters
(`systemctl kill -s STOP <u>`) for the swap and `CONT` them after, so they do not jump the queue during the gap.
Related: [[long-jobs-need-detach]].
