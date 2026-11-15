---
name: long-tasks-as-subagents
description: User preference - run long-running jobs (conversions, multi-step checks, downloads+verification) as subagents, not in the main thread
metadata:
  type: feedback
---

2026-10-14 (Ling port): "do long running tasks as subagents".
**Why:** long foreground runs block the conversation; the user keeps asking questions mid-turn.
**How to apply:** delegate bounded long work (quantization runs, layer-by-layer verification, benchmarks) to a
background Agent with a self-contained brief (paths, commands, acceptance criteria, what not to do); keep the main
thread for decisions and short checks. Related: [[subagents-for-fanout-not-for-the-thread]].
