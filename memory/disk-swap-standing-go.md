---
name: disk-swap-standing-go
description: Standing go (2026-11-05) to swap models off the GB10 to the PBS archive to free disk — verify both sides first, log in ~/notes/disk-swaps.log
metadata:
  type: feedback
---
User 2026-11-05: "swap models to free disk as needed". I may delete local model copies when disk nears the 40 GB floor,
and restore them from PBS when needed, without asking each time.

**Why:** disk hit the floor with four agents building; asking per model stalled work.

**How to apply:** only after the archive copy is verified at deletion time (hfverify.py for hf/ dirs; sha256 both sides
for gb10/models, and write SHA256SUMS to PBS if missing), names+sizes match, and `lsof +D` / queued jobs show no user.
Log each swap in ~/notes/disk-swaps.log. First swap: kolibri-1 + Bolt-E4B-BF16, 40 → 126 GB. See pbs-backup skill.

**2026-11-08 (user): "resource management should be done by main job".** Only the main session swaps, restores or
deletes models and plans disk/GPU memory. Subagents never do: they ask the main session (SendMessage) for space or
a model, with path, size and until when. Main checks every queued job + all ledger files + lsof, then swaps.
**Why:** the kolibri-dspark agent swapped the 35B MTP model kv-p3 was using (17:08) → q1-conf failed, then the
model had to be restored. Agents only see their own task. Put "no swaps; ask main" in every agent brief.
