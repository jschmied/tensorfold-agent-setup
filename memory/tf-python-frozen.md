---
name: tf-python-frozen
description: "TensorFold's Python engine is FROZEN (2026-10-06, ashhart on #211) — no Python PR merges; future is the Zig engine"
metadata:
  node_type: memory
  type: project
  modified: 2026-10-06T06:22:57.191Z
---

2026-10-06 ashhart on TensorFold #211 (https://github.com/ashhart/TensorFold/pull/211#issuecomment-6010578121): "The
Python engine is frozen (#286), so this won't merge." The native Zig engine (branch `zig-preview`, `ZIG-PREVIEW.md`;
Metal first, CUDA = Nemotron MLX 4-bit from the command line only, Flash Next port on `zig-flashnext`) is the future. Our
FP4 x FP4 expert kernel (#211) comes across to Zig CUDA under `--precision checkpoint` with credit when Flash Next
NVFP4 serves there.

**Why:** all our open Python PRs (#211, #303, #304, #318, #327, #328) and the planned Kolibri drafter PR cannot merge.
**How to apply:** don't write new Python-engine PRs for TensorFold. Kolibri + drafter live on our fork
(`jschmied/TensorFold:kolibri1-cuda` / `kolibri1-drafter`). Upstream path = Zig (Kolibri family port once Zig CUDA serves
Flash Next) — ask the user before investing. Zig house rules match ours: drafted == `--no-drafts` byte-identical, bf16
activations / fp32 accumulation, files <= ~600 lines. Related: [[tf-kolibri-drafter-hf]], [[kolibri-drafter-plan]].

**2026-10-06 later:** our RFC #443 (Zig native CUDA server + family registry) was accepted in shape: ashhart made our
commit the base of their Zig CUDA serving branch (GB10 + RTX PRO 6000), keeping the registry; they add --device /
--segments, fail-closed admission, /metrics, exactness receipts; statx reviewed separately; closes on landing. So the
Kolibri family's upstream path is a `families/kolibri1/cuda_native.zig` adapter on that registry, once their branch lands.
**MERGED 2026-10-06 18:42Z:** #443 is in `zig-flashnext` as our commit 59e77e8f4 (merge 7742ddd3b); ashhart built a
dozen commits on it unchanged. Our next Zig piece is the drafter interface (`jschmied/TensorFold:zig-drafter-interface`,
rebased on 7742ddd, unposted — needs the user's go).
**Zig lean rule (2026-10-07, ashhart on #455):** every comment and docstring ONE line and <=120 columns (file headers too), files <600
lines; `tools/zig/lean_check.py` checks it (run it on our files before pushing). Upstream comment lines: median 101,
max ~165 characters; trailing field comments carry detail.
