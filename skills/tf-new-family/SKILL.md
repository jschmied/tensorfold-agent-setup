---
name: tf-new-family
description: Bring a new model family (or a new backend for one) up in TensorFold end to end — field check and claim, sizing per box, download with provenance, a clean-room reference oracle, TF's own recipes, the correctness gates that caught real bugs (teacher-forced top-1, tie rule, cross-prompt resume, multi-row layouts), device fan-out and the PR. Use before starting or briefing any new-model or new-backend work in TF, and to look up which gate a family still lacks.
---

# A new model in TensorFold, end to end

TF's own docs own the engine side; read them first, every time (they change):
`docs/recipes/SKILL.md` (contributor contract, kernel registration, engine contracts, evidence),
`docs/recipes/adding-a-family.md` (MLX), `docs/recipes/adding-a-cuda-family.md`, the closest existing family
recipe in `docs/recipes/`. This skill is everything around them that we kept rebuilding by hand
(ASR #2239/#2250-2255, Inkling 2 Mini C1-C4 + #4640, LFM3 #1508/#1634/#1838).

## 0. Before any code

1. **Field:** open AND recently closed PRs/issues for the model name, `atc board` / `atc check`, ashhart's lead
   branches (`lead/<family>`; e.g. #4387 is "our own Mini line": contributors target it, not main). If ashhart
   started a host, build on it (he told HIP: "build on #4387's host rather than start a second H1").
2. **Claim** per the ATC skill; one claim per issue.
3. **Shared code first** (memory `tf-shared-code-across-families`): grep `core/`, `core/lanes`, other families and
   the other backends for every block you'd write (tokenizer, EOS, KV, experts, GEMV, drafter). List core vs
   backend-only in the plan and the PR body.
4. **Only shippable work** (memory `only-shippable-work`): every device the PR claims must be testable by us
   (GB10 CUDA, mac-agent Metal, wsl-agent Iris Xe) or by a tester who agreed first.

## 1. Size it per box

| box | budget for weights + KV |
|---|---|
| GB10 | ~110 GB unified (keep 20 GB free for the dispatcher's mem check) |
| mac-agent M3 Pro | ~28 GB |
| wsl-agent Iris Xe | ~5 GB (7.6 GiB WSL RAM) |

Write the table into the plan: which checkpoint (and quant) runs on which box. A box that can't hold it is a
device the PR can't claim.

## 2. Weights

`model-archive` skill: ask the user before a large download; `hfget`-style pinned revision + `SOURCE.json`;
verify against publisher hashes (`hfverify.py`), never sizes. Disk floor 40 GB: swap others to PBS first
(`pbs-backup`, main session only).

## 3. The reference oracle (clean-room)

- We may **run** the publisher's own package or the model card's reference as a black box. We never **read or
  port** another engine's code (vLLM, SGLang, llama.cpp, mlx-lm, Transformers, ktransformers, ModelOpt).
- Run it in fp32 (fp64 where cheap), CPU if needed, `python3 -I` from an empty cwd, downloaded code read first.
- Record per case: the token ids (greedy), the top-2 logits and their margin at every step, and stage taps if the
  package exposes them. Store under `~/notes/<family>/ref/` with SHA256SUMS; these are the fixtures.
- A float64 host reference inside TF (`<family>-ref` test, e.g. `tf-cuda-test inkling2-mini-ref`) is the second
  oracle: cheap, on every head.

## 4. Correctness gates (each one caught a real bug)

| gate | what | caught |
|---|---|---|
| teacher-forced top-1 | feed the reference's ids, compare our top-1 at every step; report N/M and the first divergence | Inkling 58/64 → 64/64 after the messages-layout fix (#4640) |
| **tie rule** | a swap is allowed only where the reference's own top-2 margin is ~0; any other differing token fails | ASR #2239: 2-3 swaps per 1,342 steps, all exact ties |
| stage taps / cosine per layer | find the first layer that drifts | Inkling visit 18 cos 0.98 → 0.9999 |
| **multi-row prompts** | prompt chunks of rows > 1, not only one row; writer and reader layouts must agree | Inkling messages written `[row][core][role]`, read plane-major: fine at 1 row only |
| greedy + seeded served equality | hash reasoning **and** content, fail on empty (memory `served-gate-hash-reasoning`) | content-only hashes passed on "" (#1503/#2989/#1508) |
| resume == fresh, multi-turn | turn 2 from cache == fresh | |
| **cross-prompt resume** | prompt B resumes from prompt A's cached prefix, then A resumes: == fresh | KV copied row-major into head-major caches: answered the other prompt (CUDA #4640, Metal #4542) |
| concurrency | c=1/4/8 == solo; a stream past capacity refused before anything is queued | |
| kernel contract | every kernel registered, planted control per kernel red then green, 0 limit problems | XPU `asr_gemm` spill and fp16 threshold (#2255) |
| refusals | unsupported quant/flag refused by name, test proves nothing was queued | main's blanket `--vision` refusal broke XPU LFM3-VL (#1838) |

Plant at least one fault per gate (`--plant ...`) and show it red in the body.

## 5. Speed

`gpu-kernel-optimization` skill. A-B-B-A, paired, min-of-N, final head only. There is no "slower than main" for a
family main can't run: the rule protects what main already serves, so for shared kernels show SASS identity of
the existing entries; report the new family's numbers as absolute.

## 6. Devices and PR

- Metal/XPU checks: `device-handoff` skill.
- GPU jobs only through the dispatcher (`~/notes/jobs/README.md`); prio 25 for user-prioritised families.
- PR: `tf-pr` skill (evidence defaults, `pr-ready.py`, which checks against the PR's base branch, e.g.
  `lead/inkling2-mini`). One concern per PR; speed PRs after the correctness PR.
- After any rebase: `~/notes/watch/rebase-gates.py`.

## 7. Ledger

`~/notes/ledger/<family>/STATUS.md` (one line per event, heads and job ids), a board card per running agent
(`spark-board`), receipts under `~/notes`, never only in /tmp.
