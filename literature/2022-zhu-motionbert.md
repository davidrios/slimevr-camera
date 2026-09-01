# MotionBERT: A Unified Perspective on Learning Human Motion Representations

- **Authors / venue / year:** Zhu, Ma, Liu, Liu, Wu, Wang — ICCV 2023 (arXiv 2210.06551, 2022)
- **Link:** https://arxiv.org/abs/2210.06551
- **Code:** https://github.com/Walter0807/MotionBERT — Apache-2.0, plain PyTorch (CPU or CUDA, no mmcv); checkpoints mirrored on Hugging Face (`walterzhu/MotionBERT`). Cloned into `tools/motionbert/MotionBERT`.
- **Read depth:** code read (wild-inference path: `infer_wild.py`, `dataset_wild.py`, configs) + README model zoo; paper itself only abstract
- **Date read:** 2026-09-01

## Relevance to us (1–3 lines)

The monocular 2D→3D lifter for the single-camera main line (D36, exp 09): takes our cached rtmlib 2D keypoints (converted to H36M-17) and produces per-frame 3D joints from one view, dropping into the pipeline where triangulation used to be.

## What they do

DSTFormer: dual-stream spatio-temporal transformer over 2D keypoint sequences (≤243 frames), pretrained by reconstructing 3D from masked/noisy 2D on large mocap (AMASS + H36M etc.), fine-tuned per task (3D pose, action, mesh).

## Key numbers (with table/figure reference)

- README model zoo: 3D pose H36M-SH scratch 39.2 mm MPJPE, fine-tuned 37.2 mm (detected SH 2D input). MMPose's re-run reports 34.5/26.9 mm — different 2D input, not comparable; treat 37 mm as the honest detected-2D number.
- No rotation/heading metric anywhere (as usual, cf. 2023-kaufmann-emdb); heading accuracy for our bones is exactly what exp 09 measures.

## What we can reuse / what to be careful about

- **Reuse:** `lib` model + `load_backbone`; checkpoints `FT_MB_lite_MB_ft_h36m_global_lite` (wild-inference default, `rootrel: False`, `flip: True` TTA) and `FT_MB_release_MB_ft_h36m` (full, `rootrel: True`).
- **Input convention** (`dataset_wild.py` `--pixel` path): H36M-17 order `[x,y,conf]`, coordinates centred on the image and divided by `min(w,h)/2` (aspect-preserving). H36M-17: 0 pelvis, 1–3 R leg, 4–6 L leg, 7 spine, 8 thorax, 9 nose, 10 head, 11–13 L arm, 14–16 R arm; virtual joints = midpoints.
- **Output frame:** pixel-aligned camera frame (x right, y image-down, z relative depth, same scale) — i.e. scaled-orthographic; perspective distortion away from the image centre becomes heading error (absorbed by our per-pose bias to the extent it's pose-repeatable). Rotate to world with `Camera.R.T`.
- No toes in H36M-17 → no foot heading from this lifter.
- **Licence:** code Apache-2.0, but weights are trained on H36M/AMASS → evaluation-only under our D34 policy anyway.

## Open questions this raises

- Is the within-pose repeatability (~2° with 2-cam triangulation, exp 05) preserved under monocular lifting? (= exp 09's question)
- Does the full `MB_ft_h36m` release beat `global_lite` on heading? (both downloaded, cheap to compare)
