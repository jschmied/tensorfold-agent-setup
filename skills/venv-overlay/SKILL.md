---
name: venv-overlay
description: Put a vLLM source branch, an upstream PR, or a patch script onto one of the GB10's serving venvs for validation, and take it off again cleanly. Use before any server A/B of Python/Triton changes to vLLM, and to answer "what is installed in venv X right now".
---

# Overlaying a change onto a serving venv

The serving venvs are wheel installs (`/opt/llm/runtime/vllm-venv-*`, owned by root, run as `llm`).
Python/Triton changes need no build: copy the files in. Half of one night's lost runs were overlay
state, not kernel bugs, so the procedure is strict.

## Which venv

| venv | what it is | use it for |
| --- | --- | --- |
| `vllm-venv-fnmain2` | nightly `0.28.1rc1.dev401+g8340fe1bb` + the 17-file overlay (`tools/main/fnmain-overlay-dev401.diff`: PLE offload worker, PLE gate, MTP head patches, lm_head scale loader) | branch validation against main |
| `vllm-venv-fnmain` | the previous nightly (dev352) + its overlay | warm-turn work that predates dev401 |
| `vllm-venv-preview` | the shipped preview image's tree | anything meant for blazux/Mia users |
| `vllm-venv-fnext` | client-side python (probes) | never serve from it |

Pristine copies: `/opt/llm/runtime/vllm-venv-fnmain2-vllm-pkg-pristine-dev401.tgz` (the package **before**
the overlay). Restoring a file from it removes the overlay's edits too — check the overlay's file list first.

## Rules

1. **Never touch a venv while any `fx-*` unit or runner is active** (`systemctl list-units 'fx-*'`).
2. **One change at a time, and each removed with the script or backup that installed it.** A v3 patch
   cannot be removed by the v4 script (anchors differ); a failed removal that prints nothing is the
   usual sign (see git-as-root below). Keep every patch version's script under `/opt/llm/runners/`.
3. **Backups with a suffix before the first copy** (`<file>.orig-<base>`), never overwritten later.
4. **Drift check before a branch overlay**: diff the venv's base files against the branch's base commit
   (`git show origin/main:<path> | diff - <venv>/<path>`). If other files changed between the venv's
   commit and the branch base, copy them too or the set is incoherent (`qsa_indexer.py` was such a case).
5. **Env vars the branch adds to `vllm/envs.py`** must be patched into the venv's `envs.py` (type
   line + lambda); a bare `os.getenv` in a module works too, but the venv's `envs` will raise on
   attribute access otherwise. Verify with `grep -c`.
6. **Purge `__pycache__`** under the touched packages after every copy; stale bytecode has masked a copy.
7. **Compile-check with the venv's interpreter** (`<venv>/bin/python -m py_compile …`).
   **Dry-run every patch script on a copy first**: `cp <venv file> copy.py; VLLM_X_PY=copy.py python patch.py; py_compile copy.py;
   python patch.py off; diff -q copy.py <venv file>` — install, compile, remove, byte-identical. 2026-09-06: a probe with a
   4-space indent inside a class method reached the venv through a queued runner, the server died at import, and the run
   was lost; the runner's own teardown reverted the file, but only because it happened to run to the end.
8. **Prove the path at runtime**: the change must log a line when it is taken (dispatch, warmup, "path:
   raw/stock"), and the A/B runner must capture it. A guard that fails quietly turns an A/B into noise
   (finding 114: two full server runs measured stock).
9. **Test before serve**: the pytest/asserting test on the GPU (as an `fx-*` unit, `--uid=llm`,
   `PYTHONSAFEPATH=1`, the venv's caches under `/opt/llm/.cache-fnmain2`) before any serve arm.
10. **Record what is installed** in the finding or memory: venv, files, base commit, backups' suffix.

## Traps

- **Root cannot run `git show` inside the user's repo** ("dubious ownership") — it writes an empty file
  and the consumer runs nothing. Generate everything as the user into the scratchpad, then `sudo cp`.
- `cp $B/vllm/… $V/vllm/…` doubles the package path when `$V` already ends in `/vllm`; check the target
  exists after the copy (`grep -c <new symbol>`), not just the exit status.
- **`nn.Module` refuses `register_buffer` on a name already set as an attribute** (`KeyError: attribute
  already exists`); the kernel test never constructs the layer, so only the serve start catches it.
- `cp -a` of a whole venv keeps the original's interpreter path in shebangs (memory `venv-copy-shebang-trap`).
- The dev401 overlay's own list (17 files) is the boundary: a file outside it can be restored from the
  pristine tgz; a file inside it cannot.

## Removal

Reverse order of installation: patch scripts with `off` (their own version), then `cp <file>.orig-<base>`
back for copied files, purge `__pycache__`, `py_compile`, and a `grep -c` that the symbol is gone. Only
then is the venv "clean" for the next change.

Related: [[gb10-ab]], memories `gb10-venv-hygiene`, `vllm-026-cutover`, `venv-copy-shebang-trap`.
