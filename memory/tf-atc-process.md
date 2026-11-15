---
name: tf-atc-process
description: "TF since 2026-10-22: contributions coordinated via ATC (Agent Traffic Control) claims + public anonymous agent radar; adoption needs the user's decision"
metadata:
  type: project
---

On 2026-10-22 ashhart made [ATC](https://github.com/ashhart/ATC) the TF contribution process (AGENTS.md, CONTRIBUTING.md, docs/atc/SKILL.md, .github/atc.json areas). Agents should run `atc board --json`, claim the issue, pulse while working, run `atc overlap --json` before a PR, and land when done. With ATC >= 0.7.0 a new claim automatically starts an anonymous public session on https://tensorfold.dev/atc; `--local` keeps reporting local. ashhart posts `/atc presence <hash>` comments on threads (#286, #1015, #1156); those are automated and ask nothing.

**Why:** it's a public, outward-facing step (claims and sessions are visible), so we haven't adopted it without the user's go.
**How to apply:** before the next TF PR, ask the user whether to install ATC and claim (public vs `--local`). Until then, keep the old flow but mention it. Related: [[tf-27b-flashnext-nvfp4-prs-1021]].

**2026-10-23 (user pointed at tensorfold.dev/atc#join):** ATC 0.7.0 installed at ~/.local/bin/atc (`npm install -g --prefix ~/.local github:ashhart/ATC`; no deps, no install scripts). `atc doctor` all ok. Read-only commands (board, `who`, `overlap`, `check`) are free to use. `claim`/`start` without `--local` posts a public verification comment on the issue = outward: do it as part of the user's go for that PR. Check-ins are anonymous unless `--github-name`; pulse every ≤5 min while working.
**Approved 2026-10-23 (user: "yes"):** apply from the next TF PR on: agents run `atc who`/`atc overlap` (read-only) before editing TF files; before each new TF PR, `atc check` then public anonymous `atc claim` as part of the PR go.

**2026-10-24:** Dory claimed: issue #1233 opened (body ~/notes/post/dory-claim.md), `atc claim 1233` posted (comment 6381526504). Implementation agent runs locally in ~/git/tf-dory (branch dory-family), progress log ~/notes/dory-progress.md; NVFP4 3.2 GB download approved, nothing pushed.
**2026-10-24 evening:** Dory steps 1-7 done locally (branch dory-serve: 849d235e9 template tests, c1a85bc78 serving, 8ce17cbae resume gate). All gates pass at L=1/2/4. Decode tok/s @1/8 streams: L1 64/475, L2 44/328, L4 27/199. Matches vLLM #60149 semantics. Open: steps 8-9, #1233 answers, nothing posted beyond the claim issue.
**2026-10-24 ~20:45Z Dory POSTED** as 6 stacked PRs on main 6244c6206: #1256 norms, #1257 qk_rows, #1258 act_rows, #1259 dense_rows, #1260 family+forward, #1261 serving+resume (base commit = #1245's softcap include fix). All MERGEABLE; each tip lean 0 new + full test green (my own run). atc overlap: append conflicts with #987/#1050/#1113/#1163/#1211.
- 2026-10-25 ~04:00Z: whole Dory stack #1256-#1261 LANDED 6528fbec3..81b476df1 (our authorship + 5 maintainer children). GB10 L=2: decode 44.2/86.2/164.1/298.6 tok/s at 1/2/4/8 streams, prefill 5.1k-4.2k tok/s 512..16k; #1233 claim done. Paged KV (step 9) rebasing onto it.
- 2026-10-25: #548 CLAIMED (atc comment 6396144205), user "work on 548". Agent: Nemotron onto shared CUDA ops in ~/git/tf-548 (branch shared-nemotron), notes ~/notes/548/. Mac agent: Metal kv_pool adapter (branch metal-kv-pool on the Mac), user-approved; no issue claimed for Metal paging yet — claim at post time.

**Public named presence (2026-10-26, user: "by name"):** our working sessions appear on the ATC public board under the GitHub name.
- **Start:** `atc start <issue> --github-name --json`, run from a TF clone (e.g. `~/git/tf-kvdisk`), not this repo. The MCP tools default to the cwd clone.
- **Keep live:** sessions are listed in `/tmp/claude-1000/atc-sessions.txt` (`issue:session[:state]`). The scratchpad script `atc-pulse.sh` pulses them every 4 min and stops on `/tmp/claude-1000/atc-pulse.stop` or after 10 h.
- **End:** when the agent on an issue finishes, run `atc land <issue> <session>` and remove its line.
- **Claims:** a new `atc claim` auto-creates a public session (the repo has `.github/atc-presence.json`). Add `--github-name` so it shows by name.
