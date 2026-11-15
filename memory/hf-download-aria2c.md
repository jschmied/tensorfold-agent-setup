---
name: hf-download-aria2c
description: "For HuggingFace model downloads on the DGX/GB10 box use aria2c (not hf download); NO bandwidth cap -- the ~6 MB/s limit was lifted 2026-09-22, run every download at full speed"
metadata: 
  node_type: memory
  type: feedback
---

For HuggingFace model downloads on the DGX/GB10 box, use **`aria2c`**, not `hf download` (which has been flaky here). **Run at full speed — no bandwidth cap.**

**Why:** `hf download` stalled/regressed repeatedly; aria2c gives resumable transfers.

**The bandwidth cap is GONE (2026-09-22, user: "speed limit for any download is gone").** It previously stood at ~6 MB/s to stop transfers starving the box's shared unified-memory/IO. It applies to **any** download, not only HuggingFace — LAN pulls from the backup box included. Do **not** pass `--max-overall-download-limit`, `--bwlimit`, or any other throttle unless the user asks for one in the moment.

Still in force, and unaffected by this: get an explicit go-ahead before starting a large pull ([[ask-before-download]]).

**How to apply:**
- Single connection per file — HF's Xet CDN rejects aria2 multi-range ("Invalid range header"): `aria2c -c -x1 -s1 -j1 --split=1 --max-connection-per-server=1 --auto-file-renaming=false --allow-overwrite=true -d DIR -i INPUT`
- Use an aria2 input file pinning `out=<filename>` per URL, or the CDN redirect saves shards under a content hash and vLLM/llama can't resolve them by the names in `index.json`.
- Pull small config/tokenizer files with `hf download --exclude "*.safetensors"` first, then aria2c the big shards from `https://huggingface.co/<repo>/resolve/main/<file>`.
- Run detached so it survives session teardown — see [[long-jobs-need-detach]]. Documented end-to-end in `appendix/vllm-switch.md` A.2.

## `aria2c url1 url2 …` is ONE file from many mirrors, not many files (2026-09-12)

Passing six shard URLs on the command line fetched **only the first**, treating the rest as mirrors
of it, saved it under the Xet CAS hash name (no `-o` to force one), and **exited 0**. A job wrapper
of the form `aria2c … && echo done` therefore reported success. Nothing was broken; the command
succeeded at the wrong thing.

For N files use an **input file**, one URL per line with an indented `out=` under each:

```
https://huggingface.co/<repo>/resolve/main/model-00002-of-00048.safetensors
  out=model-00002-of-00048.safetensors
```

then `aria2c -i that.file -d <dir>`. Verify afterwards by **counting the files you asked for**, not
by the exit code — and by `lfs.oid` sha256, never size ([[verify-checksums-not-sizes]]).

Public HF repos need **no Authorization header at all** — check `gated`/`private` first
([[secrets-never-on-argv]]).

2026-10-27 (user, again: "there is no download cap anymore"): the leftover 6M hints were removed from the model-archive and pbs-backup skills and from hfget.sh's printed aria2c line (PBS /root and /opt/llm/runners), so no tool suggests a cap any more.
