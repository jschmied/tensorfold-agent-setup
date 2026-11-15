---
name: knowledge-tree
description: Persist substantial, evolving knowledge as a hierarchical tree of markdown files under the project's knowledge/ dir, with a root index.md that is linked from MEMORY.md. Use when accumulating multi-part findings, investigations, benchmarks, or comparisons that would sprawl as flat memory files. Also use to READ back accumulated knowledge — start at the root index and walk down.
---

# Knowledge tree

Persist large, growing knowledge as a **tree of markdown files** instead of one flat note. The tree lives on disk; MEMORY.md holds one pointer to its root, so it's reachable every session.

## Location
- **Root dir:** `<memory-dir>/knowledge/` — sibling of `MEMORY.md`
  (here: `/home/jschmied/.claude/projects/-home-jschmied-git-dgx-spark-setup-guide/knowledge/`).
- **Root index:** `knowledge/index.md` — the table of contents.
- **Subtopics:** subdirectories, each with its own `index.md`.
- **Leaves:** `<slug>.md`, one concept per file.

## Structure rules
- **One concept per leaf.** Frontmatter: `title`, `updated` (YYYY-MM-DD), `tags`.
- **Every directory has an `index.md`** listing its children — one line each, linked, with a one-line hook. This is what makes it a navigable tree.
- **MEMORY.md carries exactly one pointer** to `knowledge/index.md` (kept up to date). The individual leaves are NOT indexed in MEMORY.md — only the root is. Discovery flows root → subtree → leaf.
- Link between leaves with **relative markdown links**; link to flat memory notes with `[[slug]]`.
- Convert relative dates to absolute; record the "why", not just the "what".

## Maintenance
- On add/rename/move/delete: **update the nearest `index.md`** (and the root if a top-level subtree changed).
- **Prune** stale leaves; delete what's wrong. Don't duplicate what the repo, its docs, or a flat memory note already record — link to those instead.
- Keep leaves small and focused; when one grows past ~1 screen of distinct facts, split it into a subdir.

## What to store (prioritise these)
- **Results of expensive computation** — benchmark sweeps, evals, long training/quant runs, cloud
  scores. Anything costly to reproduce. Record the numbers, the exact config that produced them, and
  the date. This is the highest-value category — never let an expensive result live only in chat.
- **Configuration of checkpoints** — per model: on-disk path, quant scheme (weights/activations/KV),
  serving flags, served name, sampling defaults, and any gotchas. So a checkpoint can be re-served
  correctly without re-deriving it.
- **Infrastructure knowledge** — service accounts, API keys/tokens, endpoints, credentials, venv/tool
  locations, one-off setup steps. **This machine is private and single-user, so secrets (API keys,
  passwords) MAY be stored here in plaintext** — that's a deliberate trade for a private box; do not
  carry this assumption to shared/multi-user environments.

## When to use
- A finding has many parts or grows over sessions (benchmark campaigns, model comparisons, multi-step investigations).
- You're about to write a 3rd+ flat memory file on the same theme → make a subtree instead.
- Recalling: open `knowledge/index.md` first, then walk down to the relevant leaf.

## When NOT to use
- A single self-contained fact → a flat memory file is fine.
- Something the repo/docs/git already record → link, don't copy.
