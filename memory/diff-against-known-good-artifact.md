---
name: diff-against-known-good-artifact
description: "Open the artifact before theorizing about it — a PR description, a release note or our own producer-side check is not the thing itself"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-10T19:33:06.440Z
---

When building a file another program consumes, and a **working third-party version of that file
exists**, diff our output against it — every scalar, not just shapes — **before forming any theory
about why ours misbehaves.**

**Why:** 2026-09-10 I shipped an NVFP4 rebuild with two producer/runtime contract violations —
`input_scale` written as `amax/6` instead of `amax/(6*448)` (448× off, 73,728/73,728 values wrong),
and gate/up not sharing one `weight_scale_2` (24,357/24,576 experts, median 1.22× and up to 3.18×,
which vLLM silently discards by applying the gate scale to both halves). I then produced **three
wrong diagnoses in a row** — "packer exonerated", "calibration-set overfitting", "Local-Hessian is
broken" — and burned ~5 hours of GPU on two full 48-layer rebuilds chasing them. The user found both
defects by reasoning about the *consumer's* contract; confirming them against RadixArk's checkpoint
took 90 seconds.

Every check I had built compared our output to **our own intent**: name/completeness checks,
per-tensor sha256 against *our* files, and a reconstruction test that decoded each matrix with *its
own* scale. A wrong convention passes all of them by construction. I had even opened the reference
checkpoint's header — to read shapes — and never compared a value.

**How to apply:**
- Before theorizing about misbehaviour, run a **field-by-field diff against the known-good artifact**.
  Twenty lines, seconds. Values, not just shapes and dtypes.
- **Read the consumer's code path for the fields you emit**, not just the one you're currently
  debugging. I was inside vLLM's loader for hours on file *selection* and never read what it does
  with the *scales*.
- Never say "component X is exonerated" from a test that only covers part of X. A reconstruction
  match validated the E2M1 encoding and said nothing about `input_scale`; over-generalizing it is
  what redirected the whole investigation.
- **When a hypothesis fails, retreat to fundamentals rather than escalating to a bigger one.** v2
  getting worse made me blame the most sophisticated component; the actual signature — every internal
  metric improving while behaviour worsened — points at systematic export error, not calibration.
- A verifier must test the **consumer's contract**, not the producer's self-consistency. See
  `mergeverify.py` LEVEL 1.5, added after this, and exercised against the known-bad build so it is
  proven to fire.

## The same mistake with a *third-party* artifact (2026-09-11, det-208)

`REPRODUCE.md` told the public for 11 days to pin FlashInfer **0.6.17**, because flashinfer#4757's
description says it removed SM121a from the aarch64 JIT-cache arch list — "you lose the prebuilt
cubins, fall back to JIT, OOM". I wrote that from the PR description. **Opening the two wheels took
four minutes and refuted it:** neither 0.6.17 nor 0.6.18 ships any sm121 file, and `cuobjdump`
reports the identical 17 `sm_120` ELF kernels in the NVFP4 GEMM in both. There were never any cubins
to lose. The pin then *cost* us: vllm#55715 asks for ≥ 0.6.18, so our own recipe read readers out of
a working kernel, and we ran the Triton fallback for every GDN layer (1,216/1,216) for weeks.

Immediately after, I blamed a 13-minute server start on the version-scoped autotune cache. Also
wrong: 11:20/12:01 on 0.6.17 vs 11:54 on 0.6.18 — ~12 min is just what loading 123 GB costs. Two
wrong causal stories in one hour, both from reasoning about a mechanism instead of measuring it.

**How to apply:** before writing a version pin or a "do not upgrade" into anything public, open the
artifact — `ls` the wheel, `cuobjdump` the .so, diff the two installs. And before attributing a
duration to a cause, time the same thing under the other condition; the comparison is usually one
`grep` over a log we already have.

Same family as [[search-open-prs-before-fixing]] and [[check-field-before-expensive-steps]]: the
cheap external reference beats the expensive internal derivation, and I keep relearning it.
Related: [[verify-checksums-not-sizes]], [[analyze-failures-early]].
