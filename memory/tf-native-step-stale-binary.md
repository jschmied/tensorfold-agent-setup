---
name: TF native binary needs the `native` step
description: plain `zig build` does not rebuild zig-out/native/bin/tensorfold-native; served gates ran on a stale binary for hours
type: feedback
---
`zig build -Dnvcc=... -Doptimize=ReleaseSafe` in a TensorFold worktree rebuilds zig-out/bin (tf-cuda-test etc.) but NOT
`zig-out/native/bin/tensorfold-native`. Build with `zig build native -Dnvcc=... -Doptimize=ReleaseSafe`.

**Why:** 2026-10-28, #1492/#1503: three "new" binaries (tf-n1, tf-n2, tf-p3) were byte-identical to older ones
(md5 equal), so a rebase gate and a cold-turn fix "showed no effect". Found only via nsys kernel names
(old `tf_lfm2m_conv` instead of `tf_liquid_conv_3`).

**How to apply:** after copying a served binary, md5sum it against the previous one; if equal, the build was stale.
Related: LFM2.5's +65 ms cold chat turn on #1503 was mark-split prompt passes (12 vs 10 passes, nsys prefill
launch count), not snapshot allocation and not copies (DtoD 115 GB/s on GB10, 200 MB = 1.8 ms). Fixed by tapping marks.
