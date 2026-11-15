#!/usr/bin/env python3
"""Claude usage overview from ~/.claude/usage-history.jsonl (written by the status line script).

usage-report.py            current state, burn rates, projection, hourly table of the last 24 h
usage-report.py --days 7   daily summary plus the hourly table of the last 7 days
usage-report.py --json     machine-readable verdict for the self-management skill
"""
import argparse, json, os, time
from collections import OrderedDict

HIST = os.path.expanduser("~/.claude/usage-history.jsonl")


def load():
    rows = []
    try:
        with open(HIST) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("d7") is not None:
                    rows.append(r)
    except FileNotFoundError:
        pass
    rows.sort(key=lambda r: r["at"])
    return rows


def at_or_before(rows, t):
    best = None
    for r in rows:
        if r["at"] <= t:
            best = r
        else:
            break
    return best


def delta_d7(rows, t0, t1):
    """Increase of the 7-day percentage between t0 and t1; resets (drops) count from 0."""
    seg = [r for r in rows if t0 <= r["at"] <= t1]
    a = at_or_before(rows, t0)
    if a:
        seg = [a] + seg
    if len(seg) < 2:
        return None
    up = 0.0
    for p, q in zip(seg, seg[1:]):
        d = q["d7"] - p["d7"]
        up += d if d >= 0 else q["d7"]  # window reset: count usage since reset
    return up


def fmt_dur(s):
    if s is None or s < 0:
        return "-"
    d, h, m = int(s // 86400), int(s % 86400 // 3600), int(s % 3600 // 60)
    return f"{d}d{h}h" if d else (f"{h}h{m:02d}m" if h else f"{m}m")


def verdict(rows, now):
    if not rows:
        return {"state": "unknown", "reason": "no history yet"}
    cur = rows[-1]
    age = now - cur["at"]
    left = 100 - cur["d7"]
    to_reset = (cur["d7_reset"] or now) - now
    rates = {}
    for name, hrs in (("1h", 1), ("6h", 6), ("24h", 24)):
        d = delta_d7(rows, now - hrs * 3600, now)
        rates[name] = None if d is None else d / hrs
    # budget per hour that lands exactly at 100 % on reset
    allowed = left / max(to_reset / 3600, 0.25)
    # Token-based estimate: units since the 7-day window opened map to the current percentage.
    cal = None
    if cur["d7_reset"] and cur["d7"]:
        hrs = token_hours(8, now)
        w0 = cur["d7_reset"] - 7 * 86400
        units = sum(e["main"] + e["sub"] for h, e in hrs.items() if h >= w0)
        if units:
            per_pct = units / cur["d7"]
            tok = {}
            for name, n in (("1h", 1), ("6h", 6), ("24h", 24)):
                u = sum(e["main"] + e["sub"] for h, e in hrs.items() if h >= now - n * 3600)
                tok[name] = round(u / per_pct / n, 2)
            sub6 = sum(e["sub"] for h, e in hrs.items() if h >= now - 6 * 3600)
            all6 = sum(e["main"] + e["sub"] for h, e in hrs.items() if h >= now - 6 * 3600)
            cal = {"munits_per_pct": round(per_pct / 1e6, 2), "tok_rate_pct_per_h": tok,
                   "subagent_share_6h": round(sub6 / all6, 2) if all6 else None}
            # The % history is whole percents, so a slow hour reads 0; take the larger of the two
            # (tokens miss other machines, % misses sub-1 % steps).
            for k in rates:
                rates[k] = tok[k] if rates[k] is None else max(rates[k], tok[k])
    rate = next((rates[k] for k in ("6h", "1h", "24h") if rates[k] is not None), None)
    proj = None if rate is None else cur["d7"] + rate * to_reset / 3600
    if cur["d7"] >= 95 or (cur["h5"] or 0) >= 95:
        state = "stop"
    elif proj is not None and proj > 125:  # user 2026-11-06: allow a bit more; the real limit stays 100 % at reset
        state = "throttle"
    elif proj is not None and proj > 100:
        state = "careful"
    else:
        state = "ok"
    return {
        "state": state, "d7": cur["d7"], "h5": cur["h5"], "sample_age_s": age,
        "d7_reset_in": fmt_dur(to_reset), "h5_reset_in": fmt_dur((cur["h5_reset"] or now) - now),
        "rate_pct_per_h": rates, "allowed_pct_per_h": round(allowed, 2),
        "projected_d7_at_reset": None if proj is None else round(proj, 1),
        "token_calibration": cal,
        "note": "rates fall back to transcript tokens (this machine only) where % history is missing",
    }


def hourly(rows, now, hours):
    out = OrderedDict()
    start = (now // 3600 - hours + 1) * 3600
    for t in range(int(start), int(now) + 1, 3600):
        d = delta_d7(rows, t, min(t + 3600, now))
        r = at_or_before(rows, min(t + 3600, now))
        out[t] = (d, r["d7"] if r else None, r["h5"] if r else None)
    return out


# Relative weights (input token = 1), from list prices: cache write 1h = 2x, 5m = 1.25x, read = 0.1x, output = 5x.
W = {"in": 1.0, "cw1h": 2.0, "cw5m": 1.25, "cr": 0.1, "out": 5.0}


def token_hours(days, now):
    """Weighted token units per UTC hour from the transcripts, split main vs subagent; deduped by message id."""
    import glob, datetime
    root = os.path.expanduser("~/.claude/projects")
    since = now - days * 86400
    seen, hours = set(), {}
    for path in glob.glob(f"{root}/**/*.jsonl", recursive=True):
        if os.path.getmtime(path) < since:
            continue
        kind = "sub" if "/subagents/" in path else "main"
        with open(path, errors="replace") as f:
            for line in f:
                if '"usage"' not in line or '"assistant"' not in line:
                    continue
                try:
                    d = json.loads(line)
                    m = d["message"]
                    u = m["usage"]
                    ts = datetime.datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).timestamp()
                except (ValueError, KeyError, TypeError):
                    continue
                if ts < since or m.get("id") in seen:
                    continue
                seen.add(m.get("id"))
                cc = u.get("cache_creation") or {}
                c1 = cc.get("ephemeral_1h_input_tokens", 0)
                c5 = cc.get("ephemeral_5m_input_tokens", u.get("cache_creation_input_tokens", 0) - c1)
                units = (u.get("input_tokens", 0) * W["in"] + c1 * W["cw1h"] + c5 * W["cw5m"]
                         + u.get("cache_read_input_tokens", 0) * W["cr"] + u.get("output_tokens", 0) * W["out"])
                h = int(ts // 3600 * 3600)
                e = hours.setdefault(h, {"main": 0.0, "sub": 0.0, "msgs": 0})
                e[kind] += units
                e["msgs"] += 1
    return hours


def print_tokens(days, now):
    hrs = token_hours(days, now)
    M = 1e6
    print(f"\nweighted tokens (M units, input=1 out=5 cw1h=2 cr=0.1), last {days} d, from transcripts")
    print("day (UTC)      main    sub   total  msgs  peak hour")
    for k in range(days - 1, -1, -1):
        t0 = (now // 86400 - k) * 86400
        hs = {h: e for h, e in hrs.items() if t0 <= h < t0 + 86400}
        mn = sum(e["main"] for e in hs.values()) / M
        sb = sum(e["sub"] for e in hs.values()) / M
        n = sum(e["msgs"] for e in hs.values())
        pk = max(hs.items(), key=lambda kv: kv[1]["main"] + kv[1]["sub"], default=None)
        pks = f"{time.strftime('%H:00', time.gmtime(pk[0]))} {(pk[1]['main'] + pk[1]['sub']) / M:.1f}" if pk else "-"
        print(f"{time.strftime('%a %m-%d', time.gmtime(t0))}  {mn:6.1f} {sb:6.1f} {mn + sb:7.1f} {n:5d}  {pks}")
    return hrs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tokens", action="store_true", help="add the transcript token overview (slow, ~30 s)")
    a = ap.parse_args()
    now = time.time()
    if a.tokens:
        print_tokens(a.days, now)
    rows = load()
    v = verdict(rows, now)
    if a.json:
        print(json.dumps(v))
        return
    if v["state"] == "unknown":
        print("no usage history yet:", HIST)
        return
    r = v["rate_pct_per_h"]
    f = lambda x: "-" if x is None else f"{x:.2f}"
    print(f"7d {v['d7']}% (reset in {v['d7_reset_in']})   5h {v['h5']}% (reset in {v['h5_reset_in']})"
          f"   sample {fmt_dur(v['sample_age_s'])} old")
    print(f"7d burn %/h: 1h {f(r['1h'])}  6h {f(r['6h'])}  24h {f(r['24h'])}   "
          f"budget to reset {v['allowed_pct_per_h']:.2f}%/h   projected at reset "
          f"{v['projected_d7_at_reset']}%   => {v['state'].upper()}")
    c = v.get("token_calibration")
    if c:
        print(f"calibration: {c['munits_per_pct']} M units per 1 % (this machine's transcripts since the window opened); "
              f"subagent share 6h {c['subagent_share_6h']}")
    if a.days > 1:
        print("\nday (UTC)    7d added  7d at end")
        for k in range(a.days - 1, -1, -1):
            t1 = (now // 86400 - k + 1) * 86400
            t0 = t1 - 86400
            d = delta_d7(rows, t0, min(t1, now))
            e = at_or_before(rows, min(t1, now))
            print(f"{time.strftime('%a %m-%d', time.gmtime(t0))}   {f(d):>8}  {e['d7'] if e else '-':>9}")
    print("\nhour (UTC)        7d +%   7d    5h")
    for t, (d, d7, h5) in hourly(rows, now, 24 * a.days).items():
        if d is None and d7 is None:
            continue
        bar = "#" * int(round((d or 0) * 4))
        print(f"{time.strftime('%a %m-%d %H:00', time.gmtime(t))}  {f(d):>6}  {d7 if d7 is not None else '-':>4}  "
              f"{h5 if h5 is not None else '-':>4}  {bar}")


if __name__ == "__main__":
    main()
