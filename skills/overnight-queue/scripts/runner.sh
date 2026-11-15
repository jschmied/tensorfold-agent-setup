#!/bin/bash
# Sequential job runner. Rescans jobs/ EVERY iteration -- the first version expanded the glob once,
# so a job added after it started was never seen, and the highest-value job of the night silently
# never ran. Markers in state/ make a restart resume rather than repeat.
#
# A job holds ~/ds41-queue/RUNNING while it owns the box. Nothing else may start a server: the first
# version let two jobs contend because a wait-job's sentinel matched a string its own tool prints.
set -u
Q=${QUEUE_DIR:-$HOME/ds41-queue}
echo "[runner] $(date '+%F %T') start, pid $$"
while :; do
  next=""
  for j in $(ls "$Q"/jobs/*.sh 2>/dev/null | sort); do
    n=$(basename "$j" .sh)
    [[ -f "$Q/state/$n.done" ]] || { next="$j"; break; }
  done
  [[ -z "$next" ]] && break
  n=$(basename "$next" .sh)
  echo "[runner] $(date '+%F %T') === $n ==="
  echo "$n" > "$Q/RUNNING"
  bash "$next" > "$Q/logs/$n.log" 2>&1
  rc=$?
  if [[ $rc -ne 0 && ! -f "$Q/state/$n.retried" ]]; then
    # A job that fails is usually a transient start (OOM under a profiler, a port still held).
    # Retry ONCE before writing it off -- the first runner marked failures done and moved on, so
    # last night's re-profile was silently skipped and nobody found out until morning.
    echo "[runner] $(date '+%F %T') $n FAILED rc=$rc -- retrying once"
    touch "$Q/state/$n.retried"
    sleep 20
    bash "$next" >> "$Q/logs/$n.log" 2>&1
    rc=$?
  fi
  rm -f "$Q/RUNNING"
  echo "$rc" > "$Q/state/$n.done"
  [[ $rc -ne 0 ]] && { touch "$Q/state/$n.failed"; echo "[runner] $(date '+%F %T') $n STILL FAILING rc=$rc"; }
  echo "[runner] $(date '+%F %T') $n finished rc=$rc"
done
echo "[runner] $(date '+%F %T') QUEUE DRAINED"
