---
name: tf-1353-ruling
description: ashhart rulings on same-precision reorders (#1353 10-27, #1409 10-28 10:35Z FINAL) — pure move = identical SASS; deliberate reorder = own PR, judged vs float64 + placebo, behavioural checks exact
metadata:
  type: project
---
2026-10-27, on #1353: the placebo argument won. Reversing one existing fold on main moves the float64 error, the argmax misses and the teacher-forced loss as far as #1353/#1354 do. The bar for a same-precision reorder is now "not worse beyond noise", as on #796:
- paired per-class differences, prompt and decode separately, within noise after correcting for the number of classes;
- teacher-forced loss within noise;
- a placebo as the yardstick.

Keep the shared kernels' single order.

**Still open (reviewer-requested, so the standing go applies):**
1. The prefill slowdown of 1.1–1.8 % must go: fuse the combine back into `add_rms_h` for prefill. ashhart will A/B on a GB10.
2. Restore the `+1e-20` zero guard and add an all-underflow top-k test.
3. Open an issue about main's row 162, layer 18, column 2206 (52.5 where float64 gives −1.18), with how it was found: prompt, passage, position.

Branches: #1353 shared-nemotron-1 (00f267241), #1354 shared-nemotron (worktree ~/git/tf-548).

**Why:** this sets the precedent for every same-precision reorder PR, and it unblocks the #548 shared-kernel series.

**How to apply:** cite it in future reorder PRs. Gates are paired, noise-corrected comparisons plus a placebo, not worst-column checks.

**Update 2026-10-28 (ashhart, #1353 04:10):** for #548 step 1 the bar is now **the same tokens as main**: each new launch must match main's `tf_nemo_*` kernels (embed16, add_moe_norm, concat_norms, group_rmsnorm) on real layer inputs. "Not worse beyond noise" no longer suffices here. Decode must also be level with main. Their GB10 run on head 76ab46f02 measured −7.6 % decode at 1 stream on Lightning, against our +0.5 % measured on an older main.

**Update 2026-10-28 10:35Z (ashhart, #1409) — supersedes the 04:10 "same tokens as main" for deliberate reorders.** The bar for later parts of the shared-prims work:
1. Pure moves and refactors: identical SASS, shown with the #1440 tool.
2. Deliberate order change at the same precision: its own PR plus a changelog line saying replies change. Judged against float64, not main: paired per-class differences, prompt and decode separately, class-count corrected; teacher-forced loss within noise; a placebo reorder of main as the yardstick. Say so where it is closer to float64.
3. Behavioural checks stay exact: repeats, drafted == plain, concurrent == solo, resumed == fresh.

Never lower a precision, never slow a served cell. All 20 `warp_sum` copies are one butterfly, so they move as pure moves. The real order variants are `block_sum`, `inv_rms` and the activations.

**2026-10-28 afternoon: we reached byte-equal tokens, not the reorder path. Replies are posted.**
- **Root cause:** the strided reduction order in the norms.
  - The group norm summed 8 contiguous elements per thread plus a tree. Main strides by 128.
  - The MoE residual added ((r+s0)+s1) where main adds r+(s0+s1).
  - The step 2 top-k used `expf` where main uses `tf_sigmoid`.
- **Fix:** `norms_strided.cuh` carries main's order.
- **Result:** Lightning and Bolt match main 21/21 rows and 8/8 chats. Super-VL is untested; the box doesn't have it.
- **The −7.6 % decode was from different tokens, not kernel time:** 75 vs 63 rounds.
- **Heads:** #1353 `8e1115e05`, #1354 `e6e217b7d`.
- **Lesson:** a reorder that changes tokens can lose speed through drafting (fewer accepted tokens), so "no served cell slower" can force byte equality anyway.
