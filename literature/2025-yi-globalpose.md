# Improving Global Motion Estimation in Sparse IMU-based Motion Capture with Physics (GlobalPose)

- **Authors / venue / year:** Xinyu Yi, Shaohua Pan, Feng Xu — ACM TOG 44(4), SIGGRAPH 2025
- **Link:** https://arxiv.org/abs/2505.05010 ; project https://xinyu-yi.github.io/GlobalPose/
- **Code:** linked from project page (github.com/Xinyu-Yi/GlobalPose); arXiv page license CC BY-NC-SA 4.0; repo license not checked.
- **Read depth:** HTML version read via fetch summary (method, calibration, long-term evaluation, Tables 1/5/6). Not run. Numbers below are from that summary — re-check against the PDF before citing precisely.
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Latest of the Tsinghua line. Two things new for us: a **one-step walking calibration** that estimates sensor-to-bone rotations *and* relative heading drift simultaneously, and a **20-minute long-term evaluation** (on a Nymeria sequence) — the first minute-scale drift test in this family.

## What they do

- Removes the flat-floor assumption of PIP/PNP: contact detection + physics allow 3D translation (stairs, slopes). Adds "gravity refinement": the network reconstructs the root-frame gravity direction across stages, progressively denoising global orientation (pitch/roll of the root — not yaw).
- **Calibration:** instead of T-pose, the user takes one standard step forward; double-integrated ZUPT acceleration of each IMU gives a forward direction per sensor, from which R_BS and the *relative* heading offset between sensors are solved. Preferred over T-pose by 72 % of users in their study. Still a one-shot calibration; does not run continuously.
- **Drift handling:** gravity refinement (fixes tilt error), physics contact constraints (fix position drift), and the calibration step (fixes relative heading at t=0). No mechanism for yaw drift after calibration; the 20-min test reports position error per period, not heading error.

## Key numbers (with table/figure reference)

- Table 1, TotalCapture official calibration: SIP 10.87° ± 5.22, angular 10.55° ± 4.55, pos 4.31 cm (PNP 13.95° / 13.54° / 7.37 cm — note these PNP numbers differ from PNP's own Table 1, presumably a different evaluation protocol; unverified).
- Table 5 translation drift (% of distance): 4.68 % official cal, 3.74 % DIP cal.
- Table 6, 20-min Nymeria sequence, per-period joint position error: 6.18 → 6.38 cm (PNP 7.30 → 8.23 cm) — "no significant drift" in pose error over 20 min with Xsens (mag-aided) sensors.

## What we can reuse / what to be careful about

- The walking-step calibration is attractive for SlimeVR (no T-pose) and is exactly the kind of observation (walking direction ≈ forward) a camera can verify.
- 20 min "no significant drift" was measured with Xsens MVN data (magnetometer-aided, professionally calibrated), so it does not transfer to mag-off BNO085/BMI270 trackers. Treat as an upper bound on what good hardware achieves.

## Open questions this raises

- Does the Nymeria sequence's Xsens data have raw (drifting) orientations or MVN-fused output? If the latter, the 20-min test is not a sensor-drift test at all.
