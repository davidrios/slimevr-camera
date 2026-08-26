# Human Pose as Calibration Pattern: 3D Human Pose Estimation with Multiple Unsynchronized and Uncalibrated Cameras

- **Authors / venue / year:** Kosuke Takahashi, Dan Mikami, Mariko Isogawa, Hideaki Kimata (NTT) — CVPR Workshops 2018
- **Link:** https://openaccess.thecvf.com/content_cvpr_2018_workshops/papers/w34/Takahashi_Human_Pose_As_CVPR_2018_paper.pdf
- **Code:** none.
- **Read depth:** skimmed (PDF: abstract, method outline, experiment setup, result text)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Early, simple formulation of the whole problem: 2D joints from a detector are the only correspondences; solves time shift (sub-frame, continuous), extrinsics and 3D pose jointly for wide-baseline cameras. Establishes that joint detections are usable correspondences where feature matching fails (wide baselines — our case with 2 cameras in room corners).

## What they do

2D joints (OpenPose-type) per view, cubic-spline interpolated + median filtered to allow continuous time shift. Initial extrinsics from the fundamental matrix of one camera pair + PnP for the rest (SfM-style). Then joint optimisation over time shift, extrinsics, 3D joints with (i) a **relaxed** reprojection error (tolerant to few-px joint noise) and (ii) a human-model term (bone-length constancy) as prior. Intrinsics assumed known (synthetic: f=16000 px at 1080p — a long lens; real: 200 mm lenses, 120 fps).

## Key numbers (with table/figure reference)

- Synthetic (3 cams, 1080p60, noise σ up to 5 px + 10 % detection failures): time-shift error **6–12 ms**; extrinsics stay robust with noise whereas plain bundle adjustment degrades (Fig. 6 — only qualitative trend extracted; no degree numbers in the text I read).
- Real: two CASIO EX100 at 640×480, 120 fps, wide baseline; qualitative only (Fig. 8).

## What we can reuse / what to be careful about

- Reuse: bone-length constancy as a regulariser — we have *known* bone lengths, which is strictly stronger (gives metric scale).
- Careful: sports/long-lens setup, not a room with wide-angle webcams; numbers are synthetic; no absolute accuracy tables.

## Open questions this raises

- Their sub-frame sync via spline interpolation is worth copying for RTSP cameras with non-integer frame offsets.
