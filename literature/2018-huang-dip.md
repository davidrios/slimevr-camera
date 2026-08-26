# Deep Inertial Poser (DIP): Learning to Reconstruct Human Pose from Sparse Inertial Measurements in Real Time

- **Authors / venue / year:** Yinghao Huang, Manuel Kaufmann, Emre Aksan, Michael J. Black, Otmar Hilliges, Gerard Pons-Moll — SIGGRAPH Asia / ACM TOG 37(6), 2018
- **Link:** https://arxiv.org/abs/1810.04703 ; project + dataset https://dip.is.tue.mpg.de/
- **Code:** released "for research purposes" via project page (MPI license, registration). TensorFlow-era code; not evaluated for backend.
- **Read depth:** full read of §4.2–4.5 (sensors, calibration, normalization, data collection), §5 tables, appendix C (heading normalization). Not run.
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

The founding sparse-IMU (6 sensors) pose paper and the source of DIP-IMU. Its calibration procedure (head-sensor-defines-world + straight-pose bone offsets) is the protocol every later work copies, and it is the same in spirit as SlimeVR's full reset. It does *not* handle drift after calibration at all.

## What they do

- 6 Xsens MTw IMUs (head, pelvis, wrists, knees/lower legs). Inputs: orientation + acceleration; BiRNN regresses SMPL joint rotations. Trained on synthetic IMU from AMASS, fine-tuned on DIP-IMU.
- **Calibration (§4.2, Fig. 4):** (1) The head sensor is placed so its axes align with the SMPL frame; the inverse of its orientation at calibration time defines R_TI (inertial→SMPL). (2) Subject holds a known "straight pose" (an I-pose/T-pose) for a couple of seconds; the per-sensor bone offset is R_BS = inv(R_TB0) · R_TS0 (eq. 7). So: one global heading reference from one sensor, plus per-sensor sensor-to-bone offset from a pose assumption — exactly SlimeVR "full reset" + "mounting reset".
- **Before calibration (§4.5):** "To compensate for different magnetic offsets across IMUs, a heading reset is performed first. The sensors are aligned in a known spatial configuration, after which the heading is reset." I.e. Xsens sensors are heading-aligned with each other *physically* (all in one box) before being strapped on. This is the step SlimeVR users cannot do and that mag-off IMUs cannot do.
- **Normalization (§4.3):** all bone orientations are expressed relative to the root (pelvis) sensor per frame, so the network is invariant to facing direction. Appendix C: "per-frame heading removal" (yaw-only normalization) gave 40.18° vs 15.77° — i.e. the network needs full root-relative normalization, not just yaw removal.
- **Drift:** not modelled, not measured. The only mention is generic ("real IMU data contains noise and drift"). Sequences are short (DIP-IMU: 64 sequences, ~92 min total, so ~1.5 min each); heading error within a sequence is treated as noise.

## Key numbers (with table/figure reference)

Table 2/3 (joint angle error over all joints, mean ± std; positional error cm):
- TotalCapture: SIP 16.98° / 5.97 cm; DIP BiRNN (fine-tuned) 16.84° / 6.51 cm; online (20 past, 5 future) 16.90°.
- DIP-IMU: SIP (17-sensor GT) — the 6-sensor SIP 24.00° / 6.34 cm; DIP online fine-tuned 18.49° / 6.63 cm.
- Note the ~15–17° mean joint angle error is *with* perfect calibration and no accumulated drift; this is the floor of the 6-IMU approach in 2018.
- DIP-IMU dataset: 10 subjects (9 m / 1 f), 17 Xsens sensors, 64 sequences, 330 k frames (~92 min @60 Hz), GT = SIP fit on all 17 sensors (not optical). Both raw and calibrated orientations released (TransPose §5 notes calibrated version strips root inertial data).

## What we can reuse / what to be careful about

- The calibration maths (eqs. 6–8) is a clean statement of what SlimeVR's reset does; reuse notation R_TI (world heading), R_BS (mounting).
- DIP-IMU's raw files include per-sensor heading offset from the pre-alignment; with 17 sensors and SIP GT one can measure residual per-sensor heading error, but sequences are too short to see gyro-only drift, and Xsens uses magnetometer-aided heading, so its drift regime is not ours.
- 16–17° reported angular error mixes pose-model error with sensor error; do not read it as an IMU heading-error number.

## Open questions this raises

- How much of the 16° residual is heading misalignment between sensors vs. pose ambiguity? DIP never separates them; PNP 2024 later reports 8.6° vs 12.1° "calibration error" for two calibrations of TotalCapture (see 2024-yi-pnp.md).
