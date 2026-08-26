# Efficient 2D to Full 3D Human Pose Uplifting including Joint Rotations

- **Authors / venue / year:** Katja Ludwig, Yuliia Oksymets, Robin Schön, Daniel Kienzle, Rainer Lienhart — CVPR 2025 Workshops (CVSports); arXiv 2504.09953
- **Link:** https://arxiv.org/abs/2504.09953
- **Code:** not checked
- **Read depth:** abstract + skimmed HTML (Table 4)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

One of the very few 2025 papers that reports **MPJAE in degrees** for a modern HMR-style baseline, and shows that a 2D-keypoint-sequence → SMPL-X-rotation lifter with rotation supervision halves the angular error of a mesh regressor. Supports the "keypoints + lifting + rotation head" route over end-to-end HMR for rotation quality.

## What they do

Temporal uplifting transformer from 2D keypoints to 3D joints *and* SMPL-X joint rotations (22 body joints) in one pass; studies rotation representations (6D, axis-angle …), losses, and weak supervision without GT rotations. 150× faster than IK-based fitting.

## Key numbers (with table/figure reference)

- Table 4 (fit3D, sports, SMPL-X GT): their supervised model MPJAE **9.2°** (22 joints); Multi-HMR baseline **17.6°**; their weakly supervised (no GT rotations) 15.9°.
- Only aggregate MPJAE; no per-joint / twist breakdown. Only fit3D (single dataset, sports, studio).

## What we can reuse / what to be careful about

- Reuse: evidence that ~9–10° mean rotation error is reachable from monocular video with rotation supervision on an in-domain dataset; and that generic HMR ≈ 17–18° even in a studio.
- Careful: fit3D is multi-view studio data; in-the-wild numbers will be worse. Doesn't separate heading from twist.

## Open questions this raises

- What is their per-joint error at elbow/wrist vs hip/knee? (Would need their code.)
