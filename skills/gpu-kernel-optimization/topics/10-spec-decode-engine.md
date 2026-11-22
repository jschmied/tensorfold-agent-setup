# Speculative-decode engines: where the time goes and which levers pay (cudafast 27B, 2026-10-30/31)

Source: the Yukon cudafast challenge, TF engine on Qwen3.8-27B (MLX affine-4 target plus a DFlash2 block-16 drafter, quantized to affine-4 at load).
Receipts are in `~/notes/cudafast/<item>/REPORT.md`. The score is prefill^0.25 × decode^0.75, and promotion needs ×1.02 over the record.

## The round budget (nsys, record a834106)
- Round 66 ms: target verify 59.9 ms (91 %), drafter 5.3 ms (8 %), GPU idle 1.3 %. Host and launch overhead is NOT a lever: graph/ found 0.37 % idle, and a CUDA graph per target round is already in place.
- **Decode is a round count.** One round ≈ 3 % decode for 128 tokens. A tree change that saves 1 of 30 rounds is worth more than any kernel left.
- Projections already stream at 235–252 GB/s. The practical ceiling of a pure copy is **231–241 GB/s** (see 02), so verify headroom is ~3–5 % (verify/, bw/).
- Verify at 16 rows costs only +1.6–2 ms over 2 rows: M ≤ 16 reads the weights once.

## Levers that paid (officially, on the private prompts)
1. **Better 4-bit fit of the drafter at load time:** least-squares refit of the affine-4 scale and bias per group, alternating "assign codes" and "fit the line", 3 → 8 passes. That gave **+1.2 % official**, at zero runtime cost: the engine quantizes the bf16 drafter at load anyway.
   - We MISSED this. Our dq/ A/B showed an 8-bit drafter gives +3.4 % tokens/round (precision buys acceptance) but costs +61 % drafter time. We closed it as "q4 is the cheap arm" instead of asking how good the q4 fit was.
   - **Rule:** when a precision A/B shows acceptance moving, test fit quality at the same width before closing.
   - A lower weight error can still hurt acceptance (paulobrien's ulp-neighbour search scored worse), so judge by rounds, not error.
2. Small launch-shape tweaks (shared-memory stage room for the 16-row output stream, `gdn_pre` 4 rows per block, 32-row stream twins): +0.3–0.8 % each.

## Levers that did NOT carry over: the local-workload trap
- **edge_weight 0.6 → 0.85** (predecessor-edge weight in the best-first tree): +6.8 % local decode on the public longcopy seed (ABBA×2, goldens pass) → **+0.25 % official**. Both official pairs decoded at the record's speed.
- The offline sim had said so: the generic prompts gained only +0.5 %. Most of the public-seed gain came from copy-style continuation.
- **Rule:** for tree, policy or acceptance knobs, rank by the generic prompts, never by the public seed. Only gains that are prompt-independent (drafter speed or accuracy on all text, target cost per round, prefill) carry over to a private benchmark prompt.
- Scale 1.35 (sharper chance softmax) is the same kind: +3.1 % local, not submitted.

## The offline acceptance simulator (build it first)
- Recorder (`TF_RECORD`): replace every drafted node with a never-chosen token, so each round commits only the bonus token and the drafter runs at every tape position. Log per position:
  - the rows' top-k ids and raw unary logits;
  - the edge sums per predecessor;
  - the target's top-8.
- The replay (`~/notes/cudafast/oracle/sim.py`) reimplements the tree and the copy chain and walks the fixed greedy tape.
  - Validated against the live engine round for round (264/264 accepted lengths).
  - Recomputing chances from the raw logits reproduced the logged chances to ≤ 0.001.
- After that, every tree and policy idea is a minutes-long CPU sweep. The GPU is only for goldens and the final A/B.
- **Dense-information trap:** a sim that uses drafter outputs at every position knows more than the live engine (which only drafts at round starts). A "−1 round" residual-correction win vanished in the live-faithful version (resid_live.py). Make the sim use only what the live engine has.

## Tree findings (closed)
- Best-first over calibrated drafter probabilities is already expected-optimal for a fixed node count. Its own probabilities are calibrated (0.86 → 0.88, 0.47 → 0.53, …).
- No gain from any of these:
  - branch above 8; child cap 12 vs 16;
  - a top-32/64 shortlist (as many wrong competitors as rescues);
  - kind-aware penalties;
  - token recycling;
  - pure prompt lookup; copy pointers; copy grafts; two or three copy branches.
- **Bigger trees lose live** even when the sim saves rounds:
  - 23 nodes: −2.8 % decode; 31 nodes: −5.4 % (verify rows cost more than the saved rounds);
  - the sim counts rounds, not round cost, so screen node-count changes live.
- A "miss faster" path is not possible: a rejected round costs the same as an accepted one. Skipping the drafter on predicted misses is worth ≤ 0.5 %.

## Engine items measured and closed (bound first, all < the 1–2 % bar)
| item | result |
|---|---|
| dequant once per prompt (deq/) | dequant ALU 5–8 % of the prompt GEMM, L2 already serves the reuse; two-pass bf16 scratch no gain |
| exact lm_head pruning for argmax (math/) | Cauchy–Schwarz bound prunes 0 %; low-rank + residual 0.34 % |
| L2 prefetch of o/out in glue gaps (math/) | null |
| prefill last layer on a 128-row tail tile (math/) | prefill −1.0…−1.3 %, kept |
| GDN wide k-major projections (gdnmb/) | 0.34 ms < 2 ms bar |
| drafter attention K/V reuse (waste/) | microbench −19 %, in-model null (latency-bound, 33 % occupancy) |
| target attn_one smem 64 → one tile (waste/) | −0.55 %, superseded by paged attention |
| projection access patterns / cp.async (bw/) | null; 240–250 GB/s whatever the pattern |
| prefill idle gaps (nsys/) | 0.86 ms per 87 ms pass = 1 % → ~0.25 % score; the "5 ms gaps" were the serial leg (see 03) |
| Nemotron carry-overs (drafter head partial-K, L2-resident drafter) | head 0.3 ms/round (< 0.5 %); drafter weights ≫ 24 MiB L2 |

## Competition process rules
- **List the pending submissions before every submit:** same idea in flight? Could one promote first and raise the bar? Validation takes ~11 min median.
- Coarse first (1 run or ABBA×2), many runs only for survivors. Three classes: clearly negative = drop; −1…+1 % = archive as undecided; reproducibly positive < 2 % = keep for stacking.
- Read the field's notes (`yukon submissions --all --json`, `.submissions[].note`) before choosing a lever. If three solvers are tuning one knob, pick an orthogonal lever.

## What the field's 263 submissions taught (2026-10-30 18:00 → 10-31 18:30)
16 promotions took the score from 1.80 to 2.59 in about 24 h. 101 more submissions improved the score but fell short of the bar (mostly +1.3…+2.0 %), and 120 did not improve. The levers that won:
1. **Fewer bytes per round, losslessly, at load time.** This is the biggest class, and we had it closed wrongly as "formats, not ours".
   - **Dictionary-coded scales and biases** (ercumentyildirim, kshitij-hash): +2.4 %. Affine-4 g64 stores a bf16 scale and bias per 64 weights, i.e. 4 B per 32 B of codes, 11 % of the bytes. A model has few distinct values, so a short index plus a table re-encodes them bit-exactly.
   - **GDN keep folded into the next verify's slot scan** (fkiene): removes one 151 MB state read per round, +2.1 %.
   - **Rule:** before "at the byte floor", count metadata bytes and redundant state reads, and ask whether a lossless re-layout at load removes them. The original packed bits stay authoritative; the view is derived at load.
2. **Prefill GEMM work:** grouped same-input projections in one launch, fused prompt MLP, inner-loop addressing hoisted (+2.0 %), and the kept-row prompt tail (the last layer runs only the row whose logits are kept).
3. **Launch shape:** programmatic dependent launch (PDL) through the glue, split GEMV for narrow projections, cluster-tile decode, 16-/32-row stream kernels, and row-pair tensor-core attention for verify windows.
4. **Drafter:** branch 12, a least-squares affine-4 refit, and tap gathers.
- **How promotions happen:** most promotions are compositions. A crown plus one or two other solvers' near misses (each +1.3–2 %) clears ×1.02 together. We never composed the field's near misses; we only tried new ideas alone.
- **Failures** (15) were setup or GPU-measurement step failures, not correctness. Keep a submission's setup identical to the record's.

## The earlier Nemotron 3.5 Lightning 30B-A3B challenge (1575 submissions, 1.32 → 2.76), receipts `~/notes/cudafast/NEMOTRON-CARRYOVER.md`
- The same class won there: **lossless load-time re-encoding of bytes.**
  - fp8c, a 7.19-bit lossless code for the FP8 Mamba projections;
  - 6-bit NVFP4 block-scale planes.
- **GB10 generic memory compression** (`cuMemCreate` with `CU_MEM_ALLOCATION_COMP_GENERIC`) on immutable weights gave +1…+5 % per kernel, but only for families whose bytes compress (codes, scale copies, fragment planes). On 27B affine-4 weights it was ~1 % slower. Screen per weight family, and keep a byte-compare check plus a fallback.
- **Exact activation sparsity:** relu² gives exact zeros, so the down projection reads only nonzero rows ("zskip"). This applies only to relu² models.
- A partial-K screen of the head plus a full-K rescore gives an exact argmax. It pays only when the head is a large share of the cycle (2.7 of 25 ms there, 0.3 of 66 ms on 27B).
- Two more items:
  - Running only the logits row in the prefill's last layer won independently in both challenges.
  - Draft-depth gating by cumulative acceptance also won there; TF main already has `core/draft_depth.zig`.

## Verify attention, draft length by context, acceptance per depth (added 2026-11-22)
- **Verify rows must run on the decode attention kernel.** Sending k-row verifies to the prefill kernel made the
  step grow 3.5 ms per 1K context (47 → 104 ms at 16K). Check which kernel our verify rows hit at long context
  (nsys kernel names at 1K vs 16K vs 64K) before tuning drafts.
- **Best draft length moves with context and concurrency.** Theirs: 1 draft beat 3 at 128K (29.6 vs 15.5 tok/s)
  while 3 won short; k=4 at c1, 3 at c4, 2 at c16. Our nspec sweeps were short-context: sweep long context too.
- **Measure acceptance per depth.** One MTP head accepted ~14 % at depth 2, so its best was one draft.
Source: sybil-solutions/inference-optimisation-skill (MIT, read 2026-11-22), their measurements on Intel Arc/Apple, not ours: priors, not facts on the GB10.

## Draft length and prompt splits (added 2026-11-22)
- GLM MTP: one draft beat the default three, 66-68 → 75.7 tok/s (playbook SD-11). Sweep 1 first on MTP heads.
- Flash Next hybrid GDN cache: a non-canonical token split of a resent prompt re-read 30-54K tokens; compare the
  prefix by text, not token IDs (playbook 11).
Source: alesha-pro/inference-optimization-playbook (MIT, read 2026-11-22; RTX 3090 sm_86, many single runs; their exactness = token match or logit tolerance, not ours). Priors, not GB10 facts.
