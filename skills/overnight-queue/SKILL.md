---
name: overnight-queue
description: Run measurement jobs unattended on the GB10 box for hours without supervision — a sequential job runner, a watchdog that keeps the box usable, and a cron heartbeat that decides what to run next. Use whenever work should continue while the user is away (benchmark sweeps, A/B arms, profiling runs, long captures), and to diagnose a queue that stalled, failed silently, or left the box idle.
---

# Overnight queue

Three layers. Each catches a different failure, and **the one that has actually bitten us every time is
the layer people forget**: nothing decides what to run when the queue empties.

| layer | what it is | catches |
| --- | --- | --- |
| runner | `runner.sh`, sequential, one job at a time | a job failing — retries once, then marks `.failed` |
| watchdog | `watchdog.sh`, 60 s loop | hung job, memory pressure, full disk, two servers, dead runner, drained queue |
| heartbeat | a `CronCreate` job every 30 min | an **empty queue** — reads results, queues the next experiments |

Copy `scripts/runner.sh` and `scripts/watchdog.sh` to the work dir (default `~/ds41-queue`), write jobs
into `jobs/NN-name.sh`, start both detached, then arm the heartbeat.

```bash
Q=~/ds41-queue; mkdir -p $Q/{jobs,logs,state}
cp ~/.claude/skills/overnight-queue/scripts/{runner,watchdog}.sh $Q/
setsid env PYTHONUNBUFFERED=1 bash $Q/runner.sh   >> $Q/logs/runner.log   2>&1 < /dev/null &
setsid env PYTHONUNBUFFERED=1 bash $Q/watchdog.sh >> $Q/logs/watchdog.log 2>&1 < /dev/null &
```

Then `CronCreate` a heartbeat (`23,53 * * * *`) whose prompt tells you to: read `STATUS` and the job
logs, queue more work if idle, clear `.failed` markers after fixing their cause, and commit anything
verified. Without it the box goes idle the moment the queue drains — on 2026-09-14 that cost **6.5 h**.

## Watchdog goals — failure modes, not liveness

The first version only checked "is the runner alive". Its goals should be:

1. **Progress, not liveness.** A job whose log has not grown in 30 min is hung (a server that never
   becomes healthy, a request on a 3600 s timeout). Kill it, mark `.failed`, let the queue move on.
2. **Protect the box.** Unified memory, and GPU allocations are invisible to cgroups, so nothing can
   cap the server (see memory `gb10-oom-protection`). Below a MemAvailable floor, stop the server
   yourself — the alternative is the OOM killer taking sshd and the session with it.
3. **Protect the disk.** An nsys report is ~200 MB, its sqlite export 1–3 GB. Exports are regenerable
   from the report, so delete those first; never delete a report to make room.
4. **Never idle, never unserved.** On drain, keep looping so a later-added job is picked up, and
   restore the production server if nothing is queued.
5. **Leave a STATUS file.** One read tells the next session what is running, for how long, what
   failed, and how much memory and disk are left.

It must **never decide what to run** — that is the heartbeat's job. It only keeps the box in a state
where the next decision is still possible.

## Traps — every one of these cost a real run

* **`pkill -f` matches your own shell.** The harness wraps commands, so your command line contains the
  pattern. It killed my shell twice in one session, including with the bracketed `to[y].py` form —
  because the *same command line* also contained the unbracketed name in a later clause. Kill by PID:
  `ps -eo pid,args --no-headers | awk '$2=="bash" && $3==path {print $1}'`.
* **Sentinels that a tool also prints.** A wait-job grepped for `ALL DONE`; the measurement tool
  printed `== ALL DONE ==` after *every* run, so the wait returned instantly and two jobs contended
  for the box. Use a sentinel only your own runner emits (`QUEUE DRAINED`).
* **Appended logs make sentinels stale.** `grep -q "QUEUE DRAINED" runner.log` was true from the
  *previous* round, so the watchdog exited on startup. Check `tail -1`, or use a state file.
* **`for j in $(ls jobs/*.sh)` expands once.** A job added after the runner started is never seen —
  the highest-value job of a night silently never ran. Rescan every iteration.
* **`pgrep -c` prints `0` and exits 1.** `$(pgrep -c ... || echo 0)` yields `"0\n0"` and every later
  `((n > 1))` is a syntax error. Use `|| true`.
* **Editing a script the watchdog may spawn is a race.** A half-written `runner.sh` was executed
  mid-rewrite and died on a syntax error. Write to a temp file and `mv` it into place.
* **Detach with `setsid` and `< /dev/null`.** A harness background shell dies with the session.
  Verify with `ps -eo pid,ppid` — a detached job shows `ppid 1`.
* **Parallel agents share one checkout even when asked for worktree isolation.** Two agents on the
  same repo at once produced: one switching HEAD while the other was mid-commit, a commit landing
  on a third agent's branch, a force-reset of that branch to "repair" it, and a third agent's
  uncommitted WIP left dangling under a moved HEAD. Nothing was lost, but only because one agent
  noticed. **Run at most one agent per repo at a time**; if two must run, give the second a
  different repo or wait. When a collision happens: do NOT switch branches while someone's WIP is
  uncommitted — tell the live agent to commit where it stands and relocate the commit yourself.
* **A subagent can leave the shared checkout on its own branch.** Twice in one session an agent
  worked "in a worktree" but the main repo's HEAD ended up on its feature branch. The second time
  it was invisible: `git merge feat/x` answered *"already up to date"* — because HEAD *was*
  `feat/x` — so the merge silently did nothing, the work never reached `main`, and a later commit
  of mine landed on the branch too. `git push origin main` then says "Everything up-to-date" while
  `origin/main` sits several commits behind. **After any agent touches a repo, check
  `git rev-parse --abbrev-ref HEAD` before merging, and check `git log --oneline origin/main -1`
  after pushing.**
* **One server at a time — but the watchdog must not enforce it while a job is running.** Every job
  stops the server and starts its own, so a second server mid-job is a transient the job is already
  resolving. Acting on it killed the job's own server and failed the run. While a job owns the box,
  server management belongs entirely to the job; the watchdog only acts when idle, and only after
  seeing the condition twice in a row.
* **Restoring the production server races a job being queued.** The restored server was still loading
  weights when a newly queued job started its own, and the pair tripped the two-server rule. Require
  two consecutive idle checks before restoring.

## GPU jobs beside a long training run (added 2026-10-08, Kolibri drafter)

The GB10 holds one big model at a time (two 77 GB copies do not fit in 128 GB unified memory), so training,
generation servers and GPU tests take turns. The pattern that worked a dozen times in one day:

* **Pause only at a checkpoint save.** A root runner waits for the step file (`until [ -e out/drafter-stepN.pt ]`,
  then `sleep 30` so the copy settles), stops the training unit, waits until it is inactive, runs the GPU job
  (oracle test, scoring, a few minutes), and restarts the SAME training script, which resumes from `resume.pt`.
  Lost work: zero steps; pause cost: the job's own minutes.
* **Switch runners for phase changes** (training -> generation -> training): the same wait-for-save, then the next
  phase's script. A waiting runner may be stopped and replaced (it has executed nothing yet); a running one may not.
* **Disk-floor switch.** A generation phase writes recordings at a measurable rate (German chat: ~6 GB/h); a runner
  that ends the phase below a floor and starts the next one keeps the night productive instead of idling at the
  recorder's own floor.
* **Serving phases: `--parallel` >= concurrent clients.** One slot short and the prompt cache hits ~0 % (every turn
  of a 90k-token agent session re-prefilled); the fix lives in the runner, not in a hand restart that the next
  batch forgets.
* `bash -n` every generated runner before `systemd-run`; it caught a broken multi-line substitution on 2026-10-08.

## Job conventions

* One job = one file, `NN-name.sh`, named so `sort` gives the intended order. Leave gaps (10, 15, 20)
  so a job can be inserted ahead of pending work.
* A job owns the box for its whole run: stop the server, start it with its own env, measure, stop.
* **Warm reps are the instrument.** On this box a cold rep spreads 20 % across restarts while warm
  reps reproduce to 0.3 %. Always take ≥4 reps and discard rep 1.
* A job that changes output must compare the output, not just timings — generate greedily and compare
  a hash across arms.
* Runners are never committed to a repo (project rule); the *tools* they call are.

Related: memories `long-jobs-need-detach`, `gb10-oom-protection`, `queue-chain-check-before-restart`,
`verify-before-push`; skill `gb10-ab` for how a server A/B is measured and recorded.
