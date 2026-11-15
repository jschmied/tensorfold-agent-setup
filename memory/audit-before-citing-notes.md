---
name: audit-before-citing-notes
description: "chronological findings files hide supersessions; before citing one publicly, check the cited finding and its forward references — the 2026-09-24 audit found ~180 of ~600 claims wrong as written"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-09-24T08:00:26.478Z
---

On 2026-09-24 the user asked me to check whether notes/determinism-investigation.md holds, right after I had
cited it on vllm#55122. Eight read-only auditors, one per line range, found about 180 of about 600 claims that did
not hold as written:
- early hypotheses overturned a few entries later with no marker at the original spot;
- "stock" arms that ran the det kernel (`FN_DET_TOPK=0` is truthy);
- pseudo-replicated p-values;
- stale upstream state.

Two of our public comments carried such errors, including the one I had just posted: the k3dani attribution in
det-235 was confounded.

**Why:** a chronological lab notebook is correct at write time and wrong by accretion. A reader who lands on an
anchor link sees the old claim, not the correction 40 entries later.

**How to apply:**
- Before quoting or linking a finding publicly, grep the file for later references to it (its id and keywords)
  and re-read the raw data behind any number.
- When a finding is superseded, put a marker at the ORIGINAL location, not only in the new entry.
- For large audits the pattern that worked:
  - fan-out auditors by line range, each given the post-hoc facts;
  - they return JSON patch ops `{line, match, op, text}`;
  - one anchor-checked apply script, dry run first;
  - review every marker before writing.

Related: [[no-cause-without-counterfactual]], [[verify-guards-on-empty-output]], [[finish-before-posting]].
