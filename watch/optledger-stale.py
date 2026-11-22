#!/usr/bin/env python3
"""Find optimization-ledger cells that say `open [#N]` while #N is merged or closed.

Reads docs/optimization-ledger.md from origin/main in a TF clone (fetches main first), asks GitHub for every
referenced number in one GraphQL call, and prints one line per stale cell. Exit 1 if any cell is stale.
Usage: optledger-stale.py [--repo ~/git/tensorfold] [--no-fetch] [--ref origin/main]
"""
import argparse, json, os, re, subprocess, sys

OWNER, NAME, PATH = "ashhart", "TensorFold", "docs/optimization-ledger.md"
CELL = re.compile(r"open ([CMHX]?)\[#(\d+)\]")


def ledger(repo: str, fetch: bool, ref: str) -> str:
    if fetch:
        subprocess.run(["git", "-C", repo, "fetch", "-q", "origin", "main"], check=True)
    return subprocess.run(["git", "-C", repo, "show", f"{ref}:{PATH}"], check=True,
                          capture_output=True, text=True).stdout


def states(nums: list[int]) -> dict[int, tuple[str, str, str]]:
    """number -> (kind, state, date) for PRs and issues, in one query."""
    parts = [f'n{n}: issueOrPullRequest(number:{n}){{__typename ... on PullRequest{{state mergedAt closedAt}}'
             f' ... on Issue{{state closedAt}}}}' for n in nums]
    q = f'{{repository(owner:"{OWNER}",name:"{NAME}"){{{" ".join(parts)}}}}}'
    out = subprocess.run(["gh", "api", "graphql", "-f", f"query={q}"], capture_output=True, text=True)
    data = json.loads(out.stdout or "{}").get("data", {}).get("repository", {}) or {}
    res = {}
    for n in nums:
        r = data.get(f"n{n}")
        if r:
            res[n] = (r["__typename"], r["state"], (r.get("mergedAt") or r.get("closedAt") or "")[:10])
    return res


def table_row(lines: list[str], i: int) -> tuple[str, str]:
    """The row label and the family column of the cell on line i (header is the nearest `| Optimization` above)."""
    head = next((lines[j] for j in range(i, -1, -1) if lines[j].startswith("| Optimization")), "")
    return lines[i].split("|")[1].strip(), head


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.expanduser("~/git/tensorfold"))
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--ref", default="origin/main", help="branch or commit to read the ledger from")
    a = ap.parse_args()
    lines = ledger(a.repo, not a.no_fetch, a.ref).splitlines()
    hits = [(i, m) for i, l in enumerate(lines) if l.startswith("|") for m in CELL.finditer(l)]
    st = states(sorted({int(m.group(2)) for _, m in hits}))
    stale = 0
    for i, m in hits:
        n = int(m.group(2))
        kind, state, date = st.get(n, ("?", "UNKNOWN", ""))
        if state == "OPEN":
            continue
        row, head = table_row(lines, i)
        cols = [c.strip() for c in head.split("|")[1:-1]]
        k = lines[i].count("|", 0, m.start()) - 1           # column of this match, not the first equal cell
        fam = cols[k] if 0 <= k < len(cols) else "?"
        verdict = "done" if state == "MERGED" else "check: closed, landed elsewhere?"
        stale += 1
        print(f"STALE l{i + 1} {row} / {fam}: {m.group(0)} is {kind} {state} {date} -> {verdict}")
    print(f"optledger: {len(hits)} open cells, {stale} stale")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
