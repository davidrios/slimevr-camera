# TokenHMR: Advancing Human Mesh Recovery with a Tokenized Pose Representation

- **Authors / venue / year:** Sai Kumar Dwivedi, Yu Sun, Priyanka Patel, Yao Feng, Michael J. Black — CVPR 2024 (arXiv 2404.16752)
- **Link:** https://arxiv.org/abs/2404.16752
- **Code:** https://github.com/saidwivedi/TokenHMR — **non-commercial research licence (MPI)**. PyTorch (CUDA 11.8 / torch 2.1), Python ≤ 3.10, built on 4D-Humans; ViT-H backbone.
- **Read depth:** abstract + skimmed HTML (Table 1)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Per-frame HMR2.0 successor whose central claim is directly about *rotation* quality: better 2D alignment under a wrong camera model degrades 3D pose (rotations), and constraining output to a learned discrete pose codebook fixes part of it. Still reports only position metrics.

## What they do

(1) Threshold-Adaptive Loss Scaling: down-weight small 2D re-projection residuals so the wrong fixed-focal camera does not bend the 3D pose. (2) Pose as classification over VQ tokens of a body-pose codebook learned from AMASS; decoder maps tokens → SMPL rotations. Camera-frame, per-frame.

## Key numbers (with table/figure reference)

- Table 1 (same training data as HMR2.0): EMDB MPJPE 91.7 vs 99.3, PA-MPJPE 55.6 vs 62.8; 3DPW 71.0 / 44.3 vs 77.4 / 47.4 mm.
- Uses SO(3) geodesic distance internally to set TALS thresholds, but no MPJAE in results.

## What we can reuse / what to be careful about

- Reuse: evidence that fixed-focal camera models corrupt rotations ⇒ we should supply real intrinsics (webcam calibration is cheap). Codebook prior may suppress implausible twists.
- Careful: non-commercial licence; per-frame; no rotation numbers.

## Open questions this raises

- Does the tokenized prior reduce twist error at elbow/wrist, or just average it toward the codebook mean?
