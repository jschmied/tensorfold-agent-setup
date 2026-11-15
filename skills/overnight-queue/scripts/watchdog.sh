#!/bin/bash
# Watchdog for the unattended queue. Its goals are the failure modes this project has ACTUALLY hit,
# not just "is the runner alive" -- which is all the first version checked, and which is why a failed
# job and then a 6.5 h idle box both went unnoticed on the night of 2026-09-14.
#
#   1. PROGRESS, not liveness. A job whose log has not grown in 30 min is hung (a server that never
#      becomes healthy, a request with a 3600 s timeout). Kill it so the runner moves on and marks
#      it failed, instead of burning the night on one stuck arm.
#   2. PROTECT THE BOX. This is a 121 GiB unified-memory machine and GPU allocations are invisible
#      to cgroups, so nothing can cap the server (memory: gb10-oom-protection). If MemAvailable
#      falls under the floor, stop the server ourselves -- the alternative is the OOM killer taking
#      sshd and the session with it.
#   3. PROTECT THE DISK. An nsys report is ~200 MB and its sqlite export 1-3 GB, and the root fs was
#      already 85 % full. Sqlite exports are regenerable from the report, so they are the first to
#      go; reports themselves only if it gets dire.
#   4. NEVER LEAVE THE BOX IDLE OR UNSERVED. On drain, say so and keep looping: a job added later is
#      picked up. If nothing is queued and no server is up, restore the shipped default.
#   5. LEAVE A STATUS FILE. One read of ~/ds41-queue/STATUS tells the next session what is running,
#      for how long, what failed, and how much memory and disk are left.
#
# It never decides WHAT to run -- that is the heartbeat's job. It only keeps the box in a state
# where the next decision is still possible.
set -u
Q=${QUEUE_DIR:-$HOME/ds41-queue}
R=${SERVER_DIR:-$HOME/git/deepseek-v41-flash-spark}
STALL_MIN=30          # no log growth for this long = hung
MEM_FLOOR_GB=8        # below this, stop the server before the kernel starts choosing victims
DISK_FLOOR_GB=40
DEADLINE=$(( $(date +%s) + 12*3600 ))
log() { echo "[wd] $(date '+%F %T') $*"; }
log "start, pid $$, stall ${STALL_MIN}m, mem floor ${MEM_FLOOR_GB}G, disk floor ${DISK_FLOOR_GB}G"

announced=""
while [[ $(date +%s) -lt $DEADLINE ]]; do
  running=$(cat "$Q/RUNNING" 2>/dev/null || true)
  mem=$(awk '/^MemAvailable:/ {printf "%d", $2/1048576}' /proc/meminfo)
  disk=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
  failed=$(ls "$Q"/state/*.failed 2>/dev/null | wc -l)
  runner_up=$(ps -eo args --no-headers | grep -c "^bash $Q/runner\.sh$" || true)
  servers=$(pgrep -cf 'server/app\.p[y]' || true); servers=${servers:-0}

  { echo "updated   $(date '+%F %T')"
    echo "running   ${running:-<idle>}"
    echo "runner    $([[ $runner_up -gt 0 ]] && echo alive || echo DEAD)"
    echo "servers   $servers"
    echo "mem_avail ${mem} GiB"
    echo "disk_free ${disk} GiB"
    echo "failed    $failed"
  } > "$Q/STATUS"

  # 2. box protection first -- everything else is moot if the box wedges
  if (( mem < MEM_FLOOR_GB )); then
    log "MemAvailable ${mem} GiB below floor -- stopping the server before the OOM killer picks"
    (cd "$R" && ./stop.sh --force >> "$Q/logs/wd.log" 2>&1)
    [[ -n "$running" ]] && touch "$Q/state/$running.failed"
  fi

  # 3. disk: sqlite exports are regenerable from the .nsys-rep, so they go first
  if (( disk < DISK_FLOOR_GB )); then
    old=$(ls -t "$Q"/logs/*.sqlite 2>/dev/null | tail -1)
    if [[ -n "$old" ]]; then
      log "disk ${disk} GiB below floor -- removing regenerable export $(basename "$old")"
      rm -f "$old"
    else
      log "disk ${disk} GiB below floor and no exports left to reclaim -- NOT deleting reports"
    fi
  fi

  # 1. progress, not liveness
  if [[ -n "$running" && -f "$Q/logs/$running.log" ]]; then
    age=$(( ($(date +%s) - $(stat -c %Y "$Q/logs/$running.log")) / 60 ))
    if (( age >= STALL_MIN )); then
      log "job $running has not written a line in ${age} min -- killing it so the queue moves on"
      touch "$Q/state/$running.failed"
      (cd "$R" && ./stop.sh --force >> "$Q/logs/wd.log" 2>&1)
      pkill -f "$Q/jobs/$running\.sh" 2>/dev/null || true
    fi
  fi

  # Never two servers -- but ONLY when no job owns the box. Every job stops the server and starts
  # its own, so during a job a second server is a transient the job is already resolving. Acting on
  # it killed the job's own server and failed the run (2026-09-15 08:28). While a job is RUNNING,
  # server management belongs entirely to the job.
  if (( servers > 1 )) && [[ -z "$running" ]]; then
    if [[ -n "${two_seen:-}" ]]; then
      log "two servers for two consecutive checks and no job running -- stopping all"
      (cd "$R" && ./stop.sh --force >> "$Q/logs/wd.log" 2>&1)
      two_seen=""
    else
      two_seen=1
    fi
  else
    two_seen=""
  fi

  # 4. idle / drained
  if [[ "$(tail -1 "$Q/logs/runner.log" 2>/dev/null)" == *"QUEUE DRAINED"* ]]; then
    pending=0
    for j in "$Q"/jobs/*.sh; do
      [[ -e "$j" ]] || continue
      n=$(basename "$j" .sh); [[ -f "$Q/state/$n.done" ]] || pending=1
    done
    if (( pending )); then
      log "new job queued -> restarting runner"; announced=""
      setsid env PYTHONUNBUFFERED=1 bash "$Q/runner.sh" >> "$Q/logs/runner.log" 2>&1 < /dev/null &
    else
      if [[ -z "$announced" ]]; then
        log "QUEUE IDLE -- ${failed} failed; heartbeat should queue more work"
        announced=1
      idle_seen=""
      fi
      # Restore only after the queue has been idle for two consecutive checks. Restoring
      # immediately raced a job being queued: the restored server was still loading weights when
      # the new job started its own, and the pair tripped the two-server rule.
      if (( servers == 0 )); then
        if [[ -n "${idle_seen:-}" ]]; then
          log "idle and unserved for two checks -> restoring the shipped default"
          (cd "$R" && ./start.sh >> "$Q/logs/wd-restore.log" 2>&1)
          idle_seen=""
        else
          idle_seen=1
        fi
      fi
    fi
  elif (( runner_up == 0 )); then
    log "runner not alive mid-queue -> restarting"; announced=""
    setsid env PYTHONUNBUFFERED=1 bash "$Q/runner.sh" >> "$Q/logs/runner.log" 2>&1 < /dev/null &
  fi
  sleep 60
done
log "12 h deadline reached, exiting"
