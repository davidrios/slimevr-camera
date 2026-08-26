# PromptHMR: Promptable Human Mesh Recovery

- **Authors / venue / year:** Yufu Wang, Yu Sun, Priyanka Patel, Kostas Daniilidis, Michael J. Black, Muhammed Kocabas — CVPR 2025 (arXiv 2504.06397)
- **Link:** https://arxiv.org/abs/2504.06397
- **Code:** https://github.com/yufu-wang/PromptHMR — licence not stated clearly in README (unverified; MPI/Meshcapade involvement suggests non-commercial — check LICENSE file). Training code not released. PyTorch 2.4/2.6 CUDA. Deps: Detectron2, SAM2, DROID-SLAM, Metric3D, ViTPose, SPEC. Video world-coordinate mode for static and moving cameras.
- **Read depth:** abstract + skimmed HTML (Tables 1, 4; architecture)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Current (2025) strongest camera-frame and world-frame SMPL-X numbers on EMDB/3DPW/RICH; full-image ViT-L/DINOv2 encoder at 896² so it keeps scene context (relevant for extrinsics later). Optionally takes **camera intrinsics as ray positional encoding**, which the older models cannot.

## What they do

SAM-style promptable transformer: image encoder (DINOv2 ViT-L, 896×896), prompts = boxes/masks/text/interaction; decoder outputs SMPL-X global orientation φ, pose θ, shape β, translation τ in camera space. PromptHMR-Vid adds a 12-block temporal transformer over per-frame tokens; world frame via DROID-SLAM + metric depth as in TRAM.

## Key numbers (with table/figure reference)

- Table 1 (camera-frame, Vid): 3DPW PA-MPJPE 35.5 / MPJPE 56.9 / PVE 67.3; EMDB 40.1 / 68.1 / 79.2; RICH 37.0 / 57.4 / 65.8 mm.
- Table 4 (EMDB world): WA-MPJPE₁₀₀ 71.0 (TRAM 76.4, WHAM 135.6); W-MPJPE₁₀₀ 216.5 (222.4, 354.8); RTE 1.3 % (1.4, 6.0).
- **No angular / orientation error reported.**

## What we can reuse / what to be careful about

- Reuse: best accuracy, intrinsics-aware, static-camera video mode, SMPL-X.
- Careful: licence unverified and probably restrictive; heavy dependency stack (SAM2, DROID-SLAM, Metric3D) — VRAM on a 3090 should be fine for inference but untested; still no rotation metrics.

## Open questions this raises

- LICENSE file contents.
- Does the intrinsics prompt measurably improve global orientation (root yaw) — the paper doesn't isolate it.
