#!/usr/bin/env python3
"""GB10 job dispatcher: agents drop a job file, this starts it when it is ready and its lane is free.

Job file ~/notes/jobs/q/<id>.json:
  {"id": "e4b-ple", "owner": "<agent id>", "lane": "timing" | "correct" | "build", "prio": 10,
   "mem_gb": 20, "cwd": "~/git/tf-e4b-cuda", "cmd": "zig-out/bin/tf-cuda-test gemma4-ple",
   "ready": "test -x zig-out/bin/tf-cuda-test", "quiet_min": 10, "deadline_min": 60}
Lanes: timing holds gpu.lock exclusive; correct holds it shared (runs beside other correct jobs, never beside timing);
build takes a tfb build slot; x86 runs host-only checks on tfci@<x86-host> (one at a time, no lock, no slot: it
pushes "sha" to /srv/tf.git and runs cmd in a fresh worktree there via /srv/tf-run). Higher prio first; a waiting
timing job stops new correct jobs from starting.
Every state change is one line in ~/notes/jobs/events.log (START, DONE, FAIL, QUIET, TIMEOUT, BADJOB), which a
Monitor tails, so a crash or a hang reaches the main session within seconds. Logs land in ~/notes/jobs/done/<id>.log.
"""
import fcntl, json, os, re, shlex, signal, subprocess, time

J = os.path.expanduser("~/notes/jobs")
GPU = "/tmp/claude-1000/gpu.lock"
TFB = os.path.expanduser("~/bin/tfb")
X86 = "tfci@<x86-host>"  # unprivileged: root passes the tests that expect a chmod 000 to refuse
X86_SSH = "ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=4 " + X86
X86_ID = re.compile(r"^[A-Za-z0-9._-]+$")
running = {}  # id -> (job, Popen, log path, start time)
stalled = set()  # queued jobs already reported as waiting too long


def ev(msg):
    with open(f"{J}/events.log", "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def avail_gb():
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable"):
            return int(line.split()[1]) // 1048576
    return 0


def tail(p, n=6):
    try:
        return " | ".join(open(p, errors="replace").read().strip().splitlines()[-n:])[-600:]
    except OSError:
        return ""


def lock_free(shared):
    """Whether gpu.lock could be taken now (a holder outside the dispatcher counts too)."""
    with open(GPU, "a") as f:
        try:
            fcntl.flock(f, (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False


def slot_free():
    """Whether one of tfb's two build slots could be taken now."""
    for path in ("/tmp/claude-1000/tfbuild.lock", "/tmp/claude-1000/tfbuild.1.lock"):
        with open(path, "a") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                pass
    return False


def slots_idle():
    """Whether no build holds either tfb slot (timing runs alone, builds included)."""
    for path in ("/tmp/claude-1000/tfbuild.lock", "/tmp/claude-1000/tfbuild.1.lock"):
        with open(path, "a") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
    return True


def queued_at(j):
    """When the job file was queued; a file withdrawn meanwhile sorts last."""
    try:
        return os.path.getmtime(f"{J}/q/{j['id']}.json")
    except OSError:
        return float("inf")


def ready(j):
    r = j.get("ready")
    if not isinstance(r, str):  # a non-command ready (true/1) must not crash the loop for every queued job
        return bool(r) or r is None
    return not r or subprocess.run(r, shell=True, cwd=os.path.expanduser(j["cwd"])).returncode == 0


def x86_cmd(j):
    """Push the job's commit (and origin/main, for merge bases) to the x86 mirror, then run cmd there."""
    cwd, sha, dl = os.path.expanduser(j["cwd"]), j["_sha"], int(j.get("deadline_min", 60)) * 60
    os.makedirs(f"{J}/x86", exist_ok=True)
    cf = f"{J}/x86/{j['id']}.cmd"
    with open(cf, "w") as f:
        f.write(j["cmd"])
    refs = f"{sha}:refs/heads/job/{j['id']}"
    if subprocess.run(["git", "-C", cwd, "rev-parse", "-q", "--verify", "refs/remotes/origin/main"],
                      capture_output=True).returncode == 0:
        refs += " refs/remotes/origin/main:refs/remotes/origin/main"
    push = f"GIT_SSH_COMMAND={shlex.quote(X86_SSH.rsplit(' ', 1)[0])} git -C {shlex.quote(cwd)} push -q -f {X86}:/srv/tf.git {refs}"
    run = f"{push} && {X86_SSH} /srv/tf-run {j['id']} {dl} < {cf}"
    return f"timeout {dl + 300} bash -c {shlex.quote(run)}"


def x86_kill(i):
    """Stop the remote side of an x86 job (its session, by pid) and remove its worktree; harmless if it ended."""
    subprocess.run(f"timeout 120 {X86_SSH} /srv/tf-run --kill {i}", shell=True, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start(j):
    log = f"{J}/done/{j['id']}.log"
    lane = j["lane"]
    if lane == "x86":
        p = subprocess.Popen(x86_cmd(j), shell=True, stdout=open(log, "w"), stderr=subprocess.STDOUT,
                             start_new_session=True, stdin=subprocess.DEVNULL, pass_fds=())
        os.replace(f"{J}/q/{j['id']}.json", f"{J}/run/{j['id']}.json")
        running[j["id"]] = (j, p, log, time.time())
        ev(f"START {j['id']} lane=x86 pid={p.pid} sha={j['_sha'][:12]} owner={j.get('owner', '?')}")
        return
    wrap = {"timing": f"flock {GPU} ", "correct": f"flock -s {GPU} ", "build": f"{TFB} "}[lane]
    cmd = f"{wrap}timeout {int(j.get('deadline_min', 60)) * 60} bash -c {shlex.quote(j['cmd'])}"
    env = dict(os.environ, PATH=os.path.expanduser("~/opt/zig-aarch64-linux-0.17.0:~/bin:/usr/local/cuda/bin:")
               + os.environ.get("PATH", ""))
    p = subprocess.Popen(cmd, shell=True, cwd=os.path.expanduser(j["cwd"]), stdout=open(log, "w"), env=env,
                         stderr=subprocess.STDOUT, start_new_session=True, stdin=subprocess.DEVNULL, pass_fds=())
    os.replace(f"{J}/q/{j['id']}.json", f"{J}/run/{j['id']}.json")
    running[j["id"]] = (j, p, log, time.time())
    ev(f"START {j['id']} lane={lane} pid={p.pid} owner={j.get('owner', '?')}")


def finish(i, rc, why=None):
    j, p, log, t0 = running.pop(i)
    if j["lane"] == "x86" and rc != 0:
        x86_kill(i)
    os.replace(f"{J}/run/{i}.json", f"{J}/done/{i}.json")
    mins = (time.time() - t0) / 60
    if why:
        ev(f"{why} {i} after {mins:.0f} min owner={j.get('owner', '?')}: {tail(log)}")
    elif rc == 0:
        ev(f"DONE {i} rc=0 {mins:.0f} min owner={j.get('owner', '?')}")
    else:
        ev(f"FAIL {i} rc={rc} {mins:.0f} min owner={j.get('owner', '?')}: {tail(log)}")


def session(sid):
    """Every pid in session `sid`: `timeout` moves its child to a new process group, so a group kill misses it."""
    out = []
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                if os.getsid(int(d)) == sid:
                    out.append(int(d))
            except OSError:
                pass
    return out


def kill(p):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in session(p.pid):
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        time.sleep(10)


def step():
    for i, (j, p, log, t0) in list(running.items()):
        rc = p.poll()
        if rc is not None:
            finish(i, rc, "TIMEOUT" if rc == 124 else None)
            continue
        quiet = j.get("quiet_min", 30 if j["lane"] in ("build", "x86") else 10) * 60
        if time.time() - max(os.path.getmtime(log), t0) > quiet:
            kill(p)
            p.wait()
            finish(i, -9, "QUIET")
    jobs = []
    for f in sorted(os.listdir(f"{J}/q")):
        if not f.endswith(".json"):
            continue
        try:
            j = json.load(open(f"{J}/q/{f}"))
            assert j["id"] == f[:-5] and j["lane"] in ("timing", "correct", "build", "x86") and j["cmd"] and j["cwd"]
            assert len(j["cmd"]) < 64000, f"cmd is {len(j['cmd'])} bytes; put it in a script file (E2BIG)"
            if j["lane"] == "x86":
                assert X86_ID.match(j["id"]) and j.get("sha"), "x86 needs a plain id and a sha"
                r = subprocess.run(["git", "-C", os.path.expanduser(j["cwd"]), "rev-parse", "--verify", "-q",
                                    j["sha"] + "^{commit}"], capture_output=True, text=True)
                assert r.returncode == 0, f"sha {j['sha']} not reachable from {j['cwd']}"
                j["_sha"] = r.stdout.strip()
        except Exception as e:  # a broken job file is reported once, then parked
            os.replace(f"{J}/q/{f}", f"{J}/done/{f}.bad")
            ev(f"BADJOB {f}: {e}")
            continue
        jobs.append(j)
    jobs.sort(key=lambda j: (-j.get("prio", 0), queued_at(j)))
    if os.path.exists(f"{J}/PAUSE"):  # restart aid: running jobs finish, nothing new starts
        jobs = []  # same prio: oldest first, not file-name order
    lanes = [r[0]["lane"] for r in running.values()]
    # a ready timing job that fits holds back builds and correct jobs queued after it at its prio, and all lower prios;
    # same prio is FIFO, so a stream of timing work can no longer starve an older build (sampler4 waited 18 h, 11-11)
    waiting = [t for t in jobs if t["lane"] == "timing" and ready(t) and avail_gb() >= t.get("mem_gb", 20) + 20]

    def held(j):
        return any(t.get("prio", 0) > j.get("prio", 0)
                   or (t.get("prio", 0) == j.get("prio", 0) and queued_at(t) <= queued_at(j)) for t in waiting)
    for j in jobs:
        lane = j["lane"]
        if lane == "x86":  # its own box: no gpu.lock, no build slot, no memory or drain rule; one at a time
            if "x86" not in lanes and ready(j):
                start(j)
                lanes.append(lane)
            continue
        if lane == "timing" and ("timing" in lanes or "correct" in lanes or "build" in lanes or not slots_idle()):
            continue
        if lane == "build" and ("timing" in lanes or held(j)):
            continue
        if lane == "correct" and ("timing" in lanes or held(j)):
            continue
        if lane == "build" and lanes.count("build") >= 2:
            continue
        if lane != "build" and avail_gb() < j.get("mem_gb", 20) + 20:
            continue
        if lane != "build" and not lock_free(lane == "correct"):
            continue
        if lane == "build" and not slot_free():
            continue
        if not ready(j):
            age = time.time() - os.path.getmtime(f"{J}/q/{j['id']}.json")
            if age > 1200 and j["id"] not in stalled:
                stalled.add(j["id"])
                ev(f"STALL {j['id']} not ready after {age / 60:.0f} min owner={j.get('owner', '?')}: {j.get('ready', '')[:120]}")
            continue
        start(j)
        lanes.append(lane)


if __name__ == "__main__":
    ev(f"DISPATCHER up pid={os.getpid()}")
    for f in os.listdir(f"{J}/run"):  # jobs a previous dispatcher started: their processes may still run
        os.replace(f"{J}/run/{f}", f"{J}/done/{f}.orphan")
        ev(f"ORPHAN {f[:-5]}: started by a previous dispatcher, not watched; check its log")
    while True:
        try:
            step()
        except Exception as e:
            ev(f"DISPATCHER error {e!r}")
        time.sleep(5)
