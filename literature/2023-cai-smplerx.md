# SMPLer-X: Scaling Up Expressive Human Pose and Shape Estimation

- **Authors / venue / year:** Zhongang Cai, Wanqi Yin, Ailing Zeng, et al., Ziwei Liu — NeurIPS 2023 Datasets & Benchmarks (arXiv 2309.17448)
- **Link:** https://arxiv.org/abs/2309.17448
- **Code:** https://github.com/caizhongang/SMPLer-X — licence in repo, not verified here (OpenMMLab-derived; check). PyTorch 1.12 + MMPose/MMHuman3D stack, Python 3.8, CUDA 11.3; Docker tested on RTX 3090. Variants S/B/L/H: 32M/103M/327M/662M params, 36/33/24/17 fps on V100 bs 1.
- **Read depth:** abstract + repo README
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Whole-body SMPL-X foundation model trained on 4.5 M instances / 32 datasets; useful mainly as a robustness baseline (VR headsets, odd poses) and because its S/B variants are the smallest ViT SMPL-X regressors around — relevant to the end-user CPU question.

## What they do

ViT backbone (ViT-S…H) with a simple head regressing SMPL-X body, hand, face params from a person crop; systematic data/model scaling study. Per-frame, camera-frame; video handled by per-frame inference.

## Key numbers (with table/figure reference)

- AGORA NMVE 107.2 mm; UBody PVE 57.4; EgoBody 63.6; EHF 62.3 mm (abstract). No rotation metrics.

## What we can reuse / what to be careful about

- Reuse: SMPLer-X-S32 (32 M params) is a candidate for quantization to CPU later (§F).
- Careful: old dependency stack (Python 3.8, mmcv) is painful in a uv project; per-frame; no rotation evaluation.

## Open questions this raises

- How does ViT-S vs ViT-H trade off on *rotation* error rather than PVE?
