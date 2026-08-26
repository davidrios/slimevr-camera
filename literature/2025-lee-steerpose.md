# SteerPose: Simultaneous Extrinsic Camera Calibration and Matching from Articulation

- **Authors / venue / year:** Sang-Eun Lee, Ko Nishino, Shohei Nobuhara — BMVC 2025 (arXiv 2506.01691v2)
- **Link:** https://arxiv.org/abs/2506.01691 ; project page https://kcvl-public.github.io/steerpose/
- **Code:** project page says code is released; repo link/licence not resolvable from the page text (unverified). Transformer model, so CUDA for training; inference likely CPU-tolerable.
- **Read depth:** skimmed (HTML version: method, Tables 2 and 6)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Same group as the RA-L paper, 2D-only variant: learns to "mentally rotate" 2D keypoints of an articulated subject into another view, jointly solving relative rotation and cross-view matching. Works for humans and animals; uses only 2D poses (HRNet/RTMO), intrinsics known.

## What they do

A transformer takes 2D poses from view A and a candidate rotation and predicts the 2D poses as seen from view B (rotation-covariant "steering"). Differentiable Sinkhorn matching associates subjects across views; a geometric-consistency loss checks that the (rotation, matches) pair admits a valid relative translation (epipolar). Rotation is found by searching/optimising over SO(3) using the network as a scorer; translation from the epipolar constraint.

## Key numbers (with table/figure reference)

- Table 2 (two-view, animals): RRA@20 / RTA@20 ≈ 0.99–1.00, AUC@20 0.85–0.94; better than LightGlue, comparable to MASt3R.
- Table 6 (multi-view, Bama pig): rotation error **2.43°**, translation direction error 3.75°, 2D reprojection 3.23 px.
- Human datasets (CMU Panoptic toddler, EgoHumans volleyball) are evaluated but I did not extract their numbers — **unverified**.

## What we can reuse / what to be careful about

- Reuse: idea that 2D-only suffices for relative rotation when the subject is articulated and moving; no 3D lifter needed.
- Careful: learned model; accuracy (~2.4°) is worse than the 3D-lifter-based RA-L method (~0.5–1°) on the numbers I saw. Needs training data for the skeleton format used.

## Open questions this raises

- Whether human-specific numbers are better than the animal ones.
- Whether the released code includes pretrained human weights.
