# Stereo-Inertial Poser: Towards Metric-Accurate Shape-Aware Motion Capture Using Sparse IMUs and a Single Stereo Camera

- **Authors / venue / year:** Tutian Tang, Xingyu Ji, Yutong Li, MingHao Liu, Wenqiang Xu, Cewu Lu (SJTU) — arXiv 2603.02130, 2026-03-02; arXiv abstract page says ICRA 2026 (not independently verified against the ICRA programme)
- **Link:** https://arxiv.org/abs/2603.02130 ; project https://sites.google.com/view/stereo-inertial-poser
- **Code:** network https://github.com/jxyjxyw/Stereo-Inertial-Poser (PyTorch 2.6, CUDA 11.8, Mamba SSM; **licence not stated; checkpoints and data links are TODO; 1 commit** as of 2026-08-26), IMU firmware https://github.com/robotflow-initiative/rfmarkit-esp-node, camera server https://github.com/robotflow-initiative/mediapipe-apiserver. Hardware: ZED 2 stereo (720p, 60 Hz) + in-house ESP32 IMUs.
- **Read depth:** full read (arXiv v1 PDF, text-extracted; supplementary/video not seen)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

The "two cameras" branch of our question: replaces RobustCap's monocular camera with a calibrated stereo pair, triangulates MediaPipe keypoints to metric 3D, and fuses with 6 IMUs. Reports **SIP error (global rotation error of hips + shoulders, degrees)** — the closest thing in this set to a heading accuracy number — for itself and for RobustCap/PIP/PNP.

## What they do

Six IMUs (pelvis, head, forearms, lower legs) in the PIP/RobustCap layout; one fixed stereo camera with known baseline and intrinsics. Per frame: MediaPipe on left and right image → 2D keypoints (17 COCO) + confidences → depth from disparity (Eq. 2) → metric 3D keypoints in the left-camera frame; also MediaPipe's canonical root-relative 3D. Body shape β fitted once from a T-pose with a stereo point cloud (Eq. 4). Three SSM (Mamba) encoders — TransNet (root translation from 9 head/trunk keypoints), IENet (joint positions from IMUs in the pelvis frame), KENet (joint positions from keypoints) — then a shape-aware FusionNet and RefineNet output SMPL rotations, translation, and foot-contact probabilities. Losses include foot-skating (Eq. 13) and jerk (Eq. 14). >200 fps offline; live at the camera's 60 fps. Trained on AMASS + AIST++ with synthetic IMUs/keypoints (5 cm noise on 3D keypoints).

Drift handling: same as RobustCap — IMU-side pose is root-relative, global translation from vision; "compensating for inertial drift via state-space fusion". No explicit per-sensor yaw variable. IMU-to-camera extrinsic calibration is not described in the main paper (presumably supplementary).

## Key numbers (with table/figure reference)

Table I (JPE mm / PVE mm / **SIP °** / TE cm / Jerk / FS):

| Method | AIST++ | TotalCapture |
|---|---|---|
| PIP (IMU-only) | 87.0 / 116.5 / **28.1** / 45.2 | 49.1 / 66.0 / **12.9** / 43.8 |
| PNP (IMU-only) | – | 47.4 / – / **10.8** / – |
| RobustCap (mono) | 33.1 / 43.2 / **9.34** / 9.91 | 48.7 / 63.4 / **13.4** / 23.5 |
| Ours (ideal 3D kp) | 29.8 / 39.0 / **8.91** / 1.13 | 46.5 / 54.3 / **10.6** / 5.42 |
| Ours (5 cm kp noise) | 30.6 / 39.8 / **9.12** / 4.83 | 47.6 / 55.8 / **11.0** / 8.93 |
| Ours (synthetic stereo from real cams) | 31.7 / 43.1 / **9.89** / 7.76 | 49.0 / 57.1 / **10.9** / 9.41 |

- The stereo advantage is almost entirely in **translation** (TE 23.5→5–9 cm on TotalCapture); local pose and hip/shoulder rotation improve only 1–3°.
- On TotalCapture (real IMUs) the IMU-only PNP (10.8°) is as good as or better than every fusion method in SIP error; the paper admits fusion "underperform[s] recent inertial-only baselines" there.
- Qualitative (Sec. IV-B): 10 laps on a 2 m-radius circle — PIP/PNP drift, RobustCap is drift-free but scale-distorted, stereo is metric and drift-free. No numbers for this.

## What we can reuse / what to be careful about

- Confirms the cheapest workable stereo recipe: **2D detector per view + disparity**, no learned stereo net. Their "synthetic stereo from adjacent dataset cameras" trick lets us evaluate a 2-webcam setup on TotalCapture without owning a ZED.
- SIP-error numbers give a realistic bar: ~9–13° hip/shoulder global rotation error with 6 IMUs + camera on real data. That is *full* rotation (incl. pitch/roll/twist); the yaw component is not separated.
- Careful: needs a calibrated baseline; the paper does not solve stereo extrinsics from the person.
- Careful: code is skeletal today (no weights, no licence). Treat as reference, not as a dependency.
- Careful: "drift-free" in this paper family means *translation*; nobody in §A measures heading drift correction directly.

## Open questions this raises

- With two uncalibrated webcams, can the person themselves provide the baseline (§D of the agenda)? This paper assumes a factory-calibrated rig.
- Why do fusion methods lose to PNP in rotation on TotalCapture — occlusion/out-of-view frames, or the IMU orientations there being too good (Xsens with mag) for the camera to add anything? Relevant to whether a camera helps at all when the IMU is *not* drifting.
