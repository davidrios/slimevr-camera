# PNP: Physical Non-inertial Poser — Modeling Non-inertial Effects in Sparse-inertial Human Motion Capture

- **Authors / venue / year:** Xinyu Yi, Yuxiao Zhou, Feng Xu — SIGGRAPH 2024
- **Link:** https://arxiv.org/abs/2404.19619 ; project https://xinyu-yi.github.io/PNP/
- **Code:** https://github.com/Xinyu-Yi/PNP — GPL-3.0; PyTorch 2.0 + CUDA 11.8 tested, RBDL 2.6, Python 3.8. Live demo code moved to GlobalPose repo. Runs 60 fps.
- **Read depth:** full read of §3.2.3 (calibration error modeling), §4 datasets and Table 1; skimmed the rest. Not run.
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Two things matter for us: (1) they synthesize *low-level* IMU signals (gyro/acc/mag) and run their own fusion filter, so the training data contains sensor noise and calibration error rather than clean orientations; (2) they quantify TotalCapture's "calibration error" as 12.1° (official calibration) vs 8.6° (DIP calibration) — a rare number for how wrong the IMU→bone frames are in a real dataset.

## What they do

- Observes that expressing leaf accelerations in the (rotating, accelerating) root frame makes that frame non-inertial; adds a fictitious-force estimator and a proper noise model to the synthetic data pipeline. Otherwise PIP-style RNNs + physics optimizer.
- **Calibration:** same practical protocol — R_WB = R_IWᵀ · R_IS · R_BSᵀ (eq. 9) with R_IW (IMU world → mocap world, i.e. heading reference) and R_BS (sensor-to-bone) obtained by **T-pose calibration**. §3.2.3: "as the subject cannot perform a perfect T-pose, the calibration step contains errors", so in synthesis they perturb R_IW and R_BS by random rotations with mean 0.01 rad and 0.1 rad (≈0.6° and ≈5.7°) plus a random-walk sensor-sliding model (rotation error random walk starting at 0.1 rad).
- **Drift:** no yaw-drift compensation. But the random-walk perturbation of R_BS during synthesis is a (weak) model of slowly changing mounting/heading offsets, and the two-calibration TotalCapture experiment measures robustness to a *static* frame error of 8.6° vs 12.1°.
- Translation drift plotted vs distance (Fig. 7): lowest of the compared methods.

## Key numbers (with table/figure reference)

Table 1 (SIP err / ang err / pos err / mesh err / jitter):
- TotalCapture official calibration (12.1° cal error): PNP 11.35° / 11.10° / 4.89 cm / 5.60 / 0.27; PIP 14.52° / 13.85° / 6.22; TIP 15.62° / 14.45°; TransPose 18.12° / 14.91°; DIP 18.73° / 17.57°.
- TotalCapture DIP calibration (8.6°): PNP 10.89° / 10.45° / 4.74 cm; PIP 12.93° / 12.04° / 5.61.
- DIP-IMU: PNP 13.71° / 8.75° / 4.97 cm; PIP 15.33° / 8.78° / 5.12.
- Going from 8.6° to 12.1° calibration error costs PIP ~1.6° SIP error and PNP ~0.5°, i.e. the models partially absorb static frame error.

## What we can reuse / what to be careful about

- The synthetic IMU pipeline (AMASS → 6-DoF trajectory → gyro/acc/mag with noise → fusion) is the right tool if we ever want to train anything on *drifting* orientations: add gyro bias/scale-factor terms and integrate. Code is GPL.
- 8.6°/12.1° is a static offset, not drift; still a useful order of magnitude for "how well-calibrated is a real dataset".

## Open questions this raises

- No evaluation of *time-varying* heading error; GlobalPose (2025) and TIC (2025) are the follow-ups that start to.
