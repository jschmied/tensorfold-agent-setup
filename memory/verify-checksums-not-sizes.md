---
name: verify-checksums-not-sizes
description: Verify HF downloads with lfs.sha256, never file size; a size-correct corrupt shard produces fluent garbage that is invariant to every config change
metadata:
  type: feedback
---

**Verify model downloads against HuggingFace's published `lfs.sha256`, never against file size.**
Size agreement proves only that the right number of bytes were allocated — and aria2 preallocates,
so a file reaches full size the instant it starts. Never delete `.aria2` control files to "clean
up": that destroys the resume state that would otherwise catch a truncated file.

```bash
curl -s "https://huggingface.co/api/models/$REPO/tree/main?recursive=true&blobs=true" \
  | jq -r '.[]|select(.lfs)|"\(.lfs.sha256)  \(.path)"' > SHA256SUMS
sha256sum -c SHA256SUMS
```

**Why:** on 2026-08-27 this cost a full day on Qwen3.8-Flash-Next. 2 of 206 files were
size-correct and byte-corrupt (`model-bf16-00011`, `model-plefp8-00000`) — exactly the two in
flight when the download stalled, whose control files I had deleted after checking only sizes
against the HF API (418/418 "matched"). The failure mode is near-perfectly disguised:

- it **loads** — no error, sane shapes, sane dtypes, correct-magnitude activations
- the output is **fluent** token salad, so it reads like a sampling/template bug
- it is **invariant to every configuration change**, because it is a property of the weights —
  which reads as an environmental or kernel fault and sends you hunting through cudagraph modes,
  executors, backends and drivers. 20+ clean eliminations each made the wrong answer look
  better supported.
- corruption in **both** the body and the PLE defeated the one good control (the body-vs-PLE
  split was the right experiment; both halves were damaged)
- it **survives naive content checks**: PLE vs the official BF16 table gave cosine 0.999635,
  because I sampled row 0 — inside the intact head of the corrupt file.

**How to apply:** checksum immediately after any large pull, before any experiment. When a
symptom is invariant to every configuration you vary, treat that invariance as evidence for
**data corruption**, not for an environmental cause — and re-verify the inputs before opening
upstream issues. Two issues here had to be retracted. Sample content checks at several offsets,
not offset 0. See [[ask-before-download]], [[hf-download-aria2c]],
[[check-field-before-expensive-steps]].
