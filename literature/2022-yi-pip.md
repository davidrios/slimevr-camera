# PIP: Physics-aware Real-time Human Motion Tracking from Sparse Inertial Sensors

- **Authors / venue / year:** Xinyu Yi, Yuxiao Zhou, Marc Habermann, Soshi Shimada, Vladislav Golyanik, Christian Theobalt, Feng Xu — CVPR 2022
- **Link:** https://arxiv.org/abs/2203.08528 ; project https://xinyu-yi.github.io/PIP/
- **Code:** https://github.com/Xinyu-Yi/PIP — GPL-3.0. PyTorch + RBDL + pybullet + qpsolvers; README: motion prediction ~120 fps on CPU, CUDA only recommended for error computation. Noitom Perception Neuron sensors in demo.
- **Read depth:** skimmed method; full read of §3 intro (calibration), Table 3, §5 "Drifts in Long-term Tracking" and Fig. 9. Not run.
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Adds a physics optimizer (contacts, joint torques, PD control) on top of a TransPose-style kinematic RNN. It is the only paper in this line that explicitly asks "does pose drift over long time?" — and answers with a synthetic experiment, not real IMU data.

## What they do

- Kinematics: RNNs estimate leaf/full joint positions, rotations, joint velocities, foot contact probabilities. Physics: a dual-PD-controller + QP solves for torques and contact forces satisfying constraints, giving smooth, non-sliding, physically plausible motion and translation.
- **Calibration:** "Similar to TransPose, we perform a T-Pose calibration at the beginning" — same protocol (magnetometer-aligned inertial frame + T-pose bone offsets), nothing new.
- **Drift discussion (§5):** "As a purely inertial sensor based approach, PIP inevitably suffers from drifts in long-term tracking." Translation drift ≈ 4.6 % of distance travelled (Fig. 3). "Regarding the subject's pose, we do not see an evident drift in our experiments. This may be because the subject is always moving." They then simulate a perfectly still sitting pose for **4.6 hours** (zero acc, constant orientation) and the *network's* pose output drifts by only 4.2° total (Fig. 9). Important: this measures the recurrent network's internal drift with **ideal, non-drifting sensor input**; real gyro yaw drift is not simulated. So it says nothing about sensor heading drift.
- Evaluates on DIP-IMU + TotalCapture; sequences are minutes long; Xsens/Noitom mag-aided heading assumed.

## Key numbers (with table/figure reference)

Table 3 (online):
- DIP-IMU: SIP 15.02°, ang 8.73°, pos 5.04 cm, mesh 5.95 cm, jitter 0.24 (TransPose online 16.68° / 8.85° / 5.95 cm / 0.61).
- TotalCapture: SIP 12.93°, ang 12.04°, pos 5.61 cm, jitter 0.20 (TransPose 16.58° / 12.89° / 6.55 cm).
- Translation drift 4.6 % of travelled distance (Fig. 3); still-pose network drift 4.2° over 4.6 h (Fig. 9).
- Latency 16 ms.

## What we can reuse / what to be careful about

- The physics optimizer is a strong "floor contact = still moment" prior, similar in intent to SlimeVR's Localizer; could inform which frames are safest for a camera-based heading measurement (foot planted, low velocity).
- Do not cite the 4.2°/4.6 h number as "IMU drift"; it is network drift under synthetic ideal input.
- Heavy dependency stack (RBDL, pybullet); not a candidate to embed.

## Open questions this raises

- How does PIP's physics layer react to a slowly rotating heading on one sensor? Untested in paper; the contact model might partly absorb it (foot sliding suppression) and thus hide it. Worth a synthetic experiment if we ever adopt a learned IMU prior.
