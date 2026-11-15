---
name: tf-gpu-validation-budget
description: "TF agents share one GPU; speed A/Bs only on final branches, 2+2 repeats (3+3 only if within noise), only touched families; exactness gates unchanged"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-25T19:22:43.884Z
---

All TF agents share one GPU. Speed A/Bs run only on a final branch, not after every commit. Use 2+2 alternating repeats per arm, and go to 3+3 only when the difference is within noise. Test only the families the change touches. The exactness and byte-change gates stay complete.

**Why:** on 2026-10-25 about 10 jobs were queued on gpu.lock, each waiting 40–55 minutes behind per-commit speed arms and full family grids. The user asked whether that much validation was needed and approved this trim ("ok").

**How to apply:** put these rules in every new TF agent prompt that uses the GPU. See also [[tf-shared-kernels-simple-optimal]].

**Lock rule (2026-10-26):** never hold `tfbuild.lock` and `gpu.lock` at the same time, and watch for inherited flock fds. The host-fix arm script held the build lock while it waited on the GPU, and prompt16's builds starved for over an hour.

**Two lock modes (2026-10-26, user "ok"):** the protocol is in `/tmp/claude-1000/gpu-rules.md`.
- **Timing work:** `flock -x`, and it registers in `gpu.xwant.d`.
- **Correctness work:** `flock -s`; it waits while a timing job is pending, holds the lock under ~15 min, and checks free memory before loading weights.
- **CPU-only work:** runs outside the lock.

**Why:** a Debug contract run held the GPU lock for 62 min at 0% GPU. `TF_CONTRACT_ONLY` doesn't exist on main, so it ran the whole contract. Meanwhile 14 jobs waited.
