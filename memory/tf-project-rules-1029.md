---
name: tf-project-rules-1029
description: TensorFold rules re-read 2026-10-29 (AGENTS/CONTRIBUTING/docs/recipes/SKILL.md): no rebase under review, contract-runner reachability, full no-gpu CI set, ATC claim before work
metadata:
  type: reference
---
Re-read on 2026-10-29 from origin/main. The last rule-file change was CONTRIBUTING.md on 10-26 (dev-tools). These are the points that bind our work:
- **Rebase:** "Maintainers rebase at landing, so don't force-push a branch under review just to follow main" (docs/recipes/SKILL.md). See [[tf-rebase-only-on-request]].
- **Stacks:** one job per PR; stack dependent PRs, say what each sits on, keep stacks short.
- **Authorization:** creating an issue, sending a PR or uploading results needs the user's authorization.
- **New GPU kernels:** each must be reachable through the CUDA contract runner (zig/tests/cuda/contract_tests.zig) with gates and planted controls, not only a unit test. Records also go in registry.zig. The PR posts the backend's full SUMMARY line, plus `kernel-contract-limits` over the 5-SM fatbins.
- **No-GPU CI set:** `zig build test test-kernel-contract test-golden test-server-security test-pull-security fuzz-cortheon`, `git diff --check`, lean_new = 0, and a plain `zig build`. v.sh was extended to run these on 2026-10-29.
- **Code limits:** source files at most 600 lines; comments are single lines of at most 120 columns.
- **ATC:** check or claim the issue and start a session before editing, and run `atc overlap` before the PR. See [[tf-atc-standing-go]].
- **Identity:** noreply identity, no co-author trailers.

**2026-11-06 (#2263 landing):** a Metal source embedded verbatim lands in `tensorfold-native`; a comment containing "/..." or a `*.zig` name trips `check-release-paths` (zig/build/release_paths.zig). Run `zig build check-release-paths` when a PR embeds shader/kernel source text. ashhart fixed it himself (a5f1f0836). #2229 merged 2026-11-06.
- 2026-11-10 (ashhart #1660, #2739): NO token-changing speed mode, even opt-in — `--profile fast` won't ship; only
  `fast-exact` (token guard solo/conc 1-8/resumed equal to `stable`, no served cell slower; memory cost OK if stated).
  Ideas from other engines may be bounded, but code is written from our own code + the model's definition, never
  read from or ported from another engine (clean-room).
