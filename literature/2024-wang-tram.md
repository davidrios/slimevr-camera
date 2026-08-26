# TRAM: Global Trajectory and Motion of 3D Humans from in-the-wild Videos

- **Authors / venue / year:** Yufu Wang, Ziyun Wang, Lingjie Liu, Kostas Daniilidis — ECCV 2024 (arXiv 2403.17346)
- **Link:** https://arxiv.org/abs/2403.17346
- **Code:** https://github.com/yufu-wang/tram — MIT. PyTorch, Python 3.10, CUDA. Pipeline: masked DROID-SLAM + ZoeDepth (metric scale) → VIMO (frozen ViT-H from HMR2.0 + two temporal transformers) → compose. Has a "camera is static" flag. Needs SMPL registration.
- **Read depth:** abstract + skimmed HTML (Tables 3–4)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Two-stage alternative to WHAM: camera motion from SLAM with metric scale, human motion from a video transformer (VIMO) in camera frame, composed into world frame. Much lower world trajectory error than WHAM. VIMO alone is a temporal SMPL regressor we could use in camera frame with a static camera.

## What they do

Robustified DROID-SLAM (humans masked) gives camera rotation + up-to-scale translation; ZoeDepth on the background fixes metric scale. VIMO: HMR2.0 ViT-H (frozen) + temporal transformer encoders over frame tokens, outputs SMPL θ, root orientation r, β per frame, in camera coordinates. World motion = camera pose ∘ camera-frame human.

## Key numbers (with table/figure reference)

- Table 3 (EMDB 2): TRAM WA-MPJPE₁₀₀ 76.4 / W-MPJPE₁₀₀ 222.4 mm, RTE 1.4 %, ERVE 10.3 (WHAM 133.3 / 343.9 / 4.6 / 14.7).
- Table 4 (camera-frame): 3DPW PA-MPJPE 35.6 / MPJPE 59.3; EMDB 45.7 / 74.4 mm.
- No rotation/angular error reported. SLAM needs a known focal length (authors list this as a limitation).

## What we can reuse / what to be careful about

- Reuse: MIT; VIMO is the cleanest "HMR2.0 + temporal" camera-frame model; static-camera path exists so SLAM can be skipped.
- Careful: heavy (ViT-H + DROID-SLAM + ZoeDepth); intrinsics matter for the SLAM stage; still no evidence about rotation accuracy beyond MPJPE.

## Open questions this raises

- Is VIMO's per-joint rotation better than HMR2.0's, or does the temporal head only smooth?
