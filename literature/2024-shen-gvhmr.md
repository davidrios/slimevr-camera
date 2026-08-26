# GVHMR: World-Grounded Human Motion Recovery via Gravity-View Coordinates

- **Authors / venue / year:** Zehong Shen, Huaijin Pi, Yan Xia, Zhi Cen, Sida Peng, Zechen Hu, Hujun Bao, Ruizhen Hu, Xiaowei Zhou — SIGGRAPH Asia 2024 (arXiv 2409.06662)
- **Link:** https://arxiv.org/abs/2409.06662
- **Code:** https://github.com/zju3dv/GVHMR — **custom ZJU academic licence: research/non-profit only, commercial use needs permission (xwzhou@zju.edu.cn)**. PyTorch/Hydra, CUDA (trained on 2×4090). Inputs: YOLOv8 boxes, ViTPose 2D keypoints, HMR2.0 ViT features, DPVO/SimpleVO camera rotation; `-s` flag skips VO for a static camera. Outputs SMPL-X body params (21×3 + 10).
- **Read depth:** abstract + skimmed HTML (results, Fig. 9, runtime)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Most directly relevant framing: predicts pose in a **gravity-aligned, per-frame-defined "Gravity-View" frame** instead of integrating heading autoregressively, and is the only paper here that plots **global orientation error** (Fig. 9). Non-autoregressive ⇒ no heading drift, which is precisely the property we need a camera reference to have.

## What they do

Define a GV coordinate system per frame from world gravity and the camera view direction (yaw about gravity fixed by the camera's viewing ray). A transformer regresses body pose + root orientation in GV coordinates per frame; camera relative rotations (from VO, or gyro, or zero for static camera) transform between frames' GV systems to assemble a world trajectory. Gravity is inferred from image + camera rotations, not measured.

## Key numbers (with table/figure reference)

- RICH (world): WA-MPJPE₁₀₀ 78.8 vs WHAM 109.9; W-MPJPE₁₀₀ 126.3 vs 184.6; RTE 2.4 % vs 4.1 %; jitter 12.8 vs 19.7.
- EMDB (world, DPVO): W-MPJPE₁₀₀ 274.9 vs WHAM 354.8; using GT gyro instead of DPVO changes only 1.6 mm.
- 3DPW (camera): PA-MPJPE 36.2 / MPJPE 55.6 mm, Accel 5.0.
- **Fig. 9:** global orientation error vs time — GVHMR stays bounded, WHAM grows with sequence length. Absolute degrees not extracted here (figure; needs full read).
- Runtime: network 0.28 s for 1430 frames on RTX 4090; ~46 s full pipeline dominated by ViTPose/VO preprocessing.

## What we can reuse / what to be careful about

- Reuse: exactly our regime (static camera ⇒ `-s`), gravity-aligned root orientation, SMPL-X joint rotations, fast. Best candidate for extracting world-heading of limbs from one camera.
- Careful: **licence is non-commercial** — fine for research, a problem for shipping in SlimeVR. Absolute orientation-error numbers not in a table; twist not evaluated. Gravity is estimated, not measured — we could feed IMU gravity instead.

## Open questions this raises

- Read Fig. 9 axis values / supplementary: what is the steady-state global orientation error in degrees on EMDB with a static camera?
- Can the GV frame's yaw ambiguity be removed by our extrinsics (camera yaw known from reset moment)?
