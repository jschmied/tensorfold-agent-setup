---
name: check-field-before-expensive-steps
description: "Before any expensive step (prod-down boot, source build, multi-hour download, benchmark sweep), check the field FIRST — and check OUR OWN recorded results too: 2026-09-11 a 48-layer rebuild was started for a number already in nll.jsonl"
metadata:
  type: feedback
---

**Check what others have published before spending hours.** Not after, not "while it runs".

**Why:** on 2026-08-26 the Flash-Next field produced four repos in twelve hours, and two
findings landed *while our download ran* that changed the plan:
- `sglang#36537` (thinking + tools → token-0 `!!!!!!` loop) reordered the experiment list —
  the tool-calling test is now worth more than any throughput number.
- 0xBakeer's page-cache measurement (100% cached after warm → **0.1% after one benchmark
  pass**) undercut the mmap residency plan outright, and reframed MiaAI's ~11 GB pinned PLE
  as a deliberate hot-set rather than a staging buffer.
Both would have been discovered *after* burning a prod-down boot cycle. See
[[flashnext-prior-art-llamacpp]] and the repo's `notes/the-field.md`.

**What counts as expensive:** anything that takes prod down, a source build, a download over
~10 GiB, a benchmark sweep needing an exclusive box, or a measurement arm requiring a server
restart (~10 min each on this hardware).

**How to apply:**
1. `gh api repos/<r> --jq .pushed_at` on the tracked repos + a `gh search repos` sweep.
2. Read any commit whose subject touches the thing about to be spent on.
3. Ask: does this make the step unnecessary, or change what it should measure?
4. Only then spend.

Also applies to upstream issues/PRs, where the same thing happened: #53435 merged overnight
and changed whether prod's branch-venv pin was still needed. Corollary of
[[posting-check-thread-state-first]] — same reflex, applied to work rather than words.

## It applies to our own results too — 2026-09-11

Started a 48-layer rebuild (~50 min, and it cost a deleted `blk` checkpoint) to measure
per-expert plain max on the 59-passage NLL set, having written in the notes that this was
"the one measurement still owed". It was not owed. The `pmax` arm had been built *after* the
contract fix, its passages *did* include Devanagari, and all three arms were already scored
paired in `/opt/llm/runners/results/nll.jsonl`. The user asked "why build again?" and the
answer, on reading our own file, was: no reason.

**Why:** an unchecked sentence in my own notes ("still owed") was trusted over the results
file it was describing. Notes drift; the jsonl does not.

**How to apply:** before rebuilding or re-running *any* arm, query the results store for that
arm name and read what it already contains — `jq`/`collections.Counter` over the arm field
takes seconds. Ask specifically: was this arm built before or after the last correctness fix,
and which groups did it cover? Both were checkable in one command here, and both came out the
opposite of what I assumed. See [[diff-against-known-good-artifact]] for the same reflex
applied to artifacts rather than measurements.

## It applies to NEGATIVE claims too — 2026-09-11

Wrote "DeepSeek-V4.1-Flash on one Spark? — no" by comparing published checkpoint sizes
(386–491 GiB) against GB10's 119.2 GiB. The user produced
[0xBakeer/deepseek-v41-flash-spark](https://github.com/0xBakeer/deepseek-v41-flash-spark), which
serves it at full FP4 quality: hot 25.6 % of routed experts resident in a 73.8 GB arena, the rest
streamed off NVMe with `O_DIRECT`. 2.68 tok/s, 0.92 GB read per token, 0.83 hit rate.

**Why:** size-vs-memory is a **capacity** argument. Residency is a **cache** argument. Worse, I had
already made the cache argument in the same note for the model's 189 GiB engram tables and failed to
carry it to the experts.

**How to apply:** before writing "X does not fit / cannot be done", search for someone doing X — a
`gh search repos` on the model name costs seconds. Negative claims feel safe because they need no
measurement; that is exactly what makes them cheap to get wrong. Same author is behind the PLE mmap
trick we ported the same day ([[flashnext-prior-art-llamacpp]]), so the source was already in our
notes.
