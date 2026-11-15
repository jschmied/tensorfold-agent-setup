---
name: pkill-f-kills-own-shell
description: pkill -f <pattern> matches the invoking shell's own command line and self-kills the tool call (exit 144); check with pgrep first, or kill by pid
metadata:
  type: feedback
---

`pkill -f "ds41-queue/runner.sh"` kills the shell running it, because the Bash tool's command line
*contains that string* — the `-f` pattern matches the full command line of every process including
the one issuing the kill. The tool call dies with **exit 144** and everything after the pkill in that
command block never runs.

This has now happened THREE times on this project (2026-09-19: twice on a runner pattern, once on `pgrep -f 'vllm-venv-main-dflash2/bin/python'` while trying to stop an engine). The second time it silently skipped a `submit.sh`, so
the next run used a stale worktree pinned at the previous SHA and the failure looked like a code bug.

**Why:** exit 144 gives no hint that the cause was self-inflicted, and the commands after the pkill
are simply absent rather than reported as skipped — so the damage shows up later, somewhere else.

**How to apply:** never use `pkill -f` OR `pgrep -f` with a pattern that appears in the command you
are typing — and a `[ "$p" != "$$" ]` guard does not save you, because `$$` inside a pipeline subshell
is not the pid that gets matched (tried, still self-killed). Instead enumerate processes without a
pattern the command contains, e.g. walk `/proc/*/exe` and match the target with `case`. Best of all,
check whether anything needs killing first: all three times the ds41 runner had already exited on its
own when the queue drained, and the third time no engine was even resident. Related: [[never-edit-a-running-job-file]], [[long-jobs-need-detach]].

**Same trap with `pgrep -f` in wait loops (2026-10-26):** a loop such as `until ! pgrep -f "zig build compile-cuda-tests"; do sleep 10; done` matches its own shell's command line, so it never ends. 41 such loops piled up over 1–2 days, along with loops waiting on a done-file that was never written. Instead, wait on a PID (`while kill -0 $PID`), on a lock (`flock`), or on a file with a timeout. Every wait loop needs a deadline.
