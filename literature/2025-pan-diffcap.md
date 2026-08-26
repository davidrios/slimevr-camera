# DiffCap: Diffusion-based Real-time Human Motion Capture using Sparse IMUs and a Monocular Camera

- **Authors / venue / year:** Shaohua Pan, Xinyu Yi, Yan Zhou, Weihua Jian, Yuan Zhang, Pengfei Wan, Feng Xu — arXiv 2508.06139 (submitted 2025-08-08, journal-style preprint; venue not stated, CC BY 4.0)
- **Link:** https://arxiv.org/abs/2508.06139 ; project https://shaohua-pan.github.io/diffcap-page
- **Code:** https://github.com/shaohua-pan/DiffCap — MIT, PyTorch (CUDA), checkpoints on Google Drive, live demo with 6 Noitom IMUs + Logitech webcam, MediaPipe; two-laptop demo at 60 fps with 0.5 s latency (RTX 2080 Super).
- **Read depth:** full read (arXiv v1 PDF, text-extracted; supplementary with calibration details not read)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Direct successor of RobustCap from the same group: same 6-IMU + monocular setting, replaces the hand-tuned confidence switching with a diffusion model. Confirms the setting is active in 2025 and gives the best current monocular+6-IMU pose numbers. Still no explicit yaw-drift estimate and still magnetic-drift-agnostic.

## What they do

Inputs per 60-frame window: MediaPipe 2D keypoints + confidences (root-normalised, on the z=1 plane) and 6 IMU accelerations/orientations. Same calibration of IMU frame to camera frame as RobustCap (supplementary). Two transformer-encoder diffusion models: a **Joint Diffusion Model** (3D joint positions) and a **Pose Diffusion Model** (6D joint rotations). Key design (Sec. III-B): the 2D keypoint sequence is compressed into a *single condition embedding* (robust to frames where vision is missing), while IMU measurements are concatenated frame-by-frame with the noisy pose (Table III shows this split matters: 60.5 vs 71.1 mm on 3DPW-OCC). Sliding window of 60 with 30-frame overlap and linear blending, 5 DDIM steps. Translation is taken from RobustCap's module unchanged. Mean body shape.

Drift handling: implicit only — the diffusion prior plus vision condition; no per-sensor heading variable. Limitations section: "The IMU measurements may be influenced by magnetic disturbances … how to model the magnetic disturbance and subtract it from the IMU input … is still an open question."

## Key numbers (with table/figure reference)

Table I (MPJPE / PA-MPJPE / PVE mm):

| Dataset | RobustCap | RobustCap (biRNN, offline) | DiffCap |
|---|---|---|---|
| 3DPW | 55.0 / 38.9 / 71.8 | 53.6 / 38.6 / 69.7 | **46.9 / 33.5 / 65.9** |
| 3DPW-OCC | 77.9 / 53.1 / 97.5 | 76.8 / 52.5 / 96.2 | **60.5 / 43.1 / 85.6** |
| AIST++ | 33.1 / 24.0 / 43.2 | 32.0 / 22.8 / 41.5 | **31.0 / 21.2 / 40.5** |
| TotalCapture | 48.7 / 33.5 / 63.4 | 48.1 / 32.7 / 62.1 | **46.2 / 29.9 / 60.9** |

- Table V (robustness to 2D keypoint noise on AIST++, σ on z=1 plane): at σ=0.1 RobustCap 33.1→42.3 mm, DiffCap 31.0→32.7 mm.
- Table IV: 1 vs 5 vs 10 denoising steps: 32.7 / 31.0 / 31.0 mm — one step is nearly as good.
- **No angular / heading error reported.** Jitter not quantified numerically (they admit "non-physical artifacts such as jitter").

## What we can reuse / what to be careful about

- Evidence that a **whole-window visual embedding** is the right way to consume intermittent camera evidence — matches our "still-moment windows" idea better than per-frame fusion.
- MIT code with the same evaluation harness as RobustCap; a modern baseline to compare any yaw-correction scheme against on TotalCapture.
- Careful: gains over RobustCap on real-IMU TotalCapture are small (48.7→46.2 mm); most of the benefit is occlusion robustness on synthetic-IMU 3DPW-OCC.
- Careful: 60-frame windows + diffusion transformer; heavier than what an end-user CPU path wants, though 5 DDIM steps at 60 fps on a laptop GPU is reported.

## Open questions this raises

- If the network is fed IMUs with an injected constant yaw offset per sensor, how much does the output degrade? That would tell us whether learned fusion "absorbs" yaw drift or needs an explicit correction first. Easy experiment with their code and synthetic IMUs.
