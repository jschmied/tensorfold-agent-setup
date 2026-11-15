---
name: skills-daily-loop
description: The four procedure skills in ~/.claude/skills (gb10-ab, venv-overlay, upstream-post, model-archive) — what each covers and when to invoke it instead of re-deriving the procedure
metadata:
  type: project
---

Four skills in `~/.claude/skills/` hold the recurring procedures of the Flash-Next work, each with a "traps paid for" section:

- **`gb10-ab`** — server-level A/B on the GB10: runner layout, standard cold/warm arms, the readiness/path-line capture,
  probes (`ttft.py`, `ttft2.py`, `agentloop2.py`), stop-and-drain, recording as a numbered finding.
- **`venv-overlay`** — putting a branch/PR/patch onto a serving venv and taking it off: which venv, backups, drift check,
  envs.py entry, pycache purge, test-before-serve, removal in reverse order.
- **`upstream-post`** — posting protocol: re-read the thread, draft file, permalinks, disclosure, secret scan, posting log.
- **`model-archive`** (added 2026-09-09) — downloads, checksums and disk: `hfget.sh`+`SOURCE.json` provenance, publisher
  sha256 via HF `lfs.oid` (works without downloading), and the copy/manifest/content-hash/free ladder against the PBS
  archive at <pbs-host>. Its traps: `ssh -n` inside `while read`, the `> SHA256SUMS.tmp` self-listing manifest, page cache
  starving a pinned allocation, `du -sh` lying about hardlinked checkpoints.

**Why:** the night of 2026-09-04 lost four runs to procedure (root-git, eval quoting, stale test copy, silent fallback,
stale preflight after a module split), none to kernel bugs. **How to apply:** invoke the skill before starting the
procedure, not after the run fails; add every new trap to the skill the same session.

- `drafter-training` (2026-10-10): new target -> tap probe, draft vocab, data, train_block recipe flags, scoring gates, GPU-pause receipts, export, specbench, HF release; box rules. Recipe text: notes/upstream/tf-recipe-training-a-drafter.md.
