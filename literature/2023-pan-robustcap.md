# Fusing Monocular Images and Sparse IMU Signals for Real-time Human Motion Capture (RobustCap)

- **Authors / venue / year:** Shaohua Pan, Qi Ma, Xinyu Yi, Weifeng Hu, Xiong Wang, Xingkang Zhou, Jijunnan Li, Feng Xu — SIGGRAPH Asia 2023 Conference Papers
- **Link:** https://arxiv.org/abs/2309.00310 ; DOI 10.1145/3610548.3618145 ; project https://shaohua-pan.github.io/robustcap-page/
- **Code:** https://github.com/shaohua-pan/RobustCap — MIT, PyTorch (CUDA build required by README), Python 3.8; pretrained weights + processed data on Google Drive; live demo uses 6 Xsens DOT IMUs, one webcam (intrinsics via a supplied OpenCV calibration script), MediaPipe for 2D keypoints, Unity viewer. Trained/evaluated on a GTX 2080 Ti.
- **Read depth:** full read (arXiv v1 PDF, text-extracted; supplementary — which holds the IMU–camera calibration procedure — not read)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Real-time 6-IMU + single-RGB fusion; the camera acts as an "online calibration" of the IMU branch's drift. Same sensor count as a SlimeVR lower-body-plus set and cheapest possible camera setup, but it learns full pose end-to-end rather than correcting per-tracker yaw; it does **not** expose or evaluate a heading estimate.

## What they do

Inputs: 6 IMUs (pelvis, head, both forearms, both lower legs; acceleration + orientation) and MediaPipe 2D keypoints with confidences from one monocular camera. Output: SMPL pose + root translation in the camera frame, real-time. A one-off **calibration step aligns the IMU global frame to the camera frame** (Sec. 3, details in supplementary, not read); after that the IMU orientations are simply rotated into camera coordinates by that fixed extrinsic.

**Dual coordinate strategy** (Sec. 3.1): RNN-P1 predicts root-relative joint positions from IMUs in the *pelvis* frame (drift-free by construction, since everything is relative to the root IMU); RNN-P2 predicts them in the *camera* frame from IMU + 2D keypoints. Results are blended by mean keypoint confidence (thresholds 0.7/0.8), then RNN-P3 does IK to joint rotations. Translation: TransPose-style foot-contact velocity integration when vision is unreliable, RNN-T3 absolute root position from 2D + IMU when reliable, fused with a complementary filter `α_k = 0.05·σ_mean` (Eq. 7).

**Hidden-state feedback** (Sec. 3.2): when vision is confident, the fused output re-initialises the IMU-only RNN's hidden state; when not, synthesised 2D keypoints from the fused pose keep the vision RNN's state consistent. This is the mechanism by which "the visual information is used as an online calibration to solve the drifting problem" — but note it corrects *learned latent state and translation*, not an explicit per-sensor yaw. The final 1-iteration L-BFGS refinement (Eq. 8) includes `E_ori` pulling joint rotations toward the IMU measurements — i.e. the drifted IMU orientations are still trusted as a soft prior.

Training: AMASS (synthetic IMU + synthetic 2D) and AIST++ (synthetic IMU + detected 2D). Evaluation on TotalCapture (real IMUs), AIST++, 3DPW, 3DPW-OCC (synthetic IMUs).

## Key numbers (with table/figure reference)

Table 1 (MPJPE / PA-MPJPE / PVE mm; TE = root translation error cm):

| Dataset | PIP (IMU-only) | RobustCap |
|---|---|---|
| TotalCapture | 49.1 / 34.6 / 66.0, TE 43.8 | **48.7 / 33.5 / 63.4, TE 23.5** |
| AIST++ | 87.1 / 62.0 / 116.5, TE 45.2 | **33.1 / 24.0 / 43.2, TE 9.9** |
| 3DPW | 78.0 / 49.8 / 100.0 | **55.0 / 38.9 / 71.8** |
| 3DPW-OCC | 97.8 / 66.0 / 126.1 | **77.9 / 53.1 / 97.5** |

- VIP's 39.6 mm (6-IMU) vs. their 33.5 PA-MPJPE on TotalCapture.
- Table 2 ablation, TotalCapture: without dual coordinate 55.2 mm / TE 37.1; without feedback TE 23.8; the final optimisation barely changes pose (48.8→48.7).
- **No angular error reported in this paper** (the later Stereo-Inertial Poser paper reports RobustCap's "SIP error" — global rotation error of hips+shoulders — as 9.34° on AIST++ and 13.4° on TotalCapture, vs. PIP 28.1° / 12.9°). Note on TotalCapture the fusion is *not* better than IMU-only PIP in angle.
- Limitations (Sec. 4.5): out-of-view for long → IMU drift returns; "IMUs are susceptible to error accumulation caused by magnetic disturbances", explicitly left for future work.

## What we can reuse / what to be careful about

- **Reusable engineering:** MIT code, MediaPipe front end, camera-intrinsics script, and the IMU→camera frame calibration routine (in supplementary/code — worth reading `articulate/` for how they align yaw). Their evaluation harness (TotalCapture with real IMUs; synthetic IMU generation from AMASS) is a ready-made testbed.
- **Design lesson:** root-relative processing makes the *pose* drift-free even with yaw-drifting IMUs, because only relative orientations matter; the global heading error is pushed entirely onto the root. For SlimeVR the analogue is: correct root (hip) yaw first, then children relative to it.
- Careful: confidence-gated blending on MediaPipe's mean confidence — they and DiffCap both note it is brittle and needs threshold tuning. Our gate should use stillness + temporal stability, not just detector confidence.
- Careful: on TotalCapture (real IMUs, mostly in-view) the angular gain over IMU-only is nil/negative; the big wins are on AIST++ with *synthetic* IMUs. Real-IMU angular improvement from a monocular camera is **not demonstrated** here.
- Careful: 6 IMUs including forearms; SlimeVR default sets differ (no forearm, has thighs/feet). Pretrained weights are not directly usable.

## Open questions this raises

- What exactly does their IMU–camera calibration do (T-pose facing camera?), and how does it degrade when the pelvis IMU yaw drifts afterwards? The paper never re-estimates that extrinsic.
- Can their RNN-P2 (camera-frame branch) be repurposed to output a per-limb heading with an uncertainty, rather than joint positions?
