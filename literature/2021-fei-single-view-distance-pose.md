# Single View Physical Distance Estimation using Human Pose

- **Authors / venue / year:** Xiaohan Fei, Henry Wang, Xiangyu Zeng, Lin Lee Cheong, Meng Wang, Joseph Tighe (Amazon) — arXiv 2021 (2106.10335)
- **Link:** https://arxiv.org/abs/2106.10335
- **Code:** not released as far as I could find (paper mentions Ceres-Solver implementation; MEVADA annotations released).
- **Read depth:** skimmed (PDF text: abstract, formulation, Tables 1–3)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Single-camera §D(b): estimates focal length **and the ground plane (normal + distance)** from 2D ankle/shoulder keypoints of upright people of assumed constant height, with a direct linear formulation + RANSAC. Gives a sense of achievable floor-normal accuracy from keypoints alone.

## What they do

Assumes a dominant ground plane and people standing upright with constant height h (ankle center + h·N = shoulder/head point). Writes three linear constraints per person pair between the back-projected ankle and top points, eliminating depth, to solve fx, fy, ground-plane normal N and distance ρ directly (no vanishing-line intermediate). RANSAC with 2–3 people per hypothesis, Ceres refinement. Real-data pipeline: person detection → 2D pose → calibration → distances.

## Key numbers (with table/figure reference)

- Table 1 (simulation, 1080p, 90° FOV, 5000 trials): at 0.5 px keypoint noise: fx error 3.1 %, ground-normal error **0.45°**, plane-distance error 1.2 %; at 2 px noise: fx 11.9 %, normal **1.84°**, ρ 4.9 %.
- Table 2 (height std 0.05–0.25 m across people): normal error 0.8°–2.4°, fx 4.7–13.9 %.
- Table 3 (number of people 5→100): normal error 3.9°→0.8°, fx 21 %→5 %. Few observations ⇒ focal is poorly determined; the normal is more robust.
- Real data (MEVADA, Oxford Town Centre): distance-estimation benchmark, Table 6 — not extracted.

## What we can reuse / what to be careful about

- Reuse: the linear ankle/shoulder formulation; for us "many people" becomes "one person at many positions over time", and h is known exactly, so Table 2's height-variance penalty vanishes.
- Careful: focal from people alone is 5–20 % off unless many observations — do intrinsics once with a checkerboard, or take EXIF/known camera model. The normal (~1–2° at realistic noise) is comparable to what the IMUs give from gravity, so the camera's vertical is *not* better than the IMU's; the camera's unique contribution remains yaw.

## Open questions this raises

- Does a 1–2° floor-normal error matter for limb heading? (Heading is about the vertical; a 2° tilt of the vertical shifts heading of near-vertical bones a lot, of horizontal bones little.)
