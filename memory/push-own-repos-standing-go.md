---
name: push-own-repos-standing-go
description: Standing go (2026-09-13) to push OUR repos and OUR fork branch after every commit; upstream posts still need a per-post go
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-13T17:48:18.115Z
---

The user gave a standing authorisation on 2026-09-13: **"push it after any change"**, in the context
of the DS4.1 fork branch. So do not sit on commits waiting to be asked.

**Covered — push without asking, after every commit:**
- `~/git/deepseek-moe-gb10` → `origin main` (our analysis notes and tools)
- `~/git/qwen38-flash-next-gb10` → `origin main`
- `~/git/deepseek-v41-flash-spark` → `origin feat/cb3-disk-cache` — this is **our own fork**
  (`jschmied/deepseek-v41-flash-spark`), not 0xBakeer's.

**Not covered — still needs an explicit go for each one:**
0xBakeer's repo, any pull request, vLLM/SGLang issues or PRs, HuggingFace. The
[[upstream-post]] protocol is unchanged: "post it" applies to the draft named, not the next one.

**Never push our fork's `main`** — it must stay exactly on upstream `8b68fdd` so the feature branch
reads as a clean delta.

**Why:** the work was piling up locally and the user had to ask whether it was even committed. A
commit nobody can see is not a deliverable. Secret-scan still runs before every commit
(`git grep -nI -E "sk-[A-Za-z0-9_-]{16,}|hf_[A-Za-z0-9]{30,}|<REDACTED>|BEGIN [A-Z ]*PRIVATE KEY"`),
and `.sh` runners still never get committed.

**How to apply:** commit, scan, push, and say the branch and hash in the report. Related:
[[secrets-never-on-argv]], [[commit-after-tests-green]].
