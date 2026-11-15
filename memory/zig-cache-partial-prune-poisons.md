---
name: zig-cache-partial-prune-poisons
description: deleting zig-local/o entries alone poisons the cache (FileNotFound, not a rebuild); wipe whole dir under both tfb slot locks; v.sh now exits nonzero on any failed step
metadata:
  type: feedback
---
2026-11-05: hourly.py pruned `~/.cache/zig-local/o/*` older than 2 h. The `h/` manifests still named them, so the next
`zig build` trusted the cache hit and failed `FileNotFound` (7 ci errors on #2239 and the Metal branch, code was fine).
And v.sh printed `ci RC=1` but exited 0, so the dispatcher logged DONE rc=0.

**Why:** a cache "miss" is only a rebuild when the manifest goes too; a half-deleted cache is a false failure.
**How to apply:** prune = `mv` the whole zig-local away while holding BOTH tfb slot locks (`flock -n` on
tfbuild.lock and tfbuild.1.lock), else skip. Read verify step lines, not the job rc — v.sh now ends `verify BAD=0|1`
and exits with it. Related: [[gb10-job-dispatcher]], [[verify-guards-on-empty-output]].
