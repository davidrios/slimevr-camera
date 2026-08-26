# Fusing Wearable IMUs with Multi-View Images for Human Pose Estimation: A Geometric Approach

- **Authors / venue / year:** Zhe Zhang, Chunyu Wang, Wenhu Qin, Wenjun Zeng — CVPR 2020, pp. 2200–2209
- **Link:** https://openaccess.thecvf.com/content_CVPR_2020/html/Zhang_Fusing_Wearable_IMUs_With_Multi-View_Images_for_Human_Pose_Estimation_CVPR_2020_paper.html (no arXiv version found)
- **Code:** https://github.com/CHUNYUWANG/imu-human-pose-pytorch — MIT, PyTorch, ResNet-50 backbone, GPU (`--gpus 0`); TotalCapture not redistributed; pretrained `res50_256_final.pth.tar` provided.
- **Read depth:** full read (main paper PDF, text-extracted)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Uses IMU *limb orientations* as a geometric prior to improve multi-view 2D/3D keypoint estimation. The information flows **from IMU to camera**, i.e. the opposite direction from what we want; there is no drift modelling. Useful mainly as a reference for what multi-view + IMU accuracy looks like and for the limb-direction formulation.

## What they do

Sensors: 8 of TotalCapture's 13 IMUs (limb segments) and **4 of the 8 static, calibrated cameras**. Per-frame (no temporal model in the main variant; "Temporal" flag in Table 3 is a post-filter). Two stages:

1. **ORN** (Orientation Regularized Network): for each limb (J1,J2) with an IMU, back-project a 2D candidate for J1 along its ray, place J2 at `limb_length × IMU_direction`, project into all views and use the J2 heatmap response there to reinforce J1's heatmap (Eq. 3, Fig. 3). Needs known camera intrinsics/extrinsics and IMU orientation already expressed in the camera/world frame.
2. **ORPSM** (Orientation Regularized Pictorial Structure Model): discrete 3D pictorial structure with a limb-length term and a soft "limb orientation" term `ψ_IMU = (J_m − J_n)/‖…‖ · o_mn` (Eq. 6), the dot product of estimated bone direction with the IMU-measured direction. Dynamic-programming inference, ~0.15 s/frame on a Titan Xp.

IMU-to-world calibration and drift: **not discussed**; the paper assumes the IMU orientations from TotalCapture are already in the world frame. Future work says they will "learn a reliability indicator … for each sensor" because IMU readings are noisy.

## Key numbers (with table/figure reference)

- Table 2 (TotalCapture, 4 cams, MPJPE mm, all joints): SN+PSM 28.3 → ORN+ORPSM **24.6**. Largest gains on wrists/elbows (56.8→43.4, 54.8→40.7).
- Table 3: with temporal filtering 20.6 mm; Procrustes-aligned; VIP's 26.0 mm listed for comparison (VIP uses 1 camera, aligned).
- Table 1: 2D PCKh@1/12 mean(all) 65.8 → 67.1.
- Table 4: H36M with *virtual* (GT) IMUs, 27.9 → 21.7 mm — an upper bound of what perfect limb orientations buy the camera side.
- **No joint-angle / orientation error reported.**

## What we can reuse / what to be careful about

- The **limb-direction dot-product cost** (Eq. 6) is a clean, model-free way to compare a camera bone direction with an IMU bone direction; our `Δψ_i` is the yaw component of exactly this residual.
- The H36M virtual-IMU experiment quantifies how much a *correct* IMU direction helps the camera; inverted, it hints how sensitive their pipeline is to drifted directions (not measured).
- Careful: requires ≥4 calibrated cameras; drops to 1–2 cameras are not evaluated. Not applicable to our setup directly.
- Careful: no drift handling at all; if we ever feed IMU directions into a camera pipeline the yaw error propagates.

## Open questions this raises

- Would ORPSM's orientation term make yaw drift *worse* by pulling 3D joints toward the drifted IMU direction? (Untested in the paper.)
- Is there a 2-camera variant of the pictorial-structure lifting worth reusing for stereo webcams? Their code supports arbitrary view subsets in principle.
