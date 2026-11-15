---
name: model-archive
description: Download, checksum-verify, archive and reclaim model checkpoints on the GB10 — HuggingFace pulls with recorded provenance (hfget.sh/SOURCE.json), publisher-sha256 verification, and copy/verify/free against the Proxmox backup server at <pbs-host>. Use for any "download this model", "is this checkpoint intact", "where did this come from", "we need disk space" or "archive that" task.
---

# Model archive, checksums and remote download

Three rules, each paid for once:

1. **Verify checksums, not sizes.** A size-correct corrupt shard loads clean and emits fluent garbage
   that is invariant to every config change you try. The W4A16 "quant defect" was a zeroed layernorm
   from a truncated source shard, and we spent a day on the quantiser.
2. **Record provenance at download time.** We archived 30 checkpoints and could name the origin of
   **four**. `sha256` is an identifier, so three more were recovered by matching against HF `lfs.oid` —
   the rest are unknowable. Never invent a repo id to fill the gap; write `null` and say why.
3. **Verify before you delete, and re-verify at the moment of deletion.** Not with an hour-old check.

## Layout

| | |
| --- | --- |
| checkpoints | `/opt/llm/models/<name>/` — **hardlinked between variants**, so `du -sh` undercounts badly (a 126 GB dir reported 15 G). Use `du -shL`, or trust the `ls -la` link count |
| tools | `/opt/llm/runners/` (root, never committed): `hfget.sh`, `hfverify.py`, `hfidentify.py`, `write_source_json.py`, `arch*.sh` |
| archive host | Proxmox backup server `<pbs-host>`, `root` / `<REDACTED>` — dataset `/mnt/bulk/gb10/models` |
| archive list | `/opt/llm/runners/arch.list` — one directory name per line; every `arch*.sh` reads it and touches nothing else |
| ssh | key auth as `-i /home/jschmied/.ssh/id_ed25519`; root's own `/root/.ssh` is empty, so **always pass `-i`** |

## Downloading a model

**Ask the user before starting a large pull.** HF API metadata/size checks need no permission; bytes do.

```bash
/opt/llm/runners/hfget.sh <repo_id> /opt/llm/models/<dir> [revision]   # writes SOURCE.json + .aria.list
aria2c -i <dir>/.aria.list -d <dir> -x1 -s1
python3 /opt/llm/runners/hfverify.py <dir>                             # publisher sha256, file by file
```

`hfget.sh` pins the revision (resolves `main` to a commit sha first) and records, per file, the URL at
that sha, the size, and the publisher's sha256 — HF exposes it as `lfs.oid` on LFS entries. Use
`aria2c` at full speed (no cap since 2026-09-22), `-x1 -s1`, and the pinned `out=` names; `hf download` is not the tool
here. Run it **detached** (`systemd-run` or tmux): harness background shells die on session teardown.

## Checksums and provenance

- **HF publishes TWO hash kinds, and you need both.** `GET https://huggingface.co/api/models/<repo>/tree/<sha>?recursive=1&expand=1`:
  an **LFS** entry carries a real sha256 in `lfs.oid` (exactly what `sha256sum` gives); every **other**
  file carries a **git blob sha1** in the entry's top-level `oid` — `sha1(b"blob <len>\0" + content)`,
  i.e. `git hash-object <file>`. Recording only the first is why a 19-file repo verified "4 of 19" and
  left `config.json` and `hf_quant_config.json` unchecked. `hfget.sh` now records both and
  `hfverify.py` checks both (nvidia/Qwen3.8-27B-NVFP4: **19 of 19**, 4 by sha256, 15 by git-blob-sha1).
  Use `hfaugment.py <dir>` to backfill `git_blob_sha1` into a `SOURCE.json` written before 2026-09-09.
- Two HTTP calls diff two snapshots at shard level with no bytes moved — good for checking a published
  artifact against its own metadata, or an "identical" repo against a known one.
- **Unlabelled local directory:** `hfidentify.py <dir-with-SHA256SUMS> <repo>...` intersects local hashes
  with candidates' published `lfs.oid`. One matching multi-GB shard identifies the repo; zero excludes it.
- **`SOURCE.json`** (schema 1) is the record: `repository`, `revision` (pinned sha), `retrieved`,
  `provenance_note`, and `files[] = {path, size, sha256, url}`. `write_source_json.py` backfills one for
  a directory that never had it — reading only what is *in* the directory, leaving unknowns `null`.

## Pulling ONE tensor out of a remote checkpoint

HF's CDN answers byte-range requests (`206`, `accept-ranges: bytes`) and safetensors puts a JSON header
at the front giving every tensor's byte offsets. So a single tensor can be fetched **without downloading
the shard, let alone the checkpoint**:

```bash
/opt/llm/runners/hfpull_tensor.py <repo_id> <tensor-substring> <out.safetensors> [revision]
```

It reads `model.safetensors.index.json` to find the shard, range-fetches that shard's header, then
fetches only the matching byte ranges and writes a **new valid safetensors file** plus a
`.SOURCE.json` recording repo, pinned revision, and each tensor's origin shard and offsets.

Measured 2026-09-09 on `nvidia/Qwen3.8-27B-NVFP4`: `lm_head` is **682 MiB** inside a 1,879 MiB shard
inside a 19 GiB checkpoint; a 75.8 MiB scale tensor came down in **10.5 s**, byte-identical (sha256) to
the same bytes in the shard we hold on PBS. On our ~10 MB/s link that is the difference between 70
seconds and 3.5 hours.

**Limit:** it accumulates the fetched tensors in RAM before writing, so the pattern must select a
slice that fits — one layer of Flash-Next is ~7 GiB and fine; a pattern matching the whole
checkpoint would OOM. Fetch layer by layer for a full pass.

**When this matters most:** a question about one layer — does this checkpoint's head calibration differ,
is this tensor zeroed, do two repos share weights — never needs the whole checkpoint. Fetch the tensor,
answer the question, and download the rest only if the answer says to.

## Archiving and reclaiming disk

Four stages, in order, each with its own runner. Never collapse them.

| stage | runner | what it proves |
| --- | --- | --- |
| copy | `archive27b.sh` | `rsync -aH --partial`; `-H` because variants share inodes, `--partial` so a break resumes |
| manifest | `archverify.sh` | relative path + size for every file, hashed on both ends — **catches missing files, not corruption** |
| content | `archhash.sh` | a real `SHA256SUMS` inside every directory, both sides, compared. This is the check that satisfies rule 1 |
| free | `archfree.sh` | re-checks each directory immediately before its `rm -rf`, and aborts entirely if the host is unreachable |

Timings: local hashing ~1,567 MB/s (20 cores, ARM sha2) → ~4 min for 268 GiB. PBS reads at ~97 MB/s
(disk-bound, two-disk spinning mirror), so ~40 min — run the remote leg **detached on PBS**, not from here.

### How much does deleting a directory actually free?

Hardlinked variants share inodes, so deleting one directory frees only its files with link count 1:

```bash
find <dir> -type f -links 1 -printf '%s\n' | awk '{s+=$1} END{printf "%.1f GB unique\n", s/1e9}'
find <dir> -type f -links +1 -printf '%s\n' | awk '{s+=$1} END{printf "%.1f GB shared\n", s/1e9}'
```

2026-10-08: `qwen38-flash-next-fp8head` (123 GB by `du`) would have freed 11.6 GB; `mtpfp4-plebf16` (96 GB) freed
102 GB. The verify-then-delete runner for one directory: rsync -aH to PBS, sha256 every file on both sides, write the
sums to `/opt/llm/runners/SHA256SUMS-<dir>.txt`, `rm -rf` only on 0 mismatches (`tools/kolibri/drafter/
archplebf16.sh.txt`; for training outputs `backupclean*.sh.txt` with PROTECT and DROP lists).

## Traps, all of them paid for

| trap | symptom | fix |
| --- | --- | --- |
| `ssh` inside `while read` | loop verified **1 of 30** directories and printed "ALL OK" | `ssh -n` (it eats the loop's stdin) |
| `find … > SHA256SUMS.tmp` in the hashed dir | every manifest lists a file that does not exist; remote check FAILS on all | the redirect creates the target *before* `find` runs — write the tmp outside the directory, or exclude both names |
| page cache vs pinned memory | PLE worker dies `CUDA error: out of memory` while `free` shows 118 GiB **available** | ~105 GiB was page cache from the hash pass. `sync; echo 3 > /proc/sys/vm/drop_caches` before starting a server |
| `du -sh` on hardlinked models | 126 GB checkpoint reports 15 G, disk maths comes out nonsense | `du -shL`, or read the link count |
| PBS has no `rsync`/`aria2` | rsync fails on connect | `apt install rsync aria2` on the PBS side once |
| "4 of 19 verified" reported as success | 15 small files silently unchecked | non-LFS files hash as **git blob sha1**, not sha256 — record and check both (fixed 2026-09-09) |
| one page of the HF tree API | reported a 14.9 GiB PLE from a 387-file repo; the truth was 48.9 GiB | the tree API pages at 50 — always `?recursive=1`, and count what you got |
| deleting while a run is live | — | every `arch*.sh` waits for `fx-*` units and named runners to go idle first |

Related: memories `verify-checksums-not-sizes`, `hf-download-aria2c`, `ask-before-download`,
`long-jobs-need-detach`, `gb10-venv-hygiene`; skill `gb10-ab` (where server numbers come from).
