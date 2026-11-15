# Common rules for ledger-cell agents (read fully before starting)
- Repo: TensorFold (Zig). Clone ~/git/tf-ledger: remote `origin` = upstream ashhart/TensorFold, `fork` = ours (jschmied). Ledger: docs/optimization-ledger.md on branch docs/optimization-ledger (PR #2232).
- Fresh worktree per task from origin/main (or stacked on the named open PR's head: `gh pr view N --json headRefName`, fetch from fork).
- ATC first (atc_board/atc_check/atc_overlap via `node ~/.claude/plugins/cache/atc-github/atc/0.7.0/src/cli/main.js` in the worktree); claim/start under the standing go. Search open AND closed PRs for the same work; if taken, stop and report.
- SHARED CODE: BEFORE writing code, check what can be shared (core/lanes, other families, the other backend CUDA/Metal) and list core vs backend-only parts in the plan. One optimization on several families or backends = one implementation in core/lanes/shared code. No copies. Name the shared file in the report.
- Hypothesis + expected range in ~/notes/ledger/<task>/PLAN.md BEFORE coding; keep STATUS.md current (work may resume after a usage pause).
- If the work is multi-day or blocked, stop after the plan and report.
- GPU/builds ONLY via the dispatcher: read ~/notes/jobs/README.md, follow exactly (q/<id>.json via .tmp+mv, owner = the [card-key] from your description; after queuing, START A BACKGROUND WAIT (run_in_background, deadline) that ends when each of your jobs is DONE or FAIL in ~/notes/jobs/events.log, then end your turn: that wait wakes you. Never end your turn with jobs queued and no wait of your own; the board hook holds such a stop once). CUDA builds: `-Dnvcc=/usr/local/cuda/bin/nvcc -Dsm=121`; zig ~/opt/zig-aarch64-linux-0.17.0/zig; `zig build native` → <prefix>/native/bin/tensorfold-native; md5 every binary you run. Drop page cache before each server start; A-B-B-A for timings; nsys OK, ncu only on synthetic tests.
- Exactness: outputs byte-identical to main unless the task says otherwise (greedy tokens, plus sampled at default draw for spec paths).
- Verify before commit: zig build test, lean (0 new), zig fmt --check, git diff --check, kernel contract for touched families.
- Commit locally, author `Jürgen Schmied <600316+jschmied@users.noreply.github.com>`, NO co-author/AI trailers. Do NOT push, open PRs, or post anywhere.
- Never pkill -f / pgrep -f (kill by PID / session); every wait has a deadline; no git stash; never commit .sh; disk floor 40 GB; weights under ~/models and /opt/llm/models, no downloads (archived models can be restored from PBS <pbs-host> only if the main session says so).
- Other agents' worktrees: ~/git/tf-solo-chunks, ~/git/tf-recurrent-pool, ~/git/tf-statewalk, ~/git/tf-igpu-states, ~/git/tf-prompt-tail, ~/git/tf-l2pf. Don't edit others' worktrees.
- Final report ≤250 words: done, branch+SHA, numbers with receipt paths, shared file, risks.

## Dashboard block (2026-11-08)
Keep a `<!-- dash ... -->` block near the top of your ledger STATUS.md; spark-dash reads it live (no edit of tasks.json):
```
<!-- dash
now: what you are doing right now (one line)
next: step a; step b; step c
eta: 2026-11-09T06:00
-->
```
Update it at every milestone (job queued/finished, push, blocked). `note:` is optional.
- 11-09: TF CHANGELOG lines are ashhart's (placed at landing): no CHANGELOG commits in new PRs unless he asks; put the proposed line in the PR body.
- BANDWIDTH: the GB10 is memory-bandwidth-bound (273 GB/s). A compute-side change that is exact but level here is NOT a
  drop: push, write the body with the GB10 numbers marked "bandwidth-bound here", and name the cells a tester with a
  discrete card (Maxrio9 sm_120, clee sm_80) should run. Stop only if exactness fails or the GB10 gets slower.
