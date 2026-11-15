---
name: pbs-backup
description: The archive host at <pbs-host> — where bulk data lives, how it is organised, how to copy to it, verify it and restore from it, and what must never be written there. Use for "we need disk space on the GB10", "archive that", "restore X", "what is already backed up", "is the archive intact", or any capacity/retention question. Companion to `model-archive`, which owns downloads, provenance and hash formats.
---

# The archive host (Proxmox backup server, <pbs-host>)

`model-archive` covers **what** a checkpoint is and how to verify it. This skill covers **where it
goes**. Read both before a large sweep; they are deliberately non-overlapping.

## Access

```bash
ssh root@<pbs-host>          # hostname `pbs`; key auth, NO password needed
```

**As `jschmied`** the bare form works — `~/.ssh/id_ed25519` is the default identity. **As `root` it does
NOT**: `/root/.ssh` holds no private key, and bare ssh fails `Host key verification failed`.

> ⚠ **Anything run by systemd/qnext runs as root, so it MUST pass the identity explicitly:**
> `ssh -i /home/jschmied/.ssh/id_ed25519 -o StrictHostKeyChecking=accept-new`, and for rsync
> `rsync -e "$SSH"`. `model-archive` already said "always pass `-i`"; on 2026-09-12 I tested as
> `jschmied`, concluded it was over-strict, wrote that here — and the first archive sweep then failed
> rsync 255 on **12 of 12** directories. The original warning was correct. Test as the user the job
> will actually run as. Never put a password
on a command line — see memory `secrets-never-on-argv`.

## Where things go — and the one hard DON'T

| path | what | size (2026-09-12) |
| --- | --- | --- |
| **`/mnt/bulk`** | **our archive.** ZFS dataset `data/bulk` | 2.0 TB, **1.5 TB free**, 573 GB used |
| `/mnt/bulk/gb10/models/<name>/` | checkpoints we built or derived; each carries `SHA256SUMS` | 289 GB, 31 dirs |
| `/mnt/bulk/hf/<org>--<repo>/` | upstream HF repos at a pinned revision; each carries `SOURCE.json` | 284 GB |
| `/root/*.sh`, `/root/*.py` | the tooling (see below) | — |
| ⛔ **`/mnt/datastore/data`** | **the PBS deduplicating datastore.** `.chunks/`, `.lock`, `.gc-status`, owned by `backup`. **Never write loose files here** — it is a content-addressed store that PBS garbage-collects, not a filesystem. 6.2 TB free there is *not* ours to use directly. | 6.6 TB |

Naming: `gb10/models` mirrors `/opt/llm/models/<name>` one-for-one. `hf/` uses HuggingFace's
`<org>--<repo>` form (e.g. `Qwen--Qwen3.8-Flash-Next`, `nvidia--Qwen3.8-27B-NVFP4`). Keep both
conventions — a directory whose origin cannot be named cannot be verified or re-fetched.

## Tooling (lives on the PBS box, in `/root`)

| tool | does |
| --- | --- |
| `hfget.sh <repo_id> <dest> [rev]` | fetch an HF repo and write `SOURCE.json` with the **pinned revision** and per-file publisher hashes. Handles the tree-API pagination trap (see below). |
| `hfverify.py <dir>` | verify a directory against its `SOURCE.json`. Checks **both** hash kinds. |
| `hfaugment.py <dir>` | backfill `git_blob_sha1` into a `SOURCE.json` written before 2026-09-09. |
| `archcheck.sh` | sweep every dir in `gb10/models`, `sha256sum -c` its `SHA256SUMS`, write `/root/archcheck.log`. |
| `lasize.py`, `idxcensus.py` | header-only analysis of a staged checkpoint (no bytes read). |

`/opt/llm/runners/` on the GB10 holds local copies of the same tools. Neither location is a git repo —
**never commit these** (house rule: no `.sh` runners in repos).

## Capacity and link speeds — the numbers that decide plans

| link | speed | means |
| --- | --- | --- |
| GB10 ↔ PBS (LAN, `enP7s7`) | 1 GbE, ~110 MB/s practical | 100 GB ≈ 15 min; 570 GB ≈ 87 min |
| PBS → internet (HF) | **~60 MB/s (503–576 Mbit), FIXED 2026-09-12 ~19:40** | 475 GiB ≈ 2.2 h |

**WAN fault — found and FIXED 2026-09-12.** For a period the fibre synced at 500/250 Mbit but the
router's WAN **port** negotiated at 100 Mbit, capping everything at 10.52 MB/s. Reconnecting the WAN
restored it: measured 68.7 / 59.9 / 60.3 MB/s afterwards. Keep the diagnostic path — it is reusable:
TR-064 `GetCommonLinkProperties` gives the **line** sync (`NewLayer1DownstreamMaxBitRate`), which is
NOT the port negotiation; the FritzBox UI shows the port. Green Mode was ruled out (port was 2.5G
Power Mode/auto) and the link was not flapping (`ERROR_NONE`, 15 h uptime), which pointed at the
physical layer.

**Parallel connections never helped and still do not**: 200 MB took 19.0 s on 1 stream and 19.0 s on
8. `-x1 -s1` costs nothing. The old 6 MB/s house cap was working around *link saturation* of a
100 Mbit pipe, not line instability — with the port fixed it is obsolete.

**Two instruments that lie.** `GetTotalBytesReceived` is **uint32 and wraps** — add `2**32` to a
negative delta or you will report −582 Mbit/s. And **`du` cannot measure aria2 progress**: aria2
preallocates, so apparent size is full from the start (a disk delta read 0.0 MB/s while 60 MB/s was
arriving). Use the router counter, wrap-corrected.

| GB10 → internet | no cap (lifted 2026-09-22) | full line speed; PBS first when the download should also be archived |

**Restore beats re-download by an order of magnitude.** The 126 GB prod Qwen checkpoint is ~19 min
from PBS over LAN versus ~4.3 h from HuggingFace. That asymmetry is the whole reason to archive rather
than delete.

## Archiving (copy → verify → only then free)

```bash
D=qwen38-flash-next-fp8se
cd /opt/llm/models/$D && sha256sum $(ls) > SHA256SUMS      # manifest FIRST, at the source
rsync -a --info=progress2 /opt/llm/models/$D/ root@<pbs-host>:/mnt/bulk/gb10/models/$D/
ssh root@<pbs-host> "cd /mnt/bulk/gb10/models/$D && sha256sum -c --quiet SHA256SUMS && echo VERIFIED"
# ONLY after VERIFIED:  sudo rm -rf /opt/llm/models/$D
```

Rules, each paid for:

- **Verify at the moment of deletion, not with an hour-old check** (`model-archive` rule 3).
- **`du` undercounts hardlinked checkpoints badly.** `/opt/llm/models` variants share inodes:
  122.9 GB is hardlinked between `qwen38-flash-next-nvfp4` and `-fp8se`, so a parent-level
  `du --max-depth=1` reported the prod model as **15 G** when its standalone cost is **126 G**.
  Use `du -xsh <dir>` on the directory alone, and remember that deleting one of a hardlinked pair
  frees almost nothing while the other stays.
- **Run long transfers detached** (`systemd-run`/tmux): harness background shells die on teardown.
- **No heavy host IO while a measurement is running on the GB10.** A `du -x /` plus a `find` over
  `/opt/llm/models` coincided with the lowest KV sample of a 9-arm run on 2026-09-12. Check
  `systemctl list-units 'fx-*'` first.

## Restoring

```bash
rsync -a --info=progress2 root@<pbs-host>:/mnt/bulk/gb10/models/$D/ /opt/llm/models/$D/
cd /opt/llm/models/$D && sha256sum -c --quiet SHA256SUMS && echo RESTORED
```
For an `hf/` directory use `python3 /opt/llm/runners/hfverify.py <dir>` instead — it checks against
the publisher's hashes, which is strictly stronger than our own manifest.

## Verifying the archive itself

```bash
ssh root@<pbs-host> 'bash /root/archcheck.sh; tail -3 /root/archcheck.log'
```
Last full sweep **2026-09-09: 30 directories, 30 OK, 0 FAILED**. Re-run before relying on the archive
to free local disk, and after any bulk write.

## Traps this archive has actually hit

1. **The completion sentinel lies.** `/root/fnbf16.log` ends `== ALL DONE ==` while the line above it
   reads `aria2 rc=1` and `MISSING model-00038-of-00131.safetensors`, `143 of 144 verified, 1 bad`.
   **Read the verify line, never the sentinel.** Same failure as the aria2c that fetched 1 file of 6
   and exited 0 (memory `no-cause-without-counterfactual`).
2. **Checksums, not sizes.** aria2 preallocates, so a size-correct file can be absent or corrupt.
3. **HF publishes two hash kinds.** LFS files carry a real sha256 in `lfs.oid`; everything else carries
   a **git blob sha1** in the entry's top-level `oid`. Recording only the first is why a 19-file repo
   verified "4 of 19" and left `config.json` unchecked.
4. **The HF tree API pages at 50**, signalling more via the `Link` header. Fetching one page recorded
   50 files of 144 for Flash-Next — a third of a checkpoint that would have verified as complete.
5. **Provenance decays immediately.** On 2026-09-09 we archived 30 checkpoints and could establish the
   origin of **four**. Hence `SOURCE.json` at download time. Never invent a repo id to fill a gap —
   write `null` and say why.

## Current state (2026-09-12)

- `/mnt/bulk`: 573 GB used of 2.0 TB. Room for a full GB10 sweep with ~900 GB to spare.
- The archive is the **previous generation**: 27B variants plus `fnext-lh-experts`. **No directory in
  `/opt/llm/models` currently has a same-named copy on PBS** — nothing local is safe to delete yet.
- ⚠ **Known defect:** `/mnt/bulk/hf/Qwen--Qwen3.8-Flash-Next` is **incomplete** — 131 of 132 shards,
  `model-00038-of-00131.safetensors` missing. It is **not** a valid restore basis until repaired
  (~2.6 GB, ~4 min at the PBS link).
- Local `qwen38-27b-nvfp4` (22 GB) may already be archived as `hf/nvidia--Qwen3.8-27B-NVFP4` (19 GB)
  under the HF naming scheme. Compare by checksum before re-uploading it.

## Sizing a "free N GB on the GB10" request

GB10 disk is 916 GB total. Useful reference points measured 2026-09-12: `/opt/llm` 603 GB, of which
`models` 326 GB (dedup), `runtime` 102 GB (7 venvs, 9.6–17 GB each), `calib/capture` 91 GB,
`bf16-work` 52 GB; `/home/jschmied` 43 GB including two ~10 GB venvs. A full sweep keeping only the
prod checkpoint, the DS4.1 shards and the serving venv frees roughly **570 GB**.

Related: `model-archive` (downloads, provenance, hash formats), memories `verify-checksums-not-sizes`,
`hf-download-aria2c`, `ask-before-download`, `long-jobs-need-detach`, `secrets-never-on-argv`.

Update 2026-10-27: `hf/fishaudio--drama-3` @ b2b5ee99 (41.5 GB, 18 files, VERIFY_RC 0) is archived. It was downloaded with aria2c at about 65 MB/s, no speed cap; the house cap is gone. It is copied to the GB10 at `~/models/fishaudio--drama-3`.
