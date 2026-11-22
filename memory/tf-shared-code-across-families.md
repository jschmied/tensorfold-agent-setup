---
name: tf-shared-code-across-families
description: "TF: BEFORE implementing, check what can be shared (core/lanes, across families AND Metal/CUDA); no per-backend copies"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-05T17:50:40.898Z
---

When the same optimization lands on several model families (a ledger row across columns), build it once in shared
code (core, lanes, shared native/CUDA loader, beside kv_pool) and have each family call it. If the existing version is
family-local, lifting it into shared code is part of the task. Metal and CUDA should call the same rule where possible.

**Why:** user, 2026-11-05: "for same optimization on several models, consider shared code" — said while ledger agents
were porting solo chunks / direct load / pooled recurrent state per family.

**How to apply:** put it in every ledger-cell agent brief; ask the report to name the shared file; tell mac-agent the
file so Metal reuses it. Related: [[tf-todo-elastic-memory]], [[tf-atc-standing-go]].

**Rule 2026-11-09 (user): "before implementation check for possible code sharing".** Every port/feature starts with a
sharing check BEFORE code: grep core/lanes and the other backend's (CUDA/Metal) and other families' version; list what
goes into core (config contract, checkpoint tensor list, table/host math, walkers, rules) vs backend-only (kernels,
device buffers). Put the list in the plan/brief and the PR body. Trigger: DSpine Metal #2634 duplicated CUDA's
71-tensor contract and TG-row formula (caught only after both PRs were up).

**11-16 again (#2460 item 4 claim):** a survey said "no core EOS check" while `core/tokenizer/eos.zig` existed; the user's outside review caught it after posting. Before claiming a core block, grep core/ recursively (subdirs like core/tokenizer/) for the concept, and list every reader's precedence/defaults; never propose a stricter rule (e.g. "template end must be EOS") without checking a served counterexample (hf_text 248044+248046).
