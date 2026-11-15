---
name: tf-throttle-new-fronts
description: "TF PR limit REMOVED 2026-10-13 — post finished, verified work without capping how many of ours are open"
metadata:
  type: feedback
---

2026-10-13 user: "post all ready and remove PR limit". The earlier rule (2026-10-11: no new TF claims while ~3+ of
ours await review) is lifted; that day #796, #797, #798 went up beside open #734 and #746.

**Why:** ashhart merges in batches (1.0.9 took #730, #731, #733, #736 at once), so a queue of finished PRs is fine.
**How to apply:** open a PR as soon as it is verified (tests, mutations, receipts, lint) and the user says post;
still never post without the user's go, still one topic per PR ([[one-topic-per-post]]), still search open PRs for
duplicates first ([[search-open-prs-before-fixing]]).
