#!/usr/bin/env python3
"""pr-ready: the checks ashhart's reviews kept asking for, run before any push or reply.

Usage: pr-ready.py [--pr N] [--dir WORKTREE] [--body FILE] [--reply FILE]
  --pr     open PR on ashhart/TensorFold (body and head come from GitHub unless --body given)
  --dir    local worktree (default: the worktree whose branch or HEAD matches the PR)
  --body   PR body file to check instead of the live one (use for a body about to be PATCHed)
  --reply  reply draft to check (stale SHAs, AI lines)
Exit 0 = no FAIL. WARN lines are judgement calls; say in the reply why one does not apply.
"""
import argparse, json, os, re, subprocess, sys

REPO = "ashhart/TensorFold"
AUTHOR = "600316+jschmied@users.noreply.github.com"
BASE = os.path.expanduser("~/git/tensorfold")
fails, warns = [], []


def sh(cmd, cwd=None, ok=False):
    r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"})
    if r.returncode and not ok:
        raise SystemExit(f"pr-ready: `{cmd}` failed: {r.stderr.strip()[:300]}")
    return r.stdout


def find_dir(branch, head):
    for blk in sh(f"git -C {BASE} worktree list --porcelain").split("\n\n"):
        path = re.search(r"^worktree (.+)$", blk, re.M)
        if path and (f"refs/heads/{branch}" in blk or (head and f"HEAD {head}" in blk)):
            return path.group(1)
    return None


def shas_in(text):
    return set(re.findall(r"`([0-9a-f]{7,40})`", text))


def check_text(name, text, d, head, main):
    """Every backticked SHA must be a real commit; one on neither the branch nor main is stale."""
    if re.search(r"co-authored-by|generated with|claude|\bAI\b assist", text, re.I):
        fails.append(f"{name}: AI/attribution line (TF posts carry none)")
    for s in sorted(shas_in(text)):
        if sh(f"git cat-file -t {s}", d, ok=True).strip() != "commit":
            continue  # a hash of something else (md5, file sha): not ours to judge
        on_branch = subprocess.run(f"git merge-base --is-ancestor {s} {head}", cwd=d, shell=True).returncode == 0
        if not on_branch:
            warns.append(f"{name}: names `{s}`, not on the branch (fine as history; stale if it claims the current head)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", type=int)
    ap.add_argument("--dir")
    ap.add_argument("--body")
    ap.add_argument("--reply")
    ap.add_argument("--base", help="base branch (default: the PR's base, else main)")
    a = ap.parse_args()
    pr = {}
    if a.pr:
        pr = json.loads(sh(f"gh pr view {a.pr} -R {REPO} --json headRefName,headRefOid,body,isDraft,baseRefName"))
    d = a.dir or (pr and find_dir(pr["headRefName"], pr["headRefOid"]))
    if not d:
        raise SystemExit("pr-ready: no worktree found; pass --dir")
    base = a.base or (pr.get("baseRefName") if pr else None) or "main"
    sh(f"git fetch -q origin {base}", d)
    ob = f"origin/{base}"
    head = sh("git rev-parse HEAD", d).strip()
    main = sh(f"git rev-parse {ob}", d).strip()
    if pr and pr["headRefOid"] != head:
        warns.append(f"local HEAD {head[:9]} != PR head {pr['headRefOid'][:9]} (push pending, or wrong worktree)")

    # 1. merge with main (we rebase only when asked; this says whether the ask is coming)
    mt = subprocess.run(f"git merge-tree --write-tree --name-only {ob} HEAD", cwd=d, shell=True,
                        capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"})
    if mt.returncode:
        files = sorted(set(re.findall(r"Merge conflict in (\S+)", mt.stdout)))[:6]
        warns.append(f"conflicts with main {main[:9]}: {', '.join(files) or 'see git merge-tree'} "
                     "(no rebase unless ashhart asks; rerun evidence when he does)")

    # 2. commits: author, trailers, no CHANGELOG, no .sh, line width of added lines
    mb = sh(f"git merge-base {ob} HEAD", d).strip()
    for line in sh(f"git log --format='%h%x09%ae%x09%(trailers:only,unfold)' {mb}..HEAD", d).splitlines():
        h, ae, *tr = line.split("\t")
        if ae != AUTHOR:
            fails.append(f"commit {h}: author {ae}, want {AUTHOR}")
        if any(re.search(r"co-authored|claude", t, re.I) for t in tr):
            fails.append(f"commit {h}: AI trailer")
    changed = sh(f"git diff --name-only {mb} HEAD", d).split()
    if "CHANGELOG.md" in changed:
        fails.append("CHANGELOG.md changed: ashhart places the line; put it in the body")
    for f in changed:
        if f.endswith(".sh"):
            fails.append(f"{f}: .sh committed")
    for f in [c for c in changed if c.endswith((".zig", ".cu", ".cuh", ".py", ".metal"))]:
        diff = sh(f"git diff -U0 {mb} HEAD -- '{f}'", d)
        ln = 0
        for l in diff.splitlines():
            m = re.match(r"@@ .*\+(\d+)", l)
            if m:
                ln = int(m.group(1)) - 1
                continue
            if l.startswith("+") and not l.startswith("+++"):
                ln += 1
                if len(l) - 1 > 120 and re.match(r"\+\s*(//|#)", l):  # lean's rule: comments, one line, <=120
                    fails.append(f"{f}:{ln}: comment {len(l) - 1} cols > 120")
        if f.endswith(".zig") and re.search(r"^\+\s*//[^/!].*\n\+\s*//[^/!]", diff, re.M):
            warns.append(f"{f}: a multi-line // comment was added (lean flags these; one line each)")

    # 3. body and reply text
    body = open(a.body).read() if a.body else pr.get("body", "")
    if body:
        check_text("body", body, d, head, main)
        if head[:9] not in body and head[:7] not in body:
            fails.append(f"body never names the head {head[:9]} (checks/verification line is stale)")
        if not re.search(r"CHANGELOG line", body, re.I):
            warns.append("body has no proposed CHANGELOG line")
        ev = {
            "seeded": r"seeded", "resume": r"resum", "concurrency": r"concurren|c=4|4 streams|at once",
            "against main": r"against main|main's|== main|equals? main", "planted control": r"control|planted|red",
            "refusal test": r"refus",
        }
        missing = [k for k, p in ev.items() if not re.search(p, body, re.I)]
        if missing:
            warns.append(f"body never mentions: {', '.join(missing)} (ashhart asks for these; say why if N/A)")
    if a.reply:
        check_text("reply", open(a.reply).read(), d, head, main)

    for f in fails:
        print("FAIL", f)
    for w in warns:
        print("WARN", w)
    print(f"pr-ready: {len(fails)} fail, {len(warns)} warn, head {head[:9]}, main {main[:9]}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
