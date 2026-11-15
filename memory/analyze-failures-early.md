---
name: analyze-failures-early
description: "on long benchmark runs, triage each failed instance as it completes and act immediately — never wait for the batch to finish"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-16T17:44:32.208Z
---

On long benchmark/eval runs, diagnose **every failed instance as it completes** and take corrective
action mid-run. Do not accumulate failures and analyse them at the end.

**Why:** twice on the 2026-08-16 SWE-bench run, batching the analysis cost hours. A whole 46-instance
eval finished before I noticed 18 empty patches were a harness bug; then ~75 minutes of a rerun
elapsed before I checked whether the "fix" was even applied — it was a no-op. A single instance
inspected at first completion would have caught both. Related: [[swebench-marker-bashenv-bug]],
[[swebench-docker-cache-confound]].

**How to apply:**
- Wire per-instance triage into the monitor so each failure is classified the moment it lands, and
  separate **scaffold** failures (discarded submit, infra, timeout) from **model** failures
  (never submitted, genuine loop). `/root/triage.py` on the x86 box does this.
- On the FIRST failure of a new kind, stop and inspect it before letting the batch continue — a
  systematic fault repeats across every remaining instance.
- Verify a fix is actually in effect (assert the observable changed), not merely applied. A config
  override that duplicates an existing default changes nothing.
- Run `/root/preflight-swebench.sh` before launching, so known faults cannot silently return.
