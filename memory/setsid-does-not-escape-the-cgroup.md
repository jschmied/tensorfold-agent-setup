---
name: setsid-does-not-escape-the-cgroup
description: "setsid detaches from the TERMINAL, not from the systemd cgroup — restarting claude-remote.service (KillMode=control-group) reaped my 'detached' overnight runner and watchdog. Launch long-lived helpers as their OWN transient units"
metadata:
  type: feedback
---

**2026-09-23.** I restarted `claude-remote.service` at the user's request and told them the overnight
runner and watchdog would survive because they were `setsid`-detached with `ppid 1`. They did not.

**Why.** `claude-remote.service` has **`KillMode=control-group`** (the default), so stopping it kills
every process in `/system.slice/claude-remote.service`. `setsid` breaks the controlling-terminal and
session association — it does **not** move a process out of the unit's cgroup. `ppid 1` looks like
independence and is not.

**What did survive:** `fx-armrun-ishare2.service`, because `systemd-run` had created it as its own
unit in its own cgroup. It outlived its parent `armrun` and kept port 8092, which made prod's unit
read `active` while the API was down — worth recognising as a symptom.

**How to apply:**
- A helper that must outlive this session gets its **own transient unit**:
  `systemd-run --unit=NAME --collect --uid=jschmied --gid=jschmied -E HOME=/home/jschmied -E ... bash -c "..."`.
  Verify with `systemctl show NAME -p ControlGroup --value` — it must NOT be under
  `claude-remote.service`.
- `~/qwen-night`'s supervisors are now `qwen-night-runner.service` and
  `qwen-night-watchdog.service` for exactly this reason ([[overnight-queue-skill]] still describes the
  `setsid` launch; that form is only safe if the session is not restarted).
- Before claiming anything survives a restart, check the **cgroup**, not `ppid`.
- After any session restart: an orphaned `fx-*` or `*-srv` unit may be holding the serving port —
  check it. **The heartbeat cron is NOT lost** (corrected 2026-09-23): with `--continue` the cron store
  is restored, and re-arming after a restart created a DUPLICATE that fired twice per tick. Run
  `CronList` first and only re-arm if it is actually empty.
- Whole-system service restarts happen from outside this session too: at 07:54 on 2026-09-23 a login
  session cycled journald, networkd, resolved, containerd and more, restarting claude-remote AND the
  `qwen-night-*` units. The queue units survive *claude* restarts, not a system-wide one. armrun's
  append-only `results/armrun-<spec>.jsonl` survived it; the runner's `> logs/NN.log` did not.
  Related: [[long-jobs-need-detach]], [[claude-autostart-remote-control]].
