---
name: GPU arms take one lock only
description: measurement arms take gpu.lock only, builds take tfbuild.lock only; never hold both (starves builds, deadlocks)
type: feedback
---
Measurement arms with prebuilt binaries take only /tmp/claude-1000/gpu.lock; builds take only tfbuild.lock and release it
before any GPU step. Never hold both at once.

**Why:** 2026-10-25/26 hostfix run: agents took the two locks in opposite orders (c1284 gpu->build, p16 build->gpu),
two deadlocks over an hour; holding build during an arm starved other agents' builds for an hour (coordinator rule).

**How to apply:** `exec 9>gpu.lock; flock 9` in arm scripts, nothing else; build first in its own flock, then measure.

**Update 2026-10-26:** full protocol in /tmp/claude-1000/gpu-rules.md: timing work = `flock -x` + marker in
gpu.xwant.d, one arm per acquire; correctness work = wait for empty gpu.xwant.d, then `flock -s`, <15 min per acquire,
`free -g` >= model + 20 GB before loading. CPU-only work outside the lock.

**Update 2026-10-26 15:30Z — weight loads take the EXCLUSIVE lock.** Two global OOMs (14:20Z, 15:27Z; the second killed a
Flash Next prompt test with 80 GB shmem) took down claude-remote.service, i.e. this session and every agent, plus
prometheus/cloudflared/dashboards/rasdaemon. Cause: shared-lock correctness runs that load checkpoints raced past the
non-atomic `free -g` check. Rule: any run that opens a checkpoint registers in gpu.xwant.d and takes `flock -x`;
`flock -s` only for checkpoint-free runs (contract, synthetic sweeps). After an OOM: check rasdaemon/cloudflared/dashboards,
resume every agent (they all die with the session).
