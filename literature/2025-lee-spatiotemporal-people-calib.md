# Spatiotemporal Multi-Camera Calibration using Freely Moving People

- **Authors / venue / year:** Sang-Eun Lee, Ko Nishino, Shohei Nobuhara (Kyoto U.) — IEEE RA-L 2025
- **Link:** https://arxiv.org/abs/2502.12546
- **Code:** none found (arXiv page, project search, GitHub search — nothing). Reported runtime 38 s (with sync) on an Apple M1 Pro, i.e. CPU-feasible.
- **Read depth:** full read (PDF text, method + all tables)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Closest match to §D(a)+(d): extrinsics **and** per-camera time offset from off-the-shelf monocular 3D pose (AlphaPose 2D → MotionBERT 3D), no checkerboard, no sync hardware. Intrinsics assumed known. Multi-person scenes, but nothing in the formulation needs >1 person.

## What they do

Each person's 3D pose from a monocular lifter is turned into a set of unit direction vectors (bone directions on the unit sphere), per view. Pairwise registration: fit von Mises–Fisher distributions to the target view's directions over a window of T = 5–15 frames, then alternate (EM-style) between soft person association, relative rotation R, and integer time offset δ (brute-force search over ±10 frames, since offset is 1-D). Translation follows from coplanarity (epipolar) constraints once R is known. Pairwise results are chained into a multi-view graph with pose-graph optimisation, then spatiotemporal bundle adjustment (STBA) with iterative outlier rejection (ISTBA). Translation is recovered only up to scale (they normalise by the distance between the first two cameras).

## Key numbers (with table/figure reference)

- Table II (4 cameras, real data, unsynchronised, 300–1000-frame clips): ISTBA rotation error 0.004–0.078 rad (**0.2°–4.5°**, most scenes 0.4°–1°), normalised translation error 0.006–0.109, reprojection 1.1–5.7 px, time-offset MAE 0–1 frame.
- Table III (pairwise, synthetic noise σ=3 px, with RANSAC): mean rotation 0.011–0.022 rad (**0.6°–1.3°**), offset error 0–1 frame.
- Table IV (vs. 8-point / PnP / incremental SfM with 10 checkerboards, σ=0.5 px): checkerboard methods get lower reprojection error but their method gets rotation 0.006 rad and much lower translation error (0.004 vs 0.03–0.19).
- Fig. 5: rotation error grows roughly linearly with 2D noise 1–5 px; beats ARCS and ReID-Calib at all noise levels.

## What we can reuse / what to be careful about

- Reuse: the encoding trick (bone directions on the unit sphere) is exactly "limb heading" and could share code with our heading-comparison step. Their offset search (integer frames, ±10) is the simplest workable sync for RTSP cameras; combine with a coarser first-pass (CasCalib-style 1-D search) if offsets are larger.
- Careful: translation is up to scale — we would fix scale with bone lengths (SlimeVR knows them) or the HMD. Intrinsics must be known (a single checkerboard shot per camera, once). Errors are per-*4-camera rig* averages; 2-camera pairwise numbers (Table III) are the relevant ones for us, and those were on synthetic noise. Depends on monocular 3D lifter quality; VR headset/controllers may hurt it.

## Open questions this raises

- With a single person and a lot of near-still frames (our regime) does the vMF fit degenerate? They rely on motion diversity.
- No code: reimplementing is ~1–2 weeks; CasCalib (has code) may be a faster start.
