---
name: gb10-ab
description: Run a server-level A/B of a Flash-Next change on the GB10 (vLLM serve as systemd fx-* units, single and concurrent TTFT probes, warm-turn agent loop), then record the result as a numbered finding. Use for any "does change X help at the server" question on Qwen3.8-Flash-Next; also to READ how a server number was produced.
---

# GB10 server A/B — Flash-Next

The unit of evidence in this project is **a server number with two starts per arm and the path line
from the log**. Standalone kernel numbers do not count (finding 113/114: an L2-resident standalone
misranked the tile, and a silent fallback produced a fake A/B). Everything below exists to make the
next run land on the first try; every trap listed was paid for.

## Layout

| | |
| --- | --- |
| serve script | `/opt/llm/serve-fnmain.sh` — knobs via env: `FN_VENV`, `FN_CACHE`, `FN_MODEL`, `FN_SEQS`, `FN_MAXLEN`, `FN_BATCH`, `FN_UTIL`, `FN_MTP`, `FN_SPEC_METHOD`, `FN_SPEC_N`, `FN_SPEC_NODROP`, `FN_EXTRA` (extra vLLM args, one string) |
| runners | `/opt/llm/runners/*.sh` (root, **never committed** — they may carry secrets); results in `/opt/llm/runners/results/<name>.txt` |
| probes (client venv `/opt/llm/runtime/vllm-venv-fnext/bin/python`) | `ttft.py <label>` (7,503 / 29,263 tokens, 3 requests, median); `ttft2.py <label>` (two prompts fired together, 8k+8k and 30k+8k); `agentloop2.py <label>` (8 dependent turns × 130 tokens, needs MTP + prefix cache) |
| serving venvs | `vllm-venv-fnmain2` (nightly dev401 + overlay; the branch validation venv), `vllm-venv-fnmain`, `vllm-venv-preview` |
| checkpoint | `/opt/llm/models/qwen38-flash-next-fp8head` |
| notes | finding → `notes/prefill-investigation.md` (or `determinism-investigation.md`), raw file copied to `notes/data/<name>.txt` |

Standard cold arm (what every TTFT number in the notes uses): `FN_SEQS=2 FN_MAXLEN=32768 FN_BATCH=4096
FN_UTIL=0.80 FN_MTP=0`, `FN_EXTRA="--language-model-only --kv-cache-memory-bytes 2147483648
--no-enable-prefix-caching"`. Warm arm: same plus `FN_SPEC_METHOD=mtp FN_SPEC_N=3 FN_SPEC_NODROP=1`
and no `--no-enable-prefix-caching`.

## Queue: `qnext` advances it by exactly one job

`tools/qnext.py` (at `/opt/llm/runners/qnext.py`, queue at `/opt/llm/qnext/queue.json`). Not a
scheduler — the queue was never what failed, the *timing* was: read-out crons set on a wall clock
fired before a run finished twice, and three fired after the work was already done.

```bash
python3 /opt/llm/runners/qnext.py --status     # what is next, and why the rest is not
python3 /opt/llm/runners/qnext.py --dry-run    # plus the exact command it would run
sudo python3 /opt/llm/runners/qnext.py         # claim ONE job, run to its sentinel, record, exit
```

- Refuses while any `fx-*` is live (`*-dl` excepted — downloads are not GPU work), and holds a lock.
- **`needs_user: true` never auto-starts**: prod changes, downloads, upstream posts.
- An item runs only when every `prereq` is `done`.
- **Completion is the job's own `== ALL DONE ==` / `== VOID ==` sentinel, not elapsed time.** A job
  that exits without either is recorded **`unknown`** and never silently `done` — the first real run
  hit exactly that, an `rm` that failed on root-owned files.
- One job per invocation; the watchdog tick calls it again. **Run it as root** — jobs touching
  `/opt/llm/runtime` need it.

## Use `armrun` — do not hand-write another driver

`tools/armrun.py` (installed at `/opt/llm/runners/armrun.py`) takes the arms as a JSON spec and owns
everything that used to be copied. Thirteen hand-copied drivers produced five defects in one day —
a probe on port 8080 when the launcher serves 8092, a void marker that matched in both states so the
A/B compared prod to prod, a `sys.exit` that skipped cleanup and orphaned a server, a control that
forced a flag and so took a different branch than the default it was meant to reproduce, and a
docstring splice that shipped a syntax error.

```bash
python3 /opt/llm/runners/armrun.py spec.json --validate-only   # ALWAYS first: nothing is started
sudo systemd-run --unit=fx-armrun --collect python3 /opt/llm/runners/armrun.py spec.json
```

What it enforces, so you do not have to remember it:

- **Port 8092 is a constant**, not a default copied from a neighbouring file.
- **Void checks are declared per arm** (`log_must_contain`, `log_must_not_contain`) and are evaluated
  *before* any number is read. A failing check exits **2** and the arm's numbers are unusable.
- **Markers are validated**: a `source_toggle` whose marker reads the same with the patch on and off
  is refused, because it can witness nothing. It also refuses when the target file is not writable,
  rather than reporting that as a marker problem — as a non-root user the patch script fails quietly
  and both states look identical.
- **Cleanup is in `finally`**: the unit is stopped and source toggles restored even on VOID.
- `env_unset` for a control that must take the **default** branch; setting the flag explicitly is a
  different code path.
- `expect_wrong` on a control arm; a control that does not reproduce marks the run VOID.
- Ranges, not means, and a `== ALL DONE ==` / `== VOID ==` sentinel for the queue.

Run `--validate-only` first, always. A marker test that skipped it launched a real server.

## The runner, step by step

1. **Preflight** (each a hard exit with a line in the results file): no `fx-*` unit active; `/swapfile-fnext`
   in `/proc/swaps` (the PLE offload worker is OOM-killed without it); the change actually present in the
   venv (`grep` for a symbol **in the file where it lives now** — after a module split this check silently
   went stale and failed a run).
2. **Arms alternate**: `X_a`, `off_a`, `X_b`, `off_b`. Two starts minimum before quoting any rate; three
   when the effect is < 3 %.
3. **Serve as a transient unit**, one variable per `--property=Environment=` entry, `FN_EXTRA` as a
   single quoted property. **Never build the command with `eval`** — the quoting silently dropped
   `FN_EXTRA` once and the whole arm ran with prefix caching on (2.6 s → 0.6 s "TTFT"). Use a bash array
   for the varying properties.
4. **Readiness loop** on `GET /v1/models` (`Authorization: Bearer <key>`), 150 × 10 s; on unit death
   write `DIED after Ns` plus the last `Error|Traceback` lines. Then **capture the init lines** you need
   to prove the path: the activation/dispatch log line, the warmup line, and
   `enable_prefix_caching=…` grepped from the log. A run without the path line is not a measurement.
5. Probes: `ttft.py`, then `ttft2.py`, then (warm arms) `agentloop2.py`, output appended to the results file.
6. `stop_unit` between arms: `systemctl stop`, wait for `LoadState=not-found`, `reset-failed`, then wait
   for `MemAvailable ≥ 100 GiB` (the PLE tables take a minute to drain).
7. End with `== ALL DONE ==`; monitor with `tail -F … | grep --line-buffered "^=== |init:|TTFT|CONC|DIED|Traceback|ALL DONE"`.

Launch: `sudo systemd-run --unit=<name> --collect -E HOME=/root -E PATH=/usr/local/cuda/bin:/usr/local/bin:/usr/bin:/bin bash /opt/llm/runners/<name>.sh`.
Sudo: `printf '%s\n' "$SUDO_PW" | sudo -S -p '' …` — never a heredoc on sudo's stdin.

## Traps, all paid for

- **A runner restart truncates its results file** (`: > $OUT` at the top): re-running a script to add an arm wipes the
  finished arms' text. The durable record is the per-arm **append-mode JSONL** the probe writes (`posdiv-<arm>.jsonl`) and
  the server logs (`/opt/llm/fnext-<arm>.log`); give the re-run a new `$OUT` name and archive the old one first.
- **"Same prompt twice" is blind to history-dependent state.** The PLE offload semaphore ran one step ahead for three days
  while every identical-repeat check passed (warm == warm). A determinism probe must compare (a) the cold first request of a
  fresh server, (b) a warm repeat, and (c) a request that followed a *different* request; `tools/determinism/ple/period.py`
  (16 identical requests, full prompt-logprob vector hashed, class sequence) does (a)+(b), a prompt change before it does (c).

- **Root cannot run git in the user's repo** (dubious ownership): `git show sha:file > x` produces an
  empty file and the step that consumes it does nothing. Pre-copy scripts to `/opt/llm/runners/`.
- **Stale copies**: the runner must copy the test/probe file it uses at its start, or it runs last week's.
- **Do not edit a runner while it runs**; bash reads it incrementally. Stop, edit, restart under a new name.
- **A quick standalone under a 3-page cache is L2-resident** (24 MiB L2 holds 8 pages of K/V); it ranks
  tiles by dot cost, the server by gather cost. Rank at the server.
- **Silent fallbacks look like noise** (+1 %). Every gated path logs the path it took, once per
  process, and the runner captures it.
- **Prompt reuse across arms hits the prefix cache** unless it is off; `ttft.py`'s 8k prompt is a prefix of
  its 30k prompt.
- **Client on the same box**: fine at c ≤ 2; nothing else may run (no downloads — unified memory bandwidth).
- The warm arm needs the MTP head patches in the venv (`lmhead_mtp_patch.py`, `scaleinv_mtp_patch.py`
  on `vllm-venv-fnmain`; already in the `fnmain2` overlay).

- **Name a cause only after measuring the alternative.** The differing-cell rule says the knob must *reach*
  the cell; it does not say the knob is the *only* thing that moved, and a five-rung bisect ran on a cell
  that also contained our tile-union kernel and torch.compile on/off. Before writing "X caused Y", state
  what you ran that would have come out differently if it had not. Usually the counterfactual is already
  on disk: an older log, the other venv, the second wheel (memory `no-cause-without-counterfactual`).
- **Read an output, not a counter.** One "corrupt" count hid a substitution, a duplication and a
  whole-sentence translation for a morning. Aggregates cannot separate the failures they aggregate.

## Recording

Copy `results/<name>.txt` to `notes/data/` **the same session** (`/tmp` and runner state do not survive
reboots), write the finding with the table (on / off, per start), the path line, and what was wrong if
anything was, then `git grep -nI -E "sk-[A-Za-z0-9_-]{16,}|hf_[A-Za-z0-9]{30,}|<REDACTED>|BEGIN [A-Z ]*PRIVATE KEY" -- .`,
commit, push. A withdrawn number gets its own finding that names the one it withdraws.
**Put the commit message in a file** (`git commit -F msg`), never a heredoc containing backticks — command substitution ate a clause three times in one day and once left a stray file in the repo.

Related: [[venv-overlay]] (putting a branch onto the serving venv first), [[upstream-post]] (when the
number goes into a PR or issue), memories `qsa-union-kernel-state`, `spec-decode-prefix-cost-agentloop`.
