# Humans in 4D: Reconstructing and Tracking Humans with Transformers (HMR 2.0 / 4DHumans)

- **Authors / venue / year:** Shubham Goel, Georgios Pavlakos, Jathushan Rajasegaran, Angjoo Kanazawa, Jitendra Malik — ICCV 2023
- **Link:** https://arxiv.org/abs/2305.20091
- **Code:** https://github.com/shubham-goel/4D-Humans — MIT. PyTorch (+Lightning). ViT-H/16 backbone; checkpoints auto-download to `~/.cache/4DHumans`. CUDA assumed; no documented CPU path (a ViT-H forward on CPU is possible in principle but slow). SMPL model download needs MPI registration (SMPL's own non-commercial licence).
- **Read depth:** abstract + skimmed HTML (results tables, architecture)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

The de-facto per-frame SMPL regressor backbone that most 2024–2025 video/world-grounded models (WHAM, TRAM/VIMO, GVHMR, TokenHMR) build on or borrow features from. Outputs per-joint SMPL rotations in **camera frame** — the same quantity as the IMU. No rotation-error metric reported by the authors; EMDB-style MPJAE for this class of model is ~20°+ (see `2023-kaufmann-emdb.md`).

## What they do

ViT-H encoder over a person crop → transformer decoder cross-attending image tokens → SMPL pose θ (23 joint rotations + global orientation), shape β, weak-perspective camera translation. Fixed focal length, identity camera rotation (i.e. the global orientation is relative to the camera, not gravity). 4DHumans adds PHALP tracking across frames for multi-person video; the per-frame regressor itself is **not temporal**.

## Key numbers (with table/figure reference)

- Table 1: 3DPW MPJPE 70.0 mm / PA-MPJPE 44.5 mm (HMR2.0a); Human3.6M 44.8 / 33.6 mm.
- Table 2: 2D re-projection PCK@0.05 on LSP-Extended 0.53 (CLIFF 0.32).
- No MPJAE / orientation error reported. Third-party: TokenHMR Table 1 gives HMR2.0 on EMDB MPJPE 99.3 / PA-MPJPE 62.8 mm.

## What we can reuse / what to be careful about

- Reuse: MIT code, clean SMPL output, strong 2D alignment; everything downstream (WHAM, GVHMR, TRAM) uses its ViT features, so it is the natural "baseline" for a heading experiment.
- Careful: per-frame only (jitter); global orientation is camera-relative with a fixed-focal camera model, so limb heading in a world frame needs our own extrinsics. Rotation accuracy never evaluated by the authors.

## Open questions this raises

- What is the per-joint MPJAE of HMR2.0 on EMDB / 3DPW when we run it ourselves, split into swing vs twist?
- Does the 2D-alignment bias (TokenHMR's argument) hurt 3D rotations specifically?
