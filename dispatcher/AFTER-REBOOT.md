# After the reboot (GPU Xid 120 at 2026-11-05 22:31)
1. nvidia-smi: GB10 healthy (no "requires reset"); gpu-clock-cap.service active.
2. tmux `dispatch` up (restart loop) — start it if the reboot dropped it.
3. mv ~/notes/jobs/hold/*.json ~/notes/jobs/q/   (22 GPU jobs: l2pf, pt-nsys-*, sw-ident/abba-*)
4. Resume the agents (statewalk, prompt-tail, l2pf) — state in ~/notes/ledger/<task>/STATUS.md.
5. Re-run solo-nemo-abba (solo-chunks, ~/notes/ledger/solo-chunks/PLAN.md) and the recurrent-pool contract with a longer limit if wanted.
6. asr2239-build + asr2239-gate-06B/-17B (in hold/, #2239 review re-gate): results in ~/notes/2105/gate-review/{0.6B,1.7B}; reply to shuuul on #2239 with them.

## Night-only: #2005 placement run (user 11-06)
GB10 + Mac across two machines, only when the queue is empty, replies are done and the Mac is idle.
Needs a Metal stage binding first. Comes after HY items? Ask if both are ready.
- spark-dash: SUDO_ASKPASS=~/.sudo-askpass sudo -A systemd-run --unit=spark-dash --uid=1000 --gid=1000 -p Restart=always -p RestartSec=5 --setenv=HOME=/home/jschmied /usr/bin/python3 -u /home/jschmied/notes/dash/server.py
