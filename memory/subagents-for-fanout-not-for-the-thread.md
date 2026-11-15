---
name: subagents-for-fanout-not-for-the-thread
description: "Use subagents freely for bounded fan-out research; keep the engineering work in one thread, because the best results come from cross-topic links a fresh agent cannot make"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-12T10:40:20.761Z
---

Decided with the user 2026-09-12, after they asked whether a manager + fresh-subagent-per-topic
split would cut the error rate.

**Subagents: yes, and use more of them — for bounded fan-out research.** A fixed question, wide
search, no shared state needed. Two that day both landed well: the DeepSeek landscape survey (found
V4.1-Flash published two days earlier, and vLLM #56461 saying it cannot serve on SM120/121), and the
0xBakeer repo assessment (**caught that the repo had moved seven commits past the head we were
briefed on**, superseding three items — which the main thread would have missed). Give them the
user's own context verbatim when they have it, ask for sources, and tell them to prefer "not found"
over guessing.

**The engineering work stays in one thread.** The day's most valuable results were all cross-topic
links a per-topic agent structurally cannot make:

- GB10's 100 KiB shared-memory ceiling (det-217) → explained det-222's engine kill → explained why
  vllm#55872 fails on sm_121 → became the upstream report. Four "topics", one chain.
- A Marathi-for-Hindi output from the Devanagari hunt → became the lead argument that 0xBakeer's new
  free-generation gate cannot catch fluent-wrong output.
- det-208's wheel measurement → the RadixArk recipe correction.
- `verify-checksums-not-sizes` → caught aria2 preallocation faking download progress the same day.

**Why:** the user's diagnosis (long, topic-mixed chat) fitted only 3 of ~13 errors that day. Ten came
from [[no-cause-without-counterfactual]] and would recur in any context. Isolating topics would have
cost every link above and fixed almost none of the errors.

**How to apply:**
- Fan-out research, competitor/upstream surveys, "what exists now" questions → subagent.
- Anything whose value depends on remembering an unrelated measurement → main thread.
- Do not use a subagent to *avoid* holding context; use it to avoid dumping search output into it.

Related: [[skills-daily-loop]], [[check-field-before-expensive-steps]].
