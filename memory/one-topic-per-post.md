---
name: one-topic-per-post
description: "Upstream posts carry one topic each — one issue/PR/comment per finding or proposal, never bundled"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-01T06:21:04.808Z
---

One topic, one issue (or PR, or comment). Never bundle unrelated findings or proposals into a single upstream post.

**Why:** 2026-10-01, I proposed folding an opt-in W4A4 question into the same TensorFold issue as the prefill
findings (per-window bottleneck, FP8-prompt numbers); the user: "dont mix topics in posts, one topic, one issue".
A mixed post makes the maintainer answer several things at once and lets one topic stall the others.

**How to apply:** when drafting upstream text, split by topic before writing: each draft file in
`notes/upstream/` covers exactly one question or change, with its own evidence. Related topics may link to each
other by number once posted. Applies to PR scope too (one change per PR). See [[upstream-post]] skill,
[[posting-check-thread-state-first]].
