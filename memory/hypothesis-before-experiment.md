---
name: hypothesis-before-experiment
description: "Before ANY experiment, write the hypothesis and the expected parameter RANGE. If the outcome falls outside the range, debug the measurement before interpreting it — never report an out-of-range number as a result"
metadata:
  type: feedback
---

**User instruction, 2026-09-23:** *"before any experiment note a hypothesis with expected parameters
range. if outcome does not fit, debug"*.

**Why, from the run that prompted it.** Job 70 reported **66.8 tok/s at c=16** and I passed it on as a
number. Our own record has **156 tok/s at c=16** ([[flashnext-concurrency-scaling]] /
`flashnext-fp8mix-checkpoint`). The user caught it in one line — *"c16 just 66? thats really bad"* —
and the debug found two defects of mine: the prompts file carried `approx_tokens` from the parent
conversation (10.6k) while the text was only the last user turn (~1.6k), and `schedwidth`'s
`aggregate` is `completion_tokens / wall` over a **prefill-dominated** window, not a decode rate at
all. **With a written expectation of "~150-160 tok/s" the 66.8 would have tripped an alarm instead of
becoming a reported result.** Nothing else in the pipeline was going to catch it.

**How to apply:**
- Before starting a run, write into the job file / the finding stub: **the hypothesis, the expected
  range, and what instrument produced the reference number**. One or two lines is enough.
- Derive the range from our own prior measurements where they exist, or from a bandwidth/roofline
  bound where they do not. Name the source.
- **Outcome outside the range is a bug report about the measurement, not a finding.** Debug the
  instrument first: is it the metric I think it is, does its denominator include what I think, are
  the inputs the size I think.
- A range also protects the opposite error: an outcome *suspiciously good* is equally a debug
  trigger ([[acceptance-is-not-quality]], and the 2.20x "win" that was an L2-resident artefact).
- This composes with the existing bar, it does not replace it: ranges/disjointness across starts
  decide whether an effect is real; the hypothesis decides whether the number is even the right
  quantity. Related: [[no-cause-without-counterfactual]],
  [[check-field-before-expensive-steps]], [[verify-guards-on-empty-output]].
