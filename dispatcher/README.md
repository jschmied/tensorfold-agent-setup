# GB10 job dispatcher (since 2026-11-05 10:00)

Don't wait on gpu.lock or tfbuild.lock yourself, and don't poll. Drop a job file and end your turn: the main
session gets the event within seconds and resumes you.

    ~/notes/jobs/q/<id>.json   (write to a .tmp name in q/, then mv it to <id>.json)
    {"id": "<id>", "owner": "<your agent id>", "lane": "timing|correct|build", "prio": 10, "mem_gb": 20,
     "cwd": "/home/jschmied/git/<worktree>", "cmd": "<command>", "ready": "<optional shell test>",
     "quiet_min": 10, "deadline_min": 60}

- **lane**
  - `timing`: anything whose numbers are speeds. It holds gpu.lock exclusively.
  - `correct`: token/logit equality, contracts, CUDA tests, receipts without timing. It holds gpu.lock shared, runs
    beside other correct jobs, and never runs beside a timing job.
  - `build`: one of two build slots (`~/bin/tfb`), with the shared Zig cache.
- **prio**: higher runs first. A job that blocks another agent gets 20 or more, a final measurement 10.
- **ready**: a shell test run in `cwd`. The job only starts once it exits 0 (for example `test -x zig-out/bin/x`).
- **quiet_min**: a job whose log stays unchanged this long is killed and reported as QUIET. The default is 10, or 30
  for builds. Raise it for jobs that are silent on purpose.
- **Results**:
  - Your job's output goes to `~/notes/jobs/done/<id>.log`, and the finished job file to `done/<id>.json`.
  - Every state change is one line in `~/notes/jobs/events.log`: START, DONE, FAIL (with the log's last lines),
    QUIET, TIMEOUT, STALL (queued but not ready for 20 min), BADJOB and ORPHAN.

Building by hand: `~/bin/tfb zig build ...` in place of `flock tfbuild.lock zig build ...`.

**Cancel a job:** `kill -TERM $(ps -s <pid> -o pid=)`, where `<pid>` comes from the job's START line in events.log (it is the job's session id; `timeout` starts new process groups, so `kill -- -<pid>` misses them).
signals the whole process group. Never kill the wrapper shell alone: that frees the lock while your command keeps
running on the GPU unlocked. That happened to e4b-4a at 10:11.

**Shell variables in `cmd`** (`$?`, `$!`, `$x`): fixed at the next dispatcher restart after 12:40 on 2026-11-05. Before
that, the outer shell expanded them early. Jobs queued before then should use a script file.

**`ready` on events.log: anchor the line** (`grep -qE '^[0-9:]+ DONE <id> rc=0' events.log`). A plain `grep 'DONE <id> rc=0'` matches the dispatcher's own STALL line, which quotes the ready test, so the job starts early (asr2239-gate, 2026-11-06).

**`correct` jobs run side by side and start in one tick (the MemAvailable check sees none of the others' memory): a model server belongs in `timing`. At the least it** needs its own port (`SW_PORT`-style env), never a fixed one. Five sw-ident jobs shared 18197 on 2026-11-06 and answered from each other's servers (two models with the same hash) with rc=0.

**Prio beats lanes (2026-11-08).** A ready timing job blocks only builds and correct jobs of its prio or lower (drain too). Before, any ready timing job drained every build, so a prio-8 A/B (5.5 h deadline) held seven prio-20 reply jobs. Not-ready timing jobs block nothing.

**Resources are the main session's (2026-11-08, user).** Agents never swap, restore or delete models or other agents'
files to free disk or memory. Ask spark-agent (main) with path, size and how long it is needed; main does the swap
after checking q/*.json, ~/notes/ledger/*/ and lsof, and logs it in ~/notes/disk-swaps.log.

**Minimum builds and verifies (2026-11-08, user).** Run only what the change needs:
- While iterating: only the tests of the touched families/steps (e.g. `zig build test-<family>-host`), lean on touched files.
- The full CI set exactly once, on the final head, before the push that a PR or review reply needs. Not after every edit.
- A failed step: fix and rerun that step only; the full set again only on the final head.
- No served/native build unless the change reaches compiled CUDA code; reuse a main binary already built for the same
  commit (~/notes/bins/<sha>/) instead of rebuilding main.

**Lane `x86` (2026-11-08): host-only checks on <x86-host> as user tfci** (never root: tests that expect `chmod 000` to refuse pass as root) (8 cores, no GPU, Zig 0.17.0 at /opt/zig-0.17.0). Give
`"sha"` (reachable from `cwd`'s repo) and a `cmd` that calls plain `zig`; the dispatcher pushes the sha (and origin/main)
to /srv/tf.git, runs `cmd` in a fresh worktree /srv/tf-wt/<id> (removed after; `$TF_BASE` = merge base with origin/main,
for lean), shared cache /srv/zig-cache (pruned at 15 GB). One job at a time, no gpu.lock, no tfb slot, never drained by
timing. Belongs there: `zig build -Dfixed-cpu test-host` (GitHub CI runs it; missing it let #3294 pass x86 and fail CI, 11-15), `zig build -Dfixed-cpu test test-golden test-kernel-contract test-server-security
test-pull-security fuzz-cortheon check-release-paths`, `zig build check-native-cuda-host compile-cuda-tests` (native
x86, no -Dtarget), `python3 tools/pr_check.py`, lean, `zig fmt --check build.zig zig`. Stays on the GB10: anything with
nvcc/-Dnvcc, test-cuda-host and the family -cuda-host tests, the kernel contract run on the GPU, native/served builds,
every timing or correctness run. Example:
`{"id": "pr123-host", "owner": "kv-p3", "lane": "x86", "prio": 10, "cwd": "/home/jschmied/git/tf-123", "sha": "abc1234",
"cmd": "zig build -Dfixed-cpu test test-golden --summary line && python3 tools/pr_check.py", "deadline_min": 60}`.
Cancel: kill the START pid's session as above; the dispatcher then kills the remote session (/srv/tf-run --kill <id>).

**Servers must die with their job (2026-11-08).** A job that starts a server in its own session (setsid/start_new_session)
must kill it on exit (`trap 'kill $SERVER_PID' EXIT TERM`). Preempting q1 at 17:39 left two servers (62 GB) running,
which stalled the next 95 GB timing job.

**Dashboard block (2026-11-08).** Each agent keeps a `<!-- dash now/next/eta -->` block in its ledger STATUS.md
(see ledger/BRIEF-COMMON.md); a task's `ledger` field in dash/tasks.json points at the dir. Read live per page load.
- x86 lane 11-08 23:2x: /srv/tf.git, tf-wt, zig-cache, tf-run.lock were root-owned (created before the tfci switch) -> git 'dubious ownership'; chowned to tfci.
- x86 lane 11-09 02:2x: partial zig-cache prune (oldest o/ dirs) broke builds (169 failed steps, h/ manifests -> deleted outputs). tf-run now wipes the whole cache when over the 15 GB cap.
- 02:2x shared /srv/zig-cache wiped (stale manifests from the old partial prune). NOTE: I edited tf-run while x86c ran -> its 'syntax error line 59' (bash reads scripts lazily); never edit tf-run while an x86 job runs.
- 2026-11-10: a job whose cmd is over ~2 MB (E2BIG) made every step() raise, stalling ALL lanes 12:29-12:49. Validation now parks cmd >= 64000 bytes as BADJOB (active from the next dispatcher restart; not restarted, jobs were running). Long commands go in a script file.
19:49 f2-conf mem_gb 100->96: 100+20 > 118 GB avail made it unstartable AND it blocked all prio-5 builds via top_ready (stall since 19:11). TODO dispatcher: top_ready/drain only count timing jobs whose memory fits.
- 2026-11-10 21:xx: dispatcher (active from next restart): same-prio jobs FIFO by queue-file mtime (was file-name order: rowcap-x86d starved 3 h); top_ready/drain count only timing jobs whose mem_gb+20 fits (f2-conf at 100 GB blocked all prio-5 builds 19:11-19:50).
- 11-11: same-prio FIFO between lanes: a ready timing job holds back only builds/correct jobs queued after it at its prio (and lower prios). Replaced the drain/top_ready rule (sampler4 builds starved 18 h). Backup dispatch.py.bak-1111.
- PAUSE file in ~/notes/jobs: nothing new starts (restart: touch PAUSE, wait for run/ empty, kill dispatcher PID, rm PAUSE).
