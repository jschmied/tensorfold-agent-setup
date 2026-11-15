---
name: never-edit-a-running-job-file
description: Editing a queued job script while the runner is executing it corrupts bash's incremental parse; queue a NEW number instead
metadata:
  type: feedback
---

**Bash reads a script incrementally, so rewriting a job file while the runner is executing it
shifts byte offsets under the running parser.** On 2026-09-17 I rewrote
`jobs/510-prefill-byte-model.sh` (to swap in a non-repetitive prompt) four minutes after the runner
had already started it. The job died with a bash syntax error pointing at a Python line *inside* a
quoted heredoc — `bash -n` on the same file passed cleanly both before and after, which is what
makes this confusing to diagnose: the file was never invalid, the parse was.

**Why:** the runner does `bash "$next"`. Nothing snapshots the file. This is the same class as
removing a `.done` marker and letting the watchdog restart the runner over work in progress — I am
mutating state that a live process owns.

**IT IS NOT ONLY THE JOB FILE. 2026-09-17, second occurrence:** I repointed `fastdecode.py` to
`m.arena` and then `model.py` to define it, in two steps, while job 550 was running out of that
worktree. Between the two edits `fastdecode` referenced an attribute `Model` did not have yet, and
arm 1 died with `AttributeError: 'Model' object has no attribute 'arena'`. The later arms ran fine,
so the failure looked intermittent and infrastructural when it was neither. **The rule covers the
whole SOURCE TREE the running job imports, not just `jobs/*.sh`** — and a multi-file edit has a
window even when each individual file is valid.

**How to apply:** once a job is in `jobs/`, treat the file as immutable. To change its content,
**queue a new number** and let the old one fail or delete it *before* the runner reaches it. Check `cat ~/ds41-queue/RUNNING` first — it names the job that currently owns the box, and that job
is probably importing the repo you are about to edit. The runner's
retry-once saved this one, but a job that has already consumed its `state/<n>.retried` marker gets
no second chance.

Related: [[overnight-queue-skill]], [[verify-before-push]].
