# 04 — Real 2D detector heading bias on MoVi (in progress)

**Started:** 2026-08-26 · **Status:** data downloading, loader written

## Hypothesis

Averaging inside a still window removes *noise* (exp 01) but not the
*systematic* keypoint offsets of a real 2D detector (hip placed low, ankle on
the shoe, shoulder on the deltoid…). Those shift lateral-axis headings when
the person is seen obliquely. Question: how large is that bias per bone,
per viewing angle, for an off-the-shelf detector on 2 real low-res cameras?
Target D19: ≤5° long bones, ≤8–10° feet/forearms.

## Data: MoVi (`literature/datasets-multiview-gt.md`)

- 2 hardware-synced calibrated FLIR cameras (PG1, PG2), 800×600 @ 30 fps —
  a two-camera pair like ours, at roughly 4–5 m.
- Qualisys marker GT → Visual3D **segment frames** (4×4 affine, 120 Hz):
  pelvis, thorax, head, thighs, shanks, feet, upper arms, forearms, hands.
  True per-bone orientation, so the same-axis heading comparison
  (`slimevr_camera.heading`) applies directly — no keypoint-definition
  ambiguity on the GT side.
- 21 motions per subject incl. `dancing_rm`, `sitting_down`,
  `cross_legged_sitting`, `stretching`, `walking` — several are natural
  "still-ish" or constrained-motion regimes.
- Pilot: subjects 1–5, round F (≈3 GB video + 1.8 GB GT). Licence:
  non-commercial research; data stays local (`data/movi/`, gitignored).
- Note: the 2020 README says access requires an institutional Dataverse
  account; in 2026 the API serves the files directly (files unrestricted).
  Terms still apply.

## Plan

1. Verify calibration convention by reprojecting markers onto a frame
   (MATLAB row-vector convention, transposed K, radial distortion k1,k2).
2. Run RTMPose (rtmlib, body/wholebody, CPU or GPU) on both views for the
   pilot subjects; cache 2D keypoints + scores.
3. Undistort, triangulate (DLT) → 3D joints; derive per-bone axis
   (`heading.estimate_all`) and compare with the GT segment frame's same
   axis: error per frame, per bone.
4. Split into still windows (from GT angular speed) vs. moving; report
   **mean (bias) and std (noise)** of heading error per bone, and bias vs.
   body yaw relative to the camera baseline.
5. Repeat for a second detector (wholebody for toes; ViTPose if easy) and
   for single-view + bone-length lifting as the 1-camera baseline.

## Open items

- GPU: this machine has only the RX 9060 XT (Q18). rtmlib on CPU is fine
  for 800×600 pilot volume.
- Kinematic-tree "waist" has no GT segment in MoVi (pelvis→thorax only);
  evaluate hip + chest and note waist as interpolated.
