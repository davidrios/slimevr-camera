# Transformer Inertial Poser (TIP): Real-time Human Motion Reconstruction from Sparse IMUs with Simultaneous Terrain Generation

- **Authors / venue / year:** Yifeng Jiang, Yuting Ye, Deepak Gopinath, Jungdam Won, Alexander W. Winkler, C. Karen Liu — SIGGRAPH Asia 2022
- **Link:** https://arxiv.org/abs/2203.15720
- **Code:** https://github.com/jyf588/transformer-inertial-poser ; paper page shows CC BY-NC-SA 4.0 badge (repo license not separately verified). Live demo with 6 Xsens IMUs.
- **Read depth:** abstract, §3.2 (drift stabilizer), Appendix D (sensor calibration) and Tables 1/3. Not run.
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Transformer (not RNN) 6-IMU poser whose "drift" contribution is about *root position* drift via predicted stationary body points (SBPs), not orientation drift. Useful as a second data point on calibration protocol and on how little the field measures long-session degradation (they test 50 s windows).

## What they do

- Transformer decoder over a window of IMU history predicts pose + SBPs (which body points are stationary). A "drift stabilizer" uses SBPs to correct root translation and joint positions; SBP heights build a terrain height map that in turn corrects vertical drift.
- **Calibration (Appendix D):** two-step, T-pose held ~3 s; per-sensor frames G_n (sensor identity frame), a user-specified global frame G_p, sensor-to-bone offset R_S0^B0 from the T-pose reading. "Sensors need to be calibrated with a T pose before each use." No re-calibration during use.
- **Drift:** §3.2 opens "Combating drifts is one of the biggest challenges for IMU-based mocap" but everything that follows is root translation / vertical drift; heading is never addressed. Appendix notes vertical drift can come from "biased sensor error from calibrations".
- Robustness-to-length check: Table 3 re-evaluates on 50 s windows instead of 10 s and finds "degradation of model performance is minimal" — 50 s is far below the timescale of gyro-only yaw drift.

## Key numbers (with table/figure reference)

Table 1 (online), TIP vs TransPose: joint angle error 12.3° vs 13.1° (DIP-IMU eval), 9.5° vs 11.4° (TotalCapture), 15.3° vs 17.4° (DanceDB); position error 5.9 / 5.4 / 8.2 cm. Root error after 10 s: 0.20 m (TotalCapture) vs 0.35 m TransPose. Note TIP's angle metric differs from the TransPose "SIP/angular" split, so cross-paper numbers are not directly comparable.

## What we can reuse / what to be careful about

- The SBP idea — predicting *which* body points are stationary — is a learned version of foot-contact detection and is a natural gate for "trust the camera heading now".
- Their evaluation window (≤50 s) is a warning: none of these benchmarks would reveal minute-scale yaw drift.

## Open questions this raises

- Would a transformer over a long IMU window learn to detect slow heading inconsistency between sensors? TIC (2025) says yes for the differential part.
