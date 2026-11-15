---
name: pinned-sweep-crashed-box
description: a sweep that allocates large PINNED arenas must be one-arena-per-PROCESS with an aborting pre-check; an in-process release-wait that times out and continues hard-reset the GB10
metadata:
  type: feedback
---

2026-09-19: job 1055 hard-reset the box. It allocated a 60 GiB **pinned** host arena, then a 60 GiB
device arena, on a 121.6 GiB machine. Pinned pages are unreclaimable and this box resets when
MemAvailable goes negative.

The guard I had written made it worse rather than better: an in-process loop that waited up to 40 s for
the previous arena to be released and then **continued anyway** on timeout. It looked like a guard and
was only a delay.

**Why:** freeing a large pinned tensor inside a running process does not reliably return the pages to
the OS on any timescale you can wait for, and `torch.cuda` allocations draw on the same DRAM pool on
GB10 — so two "sequential" arenas are concurrent in practice.

**How to apply:** for any sweep over large allocations — pinned especially —
1. **one arena per PROCESS.** Release becomes the OS's job at process exit, not the allocator's.
2. the pre-check must **abort**, never proceed on timeout.
3. cap each arena at ~40 % of MemTotal, and say in the write-up which sizes the cap made unreachable
   rather than quietly reporting a shorter sweep.

Related: [[gb10-oom-protection]] (cgroups cannot cap GPU allocations), [[gb10-source-build-oom]],
[[long-jobs-need-detach]].
