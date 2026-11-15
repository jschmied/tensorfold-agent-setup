---
name: write-short-by-default
description: "Default to SHORT for answers and upstream posts — the user has repeatedly had to ask ('tldr if possible', 'short and on point'); apply the ladder without being told"
metadata:
  type: feedback
---

The user keeps having to ask for brevity after the fact. Stop making them ask.

**Why:** they read these on a terminal and paste the posts into GitHub threads. Length is a
cost they pay, not a signal of effort. A long answer that had to be re-requested short wasted
both passes. Modelled on the `ponytail` skill (github.com/DietrichGebert/ponytail), which does
this for code — "the first lazy solution that works is the right one"; this is the prose
version.

**How to apply — stop at the first rung that holds:**

1. **Does it need saying at all?** Already established in this conversation or that thread →
   cut it. Never re-explain what the other party just wrote.
2. **One line before a paragraph.** A verdict beats a narrative.
3. **Table before prose** for anything with more than two data points.
4. **Result before method.** Method only if it is contestable or must be reproducible.
5. **Cut the process story.** Which command failed, how many attempts, what I considered and
   rejected — none of it belongs unless it changes what the reader does next.
6. Only then write the rest.

**Never cut** (these are the "input validation" of prose): a correction to something I said
earlier; a caveat that changes a decision or a number's scope; the AI-assistance disclosure on
upstream posts; and the line between measured and assumed.

**Length is earned, not default.** Go long only when the user asks, or for an upstream
technical report where a maintainer must reproduce the result — and even then, table first,
traces second, prose last. If I catch myself writing a section header for a two-sentence point,
it should have been a sentence. See [[posting-check-thread-state-first]] for the other
pre-post reflex.
