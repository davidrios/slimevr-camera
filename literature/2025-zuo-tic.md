# Transformer IMU Calibrator (TIC): Dynamic On-body IMU Calibration for Inertial Motion Capture

- **Authors / venue / year:** Chengxu Zuo, Jiawei Huang, Xiao Jiang, Yuan Yao, Xiangren Shi, Rui Cao, Xinyu Yi, Feng Xu, Shihui Guo, Yipeng Qin — SIGGRAPH 2025 (ACM TOG 44(4))
- **Link:** https://arxiv.org/abs/2506.10580 ; https://dl.acm.org/doi/10.1145/3730937
- **Code:** https://github.com/ZuoCX1996/TIC (code + dataset, per paper); license not checked.
- **Read depth:** full read of §1–2 (problem statement, ego-yaw frame), §4 (method, trigger), Tables 3/6 and §6 Limitations. Not run.
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

The first sparse-IMU paper that treats the IMU world-frame drift R_G'G(t) and the mounting offset R_BS(t) as **time-varying** and estimates them online from motion alone. It also states plainly what IMU-only methods *cannot* do: correct global yaw drift. That is exactly the gap our camera fills.

## What they do

- Model: calibrated reading R_cali(t) = R_G'G(t)ᵀ · R_IMU(t) · R_BSᵀ. Static calibration (T-pose at t=0) assumes both matrices constant; TIC relaxes this to "constant over a short window" + "the window contains diverse rotations".
- A Transformer takes a short history of IMU orientations/accelerations (30 Hz, 256-frame sequences in the datasets) and regresses R_G'G and R_BS per sensor. A **rotation-diversity trigger** (Euler space binned at 15°; only run when the window has enough rotational diversity) prevents garbage updates during low-activity periods.
- **Key framing — ego-yaw coordinate system:** they define the global frame's yaw to follow the *root* sensor, "to eliminate the non-solvable drift component". So all drift estimates are relative to the pelvis IMU's heading; the pelvis's own yaw drift is by construction unobservable to them.
- Fig. 1/2 motivate with an Xsens/Noitom-style session: T-pose at 0 min, "IMU drifting occurs", visibly wrong pose at 12 min — the clearest statement in this literature that drift on the order of ten minutes breaks static-calibrated sparse mocap. Low-cost MEMS IMUs cited as suffering "axes misalignment, bias and cross-axis sensitivities" leading to systematic error.
- Test data DS_TIC: real recordings (Noitom Axis Lab), 1.04 M samples, with ground-truth R_G'G and R_BS from a skeleton reference.

## Key numbers (with table/figure reference)

- Table 3 (pose error with / without dynamic calibration on DS_TIC, long-term usage): PNP angular 15.5° / **30.6°**, SIP 14.2° / 25.1°, pos 7.2 / 12.7 cm; PIP 16.2° / 32.4°; TransPose 17.9° / 36.9°; DIP 19.3° / 37.2°. I.e. without re-calibration, drift roughly **doubles** angular error of every 6-IMU method over their long sessions.
- Table 6: translation error in the ego-yaw frame improves with TIC (10 s window 36.4 vs 45.0 cm), but in the fixed SMPL frame it *worsens* (49.5 vs 41.7 cm) because root yaw drift is not corrected.
- §6 Limitations, verbatim: "we only consider the coordinate drift in the ego-yaw frame and do not support the correction of global yaw drift (Fig. 9)"; also fails in "low-activity scenarios, such as office work, watching TV" where rotation diversity is insufficient.

## What we can reuse / what to be careful about

- Their decomposition (global yaw drift = unobservable from IMUs; per-sensor differential drift = observable from motion consistency) maps directly onto our design: the camera should supply the **global** heading and could optionally supply per-limb heading for the low-activity case where TIC fails (seated VR users!).
- Table 3 is the best published evidence for "drift magnitude matters" in this family, but the actual degrees of R_G'G drift over time are in figures (Fig. 7/9) not extracted here — read the PDF figures before quoting a °/min.
- Trigger idea (only trust an estimate when the window has rotational diversity) is a good pattern for gating camera-based corrections too.

## Open questions this raises

- What is the drift rate of their Noitom sensors in °/min (mag on or off)? Not in the text; check Fig. 7/9 and dataset files.
- Could TIC's per-sensor estimate be run on SlimeVR quaternion streams (with mag off, R_G'G differs per sensor from the start)?
