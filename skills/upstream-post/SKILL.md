---
name: upstream-post
description: Post to vLLM, SGLang, llama.cpp or a community repo (issue comment, RFC, PR, reply) from this project's evidence, with the checks that have prevented duplicates, leaked secrets and unsupported claims. Use whenever a result should leave the repo, and to look up where and when something was posted.
---

# Posting upstream

Nothing leaves the repo without the user's explicit go for **that** post. "Post it" applies to the draft
named, not to the next one. A reply to a reply is a new post.

## Is this post worth existing? (added 2026-09-09, after a 10-comment day)

**State in one line what the thread is MISSING, before drafting.** If that line reads "a third
confirmation of something nobody disputes", do not post. Adjacency is not a reason — on 2026-09-09 a
comment was queued for #52244 purely because the thread was open, when everything in it was either
already on the thread in our own words, better evidenced by someone else the same day, or belonged to a
different PR. Two suggestions in a row that day ("nobody has posted a GB10 datapoint on #50897") were
wrong in the same way: **we had already posted one, and a third party had since posted a stronger one.**

Checks, cheapest first:
1. Search the thread for our own login — we may have said it already.
2. Read the newest comments in full — someone may have just said it better, on better hardware.
3. Ask whether the point belongs to *this* PR or a neighbouring one (a flag's numbers belong on the
   flag's PR, not on a rival fix's).
4. If the answer is "the PR needs a rebase / a reviewer", that is not something a comment supplies.

**Volume is its own signal.** Ten comments across two projects in a day, four to one small repo inside
the same minute, reads as flooding however good each one is. Space them, or consolidate into one.

**The kinds that are almost always worth it:** correcting our own number, paying a stated debt,
answering a direct question, and supplying a mechanism nobody has named.

## `--since` takes UTC; this box is CEST

`gh api ...?since=` compares against GitHub's **UTC** timestamps. Passing the box's local clock
(CEST, UTC+2) silently skips the last two hours. On 2026-09-12 that hid a reply on vllm#51782 that
had been sitting for four hours, on a thread we had posted to that morning.

Always build the window in UTC:

```bash
SINCE=$(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%SZ)
gh api "repos/<o>/<r>/issues/<n>/comments?since=$SINCE" --jq '...'
```

and when a thread looks quiet, list the tail unfiltered (`| tail -6`) before concluding nothing
arrived — absence under a filter is not absence.

## Before writing

0. **For a fix PR, and before any long bisect of a symptom others report: search OPEN PRs first** —
   `gh pr list -R <o>/<r> --state open --search "<file basename>"` for every file the fix touches, then the symptom in
   plain words and in identifiers (GitHub does not split `state_indices` to match "state index"); read the newest five
   titles fully. We duplicated vllm#55375 this way (2026-09-05); if a PR exists, put the evidence there instead.
1. **Re-read the thread state** (`gh api repos/<o>/<r>/issues/<n>/comments?since=<ISO>`), including
   bots' comments you skip: two duplicates were posted because the thread had moved. A question that
   sounds like "where is X" is a location question — answer it, do not repost X.
2. Check the posting log `notes/upstream/README.md` for what we already said there, with the URL.
3. Confirm every number against its finding (finding number + data file). A number quoted from memory
   was wrong once (a 27B figure applied to Flash-Next; withdrawn in the-field).

## Writing the draft (`notes/upstream/<slug>.md`)

- First line: `DRAFT — needs the user's go. <venue> <target> (<date/time>).`
- Short by default (memory `write-short-by-default`): lead with the result, one table if numbers,
  the box named (GB10, sm_121, TP1, the build), starts per cell, what was *not* measured.
- Link code by **commit-pinned permalinks with line anchors** — a reviewer should never have to scan our
  repo. Link data files and findings the same way.
- vLLM policy for PRs and RFCs: disclose AI assistance in the body; `git commit -s`;
  `Co-authored-by: Claude <noreply@anthropic.com>`; the human reviewed every line. For issue comments the
  disclosure line is optional but harmless.
- Never name people by email; never paste API keys, hostnames' secrets, or runner scripts.

## Posting

```
gh issue comment <n> -R <owner>/<repo> --body-file <draft-without-the-DRAFT-line>
gh issue create -R vllm-project/vllm --title "[RFC]: …" --body-file … --label RFC   # RFC template sections: Motivation / Proposed Change / Feedback Period / CC List / Any Other Things
gh issue edit <n> -R … --body-file …                                              # edits the body; verify with `gh issue view --json body`
gh pr create -R <owner>/<repo> --base <branch> --head jschmied:<branch> --title "[Bugfix][Area] …" --body-file …
   # vLLM PR body = the template: `## Purpose` / `## Test Plan` / `## Test Result` (before/after numbers), then the
   # "Essential Elements" checklist ticked, then the AI-generated-code line; commits `git commit -s` + Co-authored-by.
   # A PR against another fork's branch (e.g. the #53899 branch on peakcrosser7/vllm) works the same way and needs the
   # same format — the author merges it into the upstream PR. 2026-09-06: opened with my own section names first, reformatted after.
```

- `gh pr edit` fails on this account (Projects classic GraphQL); edit PR bodies with
  `gh api -X PATCH repos/<o>/<r>/pulls/<n> --input body.json`.
- Push to the fork remote (`fork` = `jschmied/vllm`), never to `origin` (upstream, 403). Fetch and rebase
  onto the fork's merge commit if the push is rejected. Fast-forward the fork's `main` to upstream before
  sharing a `compare/main...branch` link, or the compare shows every upstream commit.
- **HF tokens are now in scope** (added 2026-09-10, when a `write`-scoped token entered the session and
  the old pattern would not have caught it): the scan includes `hf_[A-Za-z0-9]{30,}`. Tokens live at
  `~/.cache/huggingface/token` and `/opt/llm/.hf_token`, both mode 600, and never in a repo.
- **Known false positives**: `dgx-spark-setup-guide` contains `sk-alice-…` and `sk-promet…` in six
  documentation files. They are example API keys in the walkthroughs, not secrets. 11 matches, all
  placeholders — do not re-investigate.
- Secret scan **before** the commit that adds the draft:
  `git grep -nI -E "sk-[A-Za-z0-9_-]{16,}|hf_[A-Za-z0-9]{30,}|<REDACTED>|BEGIN [A-Z ]*PRIVATE KEY" -- .`

### Maintaining our open PRs (added 2026-10-08)

* **The PR's branch comes from GitHub, not from a worktree name:** `gh pr view N --json headRefName,headRefOid`. One
  fresh worktree per PR from the fork's head; never `reset --hard` an existing worktree to update it.
* **Merge conflicts on vLLM PRs:** merge `origin/main` into the branch (no force push), resolve, `commit -s`, push to
  `fork`. Our venvs cannot import current main, so verify by `py_compile` plus a static import check of the PR's
  files, say so in the post log, and watch CI. Stacked PRs (e.g. #58835 on #58439) need the same merge each.
* **Someone posts a duplicate of our PR:** one line on theirs, "Duplicate of #N (opened <date>), which fixes the same
  … Happy to close either one." (TF #500 was closed by its author within hours.)
* **TensorFold oracle fixtures:** a reviewer must be able to regenerate them. Kernels whose Python lives only on our
  fork (fp8/experts.py, families/kolibri1) need the fork commit named in the oracle script; prefer posting the
  pieces whose oracle is upstream (`python-0.6`) first, and split out the smallest standalone PR (TF #517).

## After posting

1. Posting log entry in `notes/upstream/README.md`: number, date/time, venue, one line, draft file, URL.
2. If the post adds a fact to the record, the finding or the-field entry references the URL.
3. Commit + push the notes repo.
4. Watch list: the hourly watchdog checks the watched numbers for **human** comments since the last tick
   (`select(.user.type!="Bot")`, skip our own login); summarise, never reply without a go.

## Venues we use and their conventions

| venue | what goes there |
| --- | --- |
| vllm-project/vllm issues #54521, #54928, #53670 | determinism evidence; keep to one mechanism per post; offer the GB10 for specific cells |
| vllm PRs #55122, #55180, #53899, #54765 | our fixes; reviewer replies within a day; numbers with two/three starts |
| RFC #55394 | the tile-union kernel; design questions listed in the order that decides the PR |
| blazux/qwen3.8-Flash-DGX, MiaAI-Lab/…-Single-DGX-Spark | recipes: config items with their numbers and ours side by side; never a kernel patch |
| HuggingFace | hiding a repo is irreversible; discussions are posts too |

Related: [[gb10-ab]] (where the numbers come from), memories `posting-check-thread-state-first`,
`write-short-by-default`, `check-field-before-expensive-steps`.
