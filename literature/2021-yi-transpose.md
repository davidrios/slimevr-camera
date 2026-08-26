# TransPose: Real-time 3D Human Translation and Pose Estimation with Six Inertial Sensors

- **Authors / venue / year:** Xinyu Yi, Yuxiao Zhou, Feng Xu — SIGGRAPH 2021 (ACM TOG 40(4))
- **Link:** https://arxiv.org/abs/2105.04605 ; project https://xinyu-yi.github.io/TransPose/
- **Code:** https://github.com/Xinyu-Yi/TransPose — GPL-3.0. PyTorch (1.7 / CUDA 10.1 in paper); inference is small RNNs, CPU-feasible. Live demo uses Noitom Legacy IMUs.
- **Read depth:** full read of §5 (evaluation, limitations 5.5.1), appendix A (sensor preprocessing/calibration), Tables 2–3. Not run.
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Adds global translation (foot-contact + RNN) to the DIP setup and is the first of the Tsinghua line (TransPose→PIP→PNP→GlobalPose) whose calibration protocol and metrics everyone now uses. Drift is discussed only for translation; heading is delegated to the magnetometer.

## What they do

- Multi-stage RNN: leaf joint positions → full joint positions → joint rotations (6D); translation from supporting-foot velocity fused with an RNN velocity estimate.
- **Calibration (Appendix A.1):** two steps. (1) Global frame: one IMU is placed with its axes aligned with the SMPL frame to read off R_IM (inertial→SMPL) — this relies on all sensors sharing the same inertial frame, i.e. on the magnetometer. (2) Subject holds **T-pose for a few seconds**; per-sensor bone offset computed from known T-pose bone orientations. Then normalization: leaf inertia expressed in the root (pelvis) sensor frame.
- **Drift handling:** none for orientation. §5.5.1 limitation: "a magnetometer is used to measure directions ... it cannot work in an environment with spatially or temporally varying magnetic fields." So their sensors are 9-axis with mag-aided heading; yaw drift is assumed solved by hardware.
- Translation drift is evaluated (root error after 1 s / 5 s of accumulation) but that is position drift, not yaw.
- §5 note: DIP-IMU has raw and calibrated variants; they evaluate on raw because calibrated strips the root inertial signal. This makes their numbers not directly comparable with the DIP paper.

## Key numbers (with table/figure reference)

Table 2 (offline) / Table 3 (online), mean (±std):
- TotalCapture offline: SIP err 14.95°, angular err 12.26°, pos err 5.57 cm, jitter 1.57 (×10² m/s³); DIP baseline 18.79° / 17.77° / 9.61 cm.
- DIP-IMU offline: SIP 13.97°, ang 7.62°, pos 4.90 cm. Online: SIP 16.68°, ang 8.85°, pos 5.95 cm.
- "SIP error" = global rotation error of hips + shoulders (the proximal bones that matter most for us); "angular error" = all joints.

## What we can reuse / what to be careful about

- The metric set (SIP err / ang err / pos err / mesh err / jitter) is the de-facto standard; use it when we evaluate IMU-only vs camera-corrected skeletons.
- Root-relative normalization means the *network* never sees absolute heading; a global yaw error common to all sensors is invisible to it and only shows up as a wrong facing direction. Per-sensor differential heading error is what breaks these models.
- GPL-3.0: fine for research, incompatible with shipping inside SlimeVR server (MIT/Apache) without isolation.

## Open questions this raises

- No experiment on how the model degrades with per-sensor heading error; PNP (2024) and TIC (2025) later quantify this.
