---
name: tf-shared-kernels-simple-optimal
description: "Rule (user 2026-10-25): TF shared CUDA/Metal kernels are as simple and fast as possible; never keep a family's old summation order or other legacy restrictions just for byte-equality"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-25T09:58:53.930Z
---

User 2026-10-25: "shared kernels should be as simple and optimal as possible without keeping unnecessary restrictions".

**Why:** Each family's reduction order is arbitrary. TF's real constraints are only these:
- the order is invariant to load and layout (drafted == plain, concurrent == solo, chunked == whole, resumed == fresh, paged == contiguous);
- within a model, the paths a gate compares agree;
- the error stays inside the f64 bound.

Byte-equal-to-main is a cheap no-bug proof, not a correctness need. Per-family template knobs that reproduce old orders turn a shared kernel into N copies behind one name.

**How to apply:**
- Design: shared kernels get one canonical order per shape class (head dim, dtype). Make them as fast as possible per arch. Only keep a parameter if it is needed for speed or correctness, never to mimic a legacy kernel.
- Migration: a family migrating onto them accepts a one-time byte change, gated on its own gates + f64 bounds + logit distance to reference no worse than main + chat/needle + speed within noise. Each step stays a separate commit.
- Never change OTHER families' bytes or SASS by editing a shared kernel in place. Add a new variant or migrate that family deliberately.
- Ashhart's acceptance was asked on #548 (comment 6396212387, 2026-10-25). If he requires byte-equality, follow his rule for upstream PRs and note the conflict to the user.
- Lossy activation formats stay banned ([[tf-exact-arithmetic-choice]]). Related: [[tf-atc-process]].
