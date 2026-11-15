---
name: long-jobs-need-detach
description: "On the GB10 box, run long downloads/installs detached (systemd-run/tmux) — Claude Code background shells die on session teardown"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-17T21:53:41.475Z
---

Long-running commands on the GB10 box (model downloads, `pip install vllm`, etc.) must be launched **detached from the Claude Code session** — either `sudo systemd-run --unit=NAME --uid=llm --gid=llm ...` (then follow with `journalctl -u NAME -f`) or inside `tmux`.

**Why:** harness `run_in_background` shells are children of the Claude Code process; when the session/shell tears down (observed repeatedly this session — "shell logged out"), those jobs are killed with no completion record. `systemd-run` transient units and tmux survive it.

**How to apply:** for any job expected to run more than a few minutes on this box, prefer `systemd-run` as user `llm` over `run_in_background`. Bonus: HF's Xet CDN rejects aria2 multi-range — use `aria2c -x1 -s1 -j1 --split=1` with an input file pinning `out=` names, or shards save under a content hash. Related: [[qwen36-dflash-deployment]].

**⚠️ aria2 hangs AFTER the last byte on the Xet CDN (seen 2026-08-17).** The file was
byte-complete against the HF API size, yet aria2 kept running with the `.aria2` control file in
place and no further traffic. **Its exit code is therefore not a completeness signal.** Never gate a
pipeline on `rc == 0`:

```python
def complete(path):            # Header-Ende gegen echte Dateigroesse -- NICHT nur keys()
    import json, os, struct
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        hdr = json.loads(f.read(n))
    end = max(v["data_offsets"][1] for k, v in hdr.items() if k != "__metadata__")
    return os.path.getsize(path) == 8 + n + end
```

**`safe_open` + `keys()` is NOT a completeness check** — it parses only the header at the
FRONT of the file, so a file truncated at the end passes. Cost of getting this wrong
(2026-08-18): a quantization build streamed a short shard, safetensors mmapped past EOF
and returned **zeros**, and one zeroed layernorm silently broke the whole model — see
[[w4a16-rebuild-attempt]].

Run aria2 under `subprocess.run(..., timeout=N)`, then check `complete()`, delete a leftover
`.aria2`, and retry once. Cost of not doing this: the job hangs alive-but-idle, and a monitor that
only greps for success stays silent — add explicit **stall detection**, threshold above the normal
per-file time (a 4 GB shard at our 6 MB/s cap takes ~11 min, so 10 min cries wolf every time).

**And `pkill -f <pattern>` kills your own shell** when the pattern appears in your command line —
hit three times in one session. Use `pgrep` into a variable, then `kill` explicit PIDs.
