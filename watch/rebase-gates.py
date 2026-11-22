#!/usr/bin/env python3
"""After a rebase: which gates must rerun on the new head, and why.

Compares the PR's own patch before and after the rebase, and what main changed under the code the PR calls.
- RESOLVED: files whose PR patch changed in the rebase (conflict resolution, a dropped hunk, a fixture recomputed).
- UNDER:    files main changed between the old and new base that the PR's files import (transitively).
- STEPS:    `zig build` test/check steps whose roots reach a PR file, so host tests to run.
- VERDICT per backend: host only, or a device rerun (CUDA on the GB10, Metal via mac-agent, HIP, XPU).
It suggests, it does not decide: read the RESOLVED and UNDER lists before trusting a "host only".
Usage: rebase-gates.py --dir WORKTREE (--pr N | --old-head SHA) [--new-head HEAD] [--main origin/main]
"""
import argparse, json, os, re, subprocess, sys
from collections import defaultdict

FIXTURE = re.compile(r"(^|/)(tests?/fixtures/|.*\.tsv$|CHANGELOG\.md$|docs/)")
IMPORT = re.compile(r'@import\("([^"]+)"\)')
INCLUDE = re.compile(r'#include\s+"([^"]+)"')
EMBED = re.compile(r'@embedFile\("([^"]+\.(?:cu|cuh|metal|h))"\)')
STEP = re.compile(r'b\.step\("([^"]+)"')
ROOT = re.compile(r'b\.path\("([^"]+\.zig)"\)')
FN = re.compile(r"^(?:pub )?fn \w+\(", re.M)


def git(d, *a):
    return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, check=True).stdout


def backend(f: str) -> str:
    s = f.lower()
    if s.endswith((".cu", ".cuh")) or "/cuda" in s or "cuda_" in s or "_cuda" in s:
        return "cuda"
    if s.endswith(".metal") or "/metal" in s or "metal_" in s or "_metal" in s:
        return "metal"
    if "/hip" in s or "hip_" in s or "_hip" in s:
        return "hip"
    if "/xpu" in s or "xpu_" in s or "_xpu" in s:
        return "xpu"
    return "host"


def patch_lines(d, base, head, f):
    """The +/- lines of one file's patch, without positions, so a moved base does not count as a change."""
    out = git(d, "diff", "--no-color", "-U0", base, head, "--", f)
    return sorted(l for l in out.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---")))


def import_graph(d, ref):
    """file -> set of .zig files it imports, at ref. Named modules resolve to files named <name>.zig."""
    files = [f for f in git(d, "ls-tree", "-r", "--name-only", ref).splitlines()
             if f.endswith((".zig", ".cu", ".cuh", ".metal", ".h"))]
    by_base = defaultdict(list)
    for f in files:
        by_base[os.path.basename(f)[:-4]].append(f)
    fs = set(files)
    g = {}
    proc = subprocess.run(["git", "-C", d, "cat-file", "--batch"],
                          input="".join(f"{ref}:{f}\n" for f in files).encode(), capture_output=True)
    raw, pos, contents = proc.stdout, 0, {}
    for f in files:                                     # sizes are in bytes, so parse bytes
        hdr_end = raw.index(b"\n", pos)
        size = int(raw[pos:hdr_end].split()[2])
        contents[f] = raw[hdr_end + 1: hdr_end + 1 + size].decode("utf-8", "replace")
        pos = hdr_end + 1 + size + 1
    for f, body in contents.items():
        deps = set()
        if not f.endswith(".zig"):                     # kernels: follow #include "x" relative to the file
            for name in INCLUDE.findall(body):
                p = os.path.normpath(os.path.join(os.path.dirname(f), name))
                if p in fs:
                    deps.add(p)
            g[f] = deps
            continue
        for name in EMBED.findall(body):              # a zig file that embeds or names a kernel source
            p = os.path.normpath(os.path.join(os.path.dirname(f), name))
            if p in fs:
                deps.add(p)
        for name in IMPORT.findall(body):
            if name.endswith(".zig"):
                p = os.path.normpath(os.path.join(os.path.dirname(f), name))
                if p in fs:
                    deps.add(p)
            elif name not in ("std", "builtin", "root", "build_options"):
                c = by_base.get(name, [])              # a named module: core's file, else the one unique match
                core = [x for x in c if x.startswith("zig/src/core/") or x.startswith(f"zig/src/{name}/")]
                deps.update(core or (c if len(c) == 1 else []))
        g[f] = deps
    return g, contents


HUB = 25          # a file importing more than this is a module root (tensorfold.zig ...): do not expand through it
DEPTH = 3         # how far "the code the PR calls" reaches


def closure(g, start, depth=DEPTH):
    """Files reachable from start within depth imports, not expanding through hub files or build files."""
    seen, layer = set(start), list(start)
    for _ in range(depth):
        nxt = []
        for f in layer:
            deps = g.get(f, ())
            if len(deps) > HUB or is_build(f):
                continue
            for n in deps:
                if n not in seen:
                    seen.add(n)
                    nxt.append(n)
        layer = nxt
    return seen


def is_build(f):
    return f == "build.zig" or f.startswith("zig/build/")


def steps(contents):
    """step name -> root .zig files declared in the same build function."""
    res = defaultdict(set)
    for f, body in contents.items():
        if not (f == "build.zig" or f.startswith("zig/build/")):
            continue
        cuts = [m.start() for m in FN.finditer(body)] + [len(body)]
        for a, b in zip(cuts, cuts[1:]):
            chunk = body[a:b]
            names, roots = STEP.findall(chunk), ROOT.findall(chunk)
            for n in names:
                res[n].update(roots)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--pr", type=int)
    ap.add_argument("--old-head")
    ap.add_argument("--new-head", default="HEAD")
    ap.add_argument("--main", default="origin/main")
    a = ap.parse_args()
    d = os.path.expanduser(a.dir)
    old_head = a.old_head
    if a.pr and not old_head:
        old_head = json.loads(subprocess.run(["gh", "pr", "view", str(a.pr), "-R", "ashhart/TensorFold", "--json",
                                              "headRefOid"], capture_output=True, text=True).stdout)["headRefOid"]
    if not old_head:
        sys.exit("need --pr or --old-head")
    git(d, "cat-file", "-e", old_head + "^{commit}")
    new_head = git(d, "rev-parse", a.new_head).strip()
    old_base = git(d, "merge-base", old_head, a.main).strip()
    new_base = git(d, "merge-base", new_head, a.main).strip()
    if old_head == new_head:
        print("rebase-gates: old head == new head, nothing was rebased")
        return 0
    old_files = set(git(d, "diff", "--name-only", old_base, old_head).split())
    new_files = set(git(d, "diff", "--name-only", new_base, new_head).split())
    resolved = sorted(f for f in old_files | new_files
                      if patch_lines(d, old_base, old_head, f) != patch_lines(d, new_base, new_head, f))
    moved = set(git(d, "diff", "--name-only", old_base, new_base).split())
    g, contents = import_graph(d, new_head)
    pr_zig = [f for f in new_files if f.endswith(".zig") and not is_build(f)]
    pr_src = [f for f in pr_zig if not f.endswith("_test.zig") and "/tests/" not in f]
    reach = closure(g, pr_src)
    reach |= closure(g, [f for f in new_files if f.endswith((".cu", ".cuh", ".metal", ".h"))])
    under = sorted(f for f in moved if f not in new_files and not is_build(f) and f in reach)
    st = steps(contents)
    # steps whose roots reach a PR file within the depth limit; most specific (smallest reach) first
    scored = []
    for n, roots in st.items():
        if not n.startswith(("test", "check", "compile")) or not roots:
            continue
        r = closure(g, roots)
        k = len(r & set(pr_zig))
        if k:
            scored.append((-k / len(r), -k, n))     # share of the step's reach that the PR touches
    hit = [n for *_, n in sorted(scored)][:20]
    print(f"rebase-gates {old_head[:10]} -> {new_head[:10]}  base {old_base[:10]} -> {new_base[:10]}"
          f"  ({len(moved)} files moved on main, PR touches {len(new_files)})")
    dropped = sorted(old_files - new_files)
    if dropped:
        print(f"DROPPED from the PR ({len(dropped)}; landed on main or removed): " + " ".join(dropped[:12]))
    code_resolved = [f for f in resolved if not FIXTURE.search(f) and f in new_files and not is_build(f)]
    build_resolved = [f for f in resolved if is_build(f)]
    fix_resolved = [f for f in resolved if FIXTURE.search(f)]
    print(f"RESOLVED code ({len(code_resolved)}): " + (" ".join(code_resolved) or "-"))
    print(f"RESOLVED build files ({len(build_resolved)}, host compile of the named steps): "
          + (" ".join(build_resolved) or "-"))
    print(f"RESOLVED fixtures/docs ({len(fix_resolved)}): " + (" ".join(fix_resolved) or "-"))
    print(f"UNDER: main changed {len(under)} file(s) the PR's code reaches: " + (" ".join(under[:20]) or "-"))
    # second view: steps named after the PR's families and file stems (roots built in helpers are invisible above)
    generic = {"test", "tests", "host", "check", "src", "zig", "core", "cuda", "metal", "hip", "xpu", "the", "and",
               "families", "native", "server", "build", "mod", "main", "lib", "common", "kernels"}
    toks = defaultdict(int)
    for f in pr_src:
        parts = f[:-4].split("/")
        if "families" in parts and parts.index("families") + 1 < len(parts):
            toks[parts[parts.index("families") + 1]] += 3
        for w in re.split(r"[_/.]", parts[-1]):
            if len(w) > 2 and w not in generic:
                toks[w] += 1
    named = []
    for n in st:
        if n.startswith(("test", "check")):
            sc = sum(toks.get(w, 0) for w in n.split("-"))
            if sc >= 2:
                named.append((-sc, n))
    print(f"NAMED steps (by family/file words): " + (" ".join(n for _, n in sorted(named)[:20]) or "-"))
    print(f"STEPS ({len(scored)}, the 20 most specific): " + (" ".join(hit) or "- (none found: name the PR's own targets by hand)"))
    need = defaultdict(list)
    for f in code_resolved + under:
        need[backend(f)].append(f)
    for b in ("cuda", "metal", "hip", "xpu"):
        if need.get(b):
            print(f"VERDICT {b}: DEVICE rerun ({len(need[b])} file(s), e.g. {need[b][0]})")
    if need.get("host") and not any(need.get(b) for b in ("cuda", "metal", "hip", "xpu")):
        print("VERDICT: host code moved; host steps above, device rerun only if a backend calls it (check UNDER)")
    if not need:
        print("VERDICT: host steps only (only fixtures/docs moved, nothing under the PR changed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
