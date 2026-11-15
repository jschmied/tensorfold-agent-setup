---
name: search-open-prs-before-fixing
description: Before bisecting a shared symptom and again before opening a fix PR, search OPEN PRs by touched-file basename and by the symptom in plain words AND identifiers; we duplicated vllm#55375 (opened the evening before our bisect) because we searched issues only, with "state_indices" while the PR said "state index strides"
metadata:
  type: feedback
---

2026-09-05: a full day's bisect of the MTP multi-prefill corruption (findings 126–131) ended in PR #55467, which duplicated
#55375 (peakcrosser7, opened 2026-09-04 17:51, same two loads, same stride fix, already approved). We had searched issues
for symptoms, and PRs only once, with terms ("Flash-Next mixed batch", "state_indices stride") that matched neither the PR's
title ("fix state index strides in fused PLE conv") nor its body ("multiple prefill requests", "Qwen4Exp", "PLE").

**Why:** GitHub search does not split identifiers — `state_indices` never matches "state index"; and a symptom shared by
several reporters (#55357 had 4 comments) is likely to have a fix in flight already. The user asked "why didn't we find this
open PR?" — the cost was a duplicate PR and an avoidable share of the bisect.

**How to apply:**
1. Before starting a bisect of a symptom others report, and again before opening a fix PR:
   `gh pr list -R vllm-project/vllm --state open --search "<file basename>"` for every file the fix would touch, plus
   `--search "<model name> <symptom in plain words>"` and the same with identifiers; sort by newest.
2. Read the newest 5 titles fully — a match is usually within the last 3 days for a hot model.
3. If a PR exists: put the evidence there, do not open a second one (that is what we did after the fact, and it was welcomed).
Related: [[check-field-before-expensive-steps]], [[posting-check-thread-state-first]], [[mtp-multi-prefill-corruption]].

**Third instance (2026-09-06):** the FLA fused kkt+solve port (finding 143, branch ready, PR body drafted) duplicates
vllm#38315 (ZJY0516, open since 2026-03-27, stale). Found only when the user said "post pending" and the pre-post search ran.
Cost: a day of porting that upstream had already done, plus the maintainer's verdict on it ("within measurement error on
B300, FlashInfer's backend is faster") was on record and would have changed the plan. Search `gh pr list --state open
--search "<plain words>"` AND `--state closed` **before the port**, not before the post; include stale PRs — they hold the
maintainers' stance.
