---
name: tf-pr
description: Open, update or answer review on a TensorFold PR (ashhart/TensorFold) without the rounds ashhart keeps asking for — evidence defaults, the pr-ready check, and the agent handover protocol so finished work never sits unpushed. Use before briefing any agent that will touch a TF PR, before every TF push/body PATCH/reply, and when an agent reports a PR done.
---

# TensorFold PRs: get it right in round 1

Measured 2026-11-11: 58 ashhart comments with asks on 34 of our PRs in two weeks. Most of them repeat the same things:
- about 27 were "rebase";
- about 24 were "the body/doc names an old head";
- about 22 were "refuse by name / before anything is queued";
- about 15 were "seeded, resume and concurrency coverage";
- about 12 were "equal to main, or on equal to off";
- about 11 were "speed rows";
- about 9 were "evidence on this exact head";
- about 9 were "a planted control".

Separately, finished work sat unpushed and unanswered: #2705 for 9.5 h, and #1503 for 20 h, twice. Both rules below exist because of these.

## 1. Evidence defaults: in the FIRST post, not after the ask

| Change touches | Ship with |
|---|---|
| any opt-in path (env flag, `_table`/second instantiation) | **off == main**, shown by SASS equality on every SM we build or by byte-identical text, AND **on == off** replies over greedy + seeded, resume, and concurrency 1/4/8 (and drafting if the family drafts) |
| a new kernel or device check | a **planted control** per kernel, shown red before green; give its file:line in the body |
| a new refusal | a test that names the refusal AND proves nothing was queued or copied before it fires |
| served behaviour | the load line, resumed == fresh over multi-turn chats, the after-drain census, and a cold turn vs main in A-B-B-A order with the **paired** median and an "N of M slower" count |
| speed | the same rows on the **final head**. No served cell may be slower (ashhart's rule). A paired loss is said plainly, with "don't land yet". |
| an env flag | a `.flag` row in `environment.zig`, read via `environment.value`, with a refusal test by name for `off/false/no/on/2/" 0"` |

Every speed change must be exact: no token-changing mode, not even opt-in. Clean-room: other engines can inspire, but never read or port their code. Check code sharing across families and backends before writing new code.

## 2. `pr-ready` before every push, body PATCH or reply

```bash
python3 ~/notes/watch/pr-ready.py --pr N [--body new-body.md] [--reply reply.md] [--dir worktree]
```
It FAILs on:
- an author other than the noreply address, or AI trailers or lines;
- a CHANGELOG.md change, or a `.sh` committed;
- an added comment over 120 cols;
- a body that never names the current head.

It WARNs on:
- a conflict with main (rebase only when ashhart asks, but expect the ask and keep the evidence ready);
- old SHAs in the body (fine as history);
- a missing proposed CHANGELOG line;
- evidence words that never appear (seeded, resume, concurrency, against main, control, refusal).

Answer each WARN in the body, or say why it doesn't apply.

**After any rebase:** run `python3 ~/notes/watch/rebase-gates.py --dir <worktree> --pr N` (or `--old-head SHA`). It lists the files whose PR patch changed in the rebase (RESOLVED), what main changed under the code the PR reaches through imports and `#include` (UNDER), the matching `zig build` steps, and a per-backend verdict: host only or a device rerun. It suggests; read RESOLVED/UNDER before trusting "host only", and say in the body which gates were rerun and why.

**A conflict with main:** never push a rebase unasked (`docs/recipes/SKILL.md:37`). If the conflict is in code rather than CHANGELOG.md alone, rebase into a local branch (`<branch>-next`), rerun the gates and served rows there, and keep them ready. When ashhart asks, push within minutes. A CHANGELOG-only conflict is ashhart's to resolve at landing.

## 3. Briefing an agent on a TF PR

Paste this block into the brief, verbatim:

> Finish condition: your LAST message must begin with exactly one of
> `POSTED <comment url>`: pushed and replied, `pr-ready` 0 fail, ask ids marked with open-asks.py;
> `READY <worktree> <branch> <sha> <reply file> [<body file>]`: everything green, not pushed;
> `BLOCKED <one line why>`.
> "Waiting" is not a finish. If you stop with gates green and no POSTED, write READY.
> Before any push or post: run `python3 ~/notes/watch/pr-ready.py --pr N --body <body> --reply <reply>`.
> Evidence defaults: ~/.claude/skills/tf-pr/SKILL.md section 1.

Also include the house rules: the author is `Jürgen Schmied <600316+jschmied@users.noreply.github.com>`, no AI trailers or lines, no CHANGELOG commit, push to `fork` only with a lease, no `.sh`, no stash, kill by PID only, and GPU only through the dispatcher.

## 4. Main session: when a PR agent completes

- `POSTED`: open the URL and check it went up. Run `open-asks.py` and confirm the ask is marked done.
- `READY`: do it yourself right away:
  1. Run `pr-ready`.
  2. Push with a lease on the PR head.
  3. PATCH the body.
  4. Re-read the thread for anything newer.
  5. Post the reply.
  6. Mark the ask done and add a ledger line.
- `BLOCKED` or anything else: triage now. An agent that says "waiting" while its gates are already done has stalled; finish its work as for READY.
- Every 2 h watch: any open ask older than 2 h whose agent has no running job is a stall, so finish it.
