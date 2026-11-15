---
name: gb10-job-dispatcher
description: GB10 GPU/build jobs go through ~/notes/jobs dispatcher (timing/correct/build lanes, events.log Monitor); tfb = 2 build slots + shared zig cache
metadata:
  type: project
---
Since 2026-11-05 10:00, at the user's ask ("do optimizations with priority … faster crash notifications").
- Dispatcher: `~/notes/jobs/dispatch.py`, run in tmux session `dispatch` (a restart loop; there is no user systemd bus).
  Agents drop `~/notes/jobs/q/<id>.json` and end their turn. Rules for agents: `~/notes/jobs/README.md`.
- Lanes:
  - `timing`: gpu.lock exclusive.
  - `correct`: gpu.lock shared. Runs beside other correct jobs, never beside timing.
  - `build`: one of two `~/bin/tfb` slots.
  - The higher prio starts first. A waiting timing job of the same or higher prio stops new correct jobs.
  - Each start needs MemAvailable ≥ the job's need + 20 GB.
- Events: `~/notes/jobs/events.log` (DONE, FAIL with log tail, QUIET = no log change for quiet_min then killed,
  TIMEOUT, BADJOB, ORPHAN). The main session keeps a Monitor on it, re-armed every 30 min, and resumes the job's
  `owner` agent.
- `~/bin/tfb`: slot 0 = tfbuild.lock (legacy `flock tfbuild.lock` still excludes it), slot 1 = tfbuild.1.lock.
  Needs MemAvailable ≥ 24 GB. Sets `ZIG_LOCAL_CACHE_DIR=~/.cache/zig-local`, one cache for every worktree
  (the per-worktree caches had reached 72 GB). v.sh uses tfb.
- Why: on 11-05, five builds queued behind one lock while the GPU sat idle, and agents polled for locks at a token cost.

**How to apply:** new jobs go through the dispatcher, never a hand-run flock queue. Before trusting a silent
dispatcher, `tmux ls` should show `dispatch`, and `tail events.log` should show its `DISPATCHER up` line.

**2026-11-05: cudafast harness runs (local-baseline.sh / benchd) go in the TIMING lane, even pure golden/tape checks.**
benchd gates every phase on quiescence (load < 2, util < 0.1), so two tfb builds beside a "correct" golden stalled it
at load 4.3 for 10 min until I killed them. Also: the drain rule (timing waited > 15 min) starts even prio-5 timing
jobs ahead of prio-40 builds; gate low-prio jobs with `ready` on the urgent chain's done marker instead.

**2026-11-06, three dispatcher traps in one morning (all in ~/notes/jobs/README.md):**
- `ready` greps on events.log must be anchored (`^[0-9:]+ DONE <id> rc=0`): the STALL line quotes the test and matches a plain grep.
- `correct` jobs start in one tick and the MemAvailable check sees none of the others' memory: five model servers declared ~200 GB on a 121 GB box. Model servers go in `timing`.
- A waiting `timing` job holds back every new build (drain rule) and same-prio `correct` job, so a long timing queue starves a p20 build; park timing jobs in ~/notes/jobs/hold/ to let it through.

**Monitor drops some FAIL events (11-06):** four FAIL lines never arrived though the log is valid UTF-8 with no NULs; cause not found. On every re-arm, check `grep -v START events.log | tail`. Job rc=0 can still hide an `exit 0` script: read the log. QUIET kills jobs writing only to a file; buffered `cut` hides stdout too (stdbuf -oL).

**Traps (11-06/07):** non-build jobs need `avail_gb() >= mem_gb + 20`; the box has ~115 GB, so mem_gb must be ≤ 95. A ready job above that never starts and blocks the queue (hit twice, sw2 and sw4). In `ready`, `! ls a b` is wrong when one glob is empty: use `test -z "$(ls ... 2>/dev/null)"`. An IDLE monitor line can be a false alarm in the gap between two jobs: check run/ first.
Lean in a job: `lean_check.py` scans the tree it sits in, so a copy outside the checkout counts "0 files, 0 problems" and every finding reads as new (hit twice on 11-07). Run the checker from inside each worktree, and fail when the base scans 0 files.


**Who resumes agents (2026-11-09):** nobody but the agent itself. BRIEF-COMMON said "end your turn after queuing; you
are resumed on events", but no main-session watcher did that, so agents (copymatch, chunksolo) stopped with jobs
queued and nothing would wake them. Now: job `owner` = the agent's [card-key], and the agent starts its own background
wait on DONE/FAIL before ending its turn. `~/notes/dash/hook.py` holds a SubagentStop once when the card has jobs in
q/ or run/ (matched by owner == key, owners, prefixes); a second stop marks it `parked` and the main session must arm
the wait and SendMessage it.
