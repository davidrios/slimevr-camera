# WHAM: Reconstructing World-grounded Humans with Accurate 3D Motion

- **Authors / venue / year:** Soyong Shin, Juyong Kim, Eni Halilaj, Michael J. Black — CVPR 2024 (arXiv Dec 2023)
- **Link:** https://arxiv.org/abs/2312.07531
- **Code:** https://github.com/yohanshin/WHAM — MIT. PyTorch, CUDA required. Needs ViTPose (2D keypoints), DPVO or DROID-SLAM (camera angular velocity; can be skipped with `--estimate_local_only` for camera-frame output, or replaced by a gyroscope), SMPL (MPI registration). Intrinsics optional (CLIFF-style focal guess by default; can pass fx fy cx cy).
- **Read depth:** abstract + skimmed HTML (Tables 1, 3; inputs; runtime)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

First fast, learned, **world-frame** SMPL-from-video model: outputs joint rotations plus a gravity-aligned global trajectory. Temporal (RNN over keypoint + image-feature sequence), so limb orientations are smoother than per-frame HMR2.0. Also: it explicitly fuses camera angular velocity, which for a *static* camera is simply zero — our case is its easy case.

## What they do

Lift a sequence of 2D keypoints (ViTPose) to a motion feature via an RNN pretrained on AMASS; fuse with HMR2.0 image features; decode SMPL pose/shape per frame in camera coordinates, plus a global-trajectory decoder that autoregressively predicts root orientation & velocity using the camera's angular velocity from SLAM. Contact-aware refinement removes foot skating. Trained on AMASS + 3DPW/H36M/MPI-INF/InstaVariety.

## Key numbers (with table/figure reference)

- Table 1 (camera-frame, ViT): 3DPW PA-MPJPE 35.9 / MPJPE 57.8 / PVE 68.7 mm, Accel 6.6; RICH 44.3 / 80.0 / 91.2; EMDB 50.4 / 79.7 / 94.4.
- Table 3 (EMDB 2, world): WA-MPJPE₁₀₀ 133.3 mm, W-MPJPE₁₀₀ 343.9 mm, RTE 4.6 %, jitter 21.5, foot sliding 4.4 mm.
- Runtime: core net ~200 fps; full pipeline 8.8 fps (bs 1) → 49 fps (bs 64) incl. ViTPose+SLAM.
- **No MPJAE / global orientation error reported.** GVHMR Fig. 9 shows WHAM's global orientation error *accumulates* with sequence length (autoregressive drift) — the exact failure mode we want a camera to be free of.

## What we can reuse / what to be careful about

- Reuse: MIT; static-camera mode; the motion prior smooths limb directions over exactly the still windows we gate on.
- Careful: the world heading is autoregressively integrated → drifts on long clips (GVHMR Fig. 9); for our purpose use camera-frame output + our own extrinsics rather than WHAM's world frame. Per-joint rotation quality is inherited from HMR2.0 features + AMASS prior; unmeasured.

## Open questions this raises

- With a static camera and ω = 0, does the world heading still drift, or is drift driven only by camera-motion integration?
- MPJAE per joint on EMDB for WHAM vs HMR2.0 — does the temporal prior reduce twist error or just jitter?
