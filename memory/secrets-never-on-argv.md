---
name: secrets-never-on-argv
description: Never put a token or password in a command line — systemd-run and journald record argv forever; check gated/private before passing auth at all
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-12T10:34:12.159Z
---

A secret passed as a command-line argument is recorded where you cannot remove it. On 2026-09-12 I
started an HF download with `systemd-run ... aria2c --header='Authorization: Bearer hf_…'`, which put
the write token into the unit's `ExecStart` — visible in `systemctl list-units` and written to
**journald, which is append-only and cannot be surgically edited**.

**Why:** the repo secret-scan (`git grep` before every commit) caught nothing because nothing reached
a repo — it was clean on all three. The rule only covers files we commit, so argv is a blind spot the
existing guard does not see. It matters because we paste log and journal excerpts into upstream
issues routinely; four went out that same day.

**And it was gratuitous.** `deepseek-ai/DeepSeek-V4.1-Flash` is `gated: False, private: False` and
serves HTTP 200 with no Authorization header at all. The secret bought nothing.

**How to apply:**
- **Check first whether auth is needed**: `curl -s https://huggingface.co/api/models/<id>` → `gated`
  and `private`. Public repo ⇒ pass no credential.
- **When auth is genuinely needed, keep it off argv.** aria2:
  `aria2c --conf-path=/opt/llm/secrets/aria2-hf.conf` (mode 600, in a 700 dir, outside every repo;
  it holds the `header=Authorization: Bearer …` line). curl: `--netrc` or `-H @file`. Never inline.
- The canonical token file is `~/.cache/huggingface/token`, mode 600 — that part was already right.
  Do not duplicate a secret into more places than one derived config.
- Exposure already in journald cannot be scrubbed; it ages out with rotation, or the token is
  rotated. Say so plainly rather than implying a cleanup happened.

Same family as [[claude-autostart-remote-control]], where a sudo wrapper plus heredoc wrote the
password into a file. Related: [[ask-before-download]], [[hf-download-aria2c]].

**Slip 2026-10-21:** `curl -H "Authorization: Bearer $(cat ~/.cache/huggingface/token)"` puts the token on argv: command substitution expands into the process arguments. Use `curl -H @file` or `--config` with a 600 file instead. Public repos need no token at all.
