# Numbers from ../drift-lab (source of truth: `drift-lab/FINDINGS.md`, 2026-08-25)

**Correction (2026-08-26):** an earlier version of this note reported
0.2–4.4 °/min static drift. That was wrong — it used the first CSV row as t₀,
which is the identity-quaternion placeholder before the first packet
(FINDINGS "Pitfalls"). Always read FINDINGS.md rather than re-deriving.

## What drift-lab established (8 hand-built BNO085 trackers, mag off, raw rotation)

1. **Static drift is negligible: worst unit −0.94 °/hour, common mode −0.10 °/hour,
   spread after 63 min 1.09°.** Both firmware paths null gyro bias at rest
   (SH2 `CAL_ON_TABLE`; VQF `restBiasEstEnabled`), so error can only
   accumulate while moving.
2. **The drift is gyro scale-factor error:** turntable, ~82 revolutions,
   dwell-to-dwell increments: tracker 17 **+0.427 % ± 0.025** (+1.54° per
   turn), tracker 12 **−0.231 % ± 0.012** (−0.83° per turn). Flat across
   719–9047 °/s peak rate → scale factor, not coning. Opposite signs → limbs
   drift *apart* (~2.4° per relative turn), which is what deforms the skeleton.
3. **Thermal accelerometer bias tilts perceived gravity by 0.8–5.7°** over an
   hour (unit-dependent). This is a pitch/roll error, not yaw — and it means
   "pitch/roll never drift" (docs/00) is only approximately true.
4. BNO085 exposes no gyro scale calibration; per-axis scale + cross-axis is
   9+ temperature-dependent parameters, so calibration "buys a factor, not a fix".

## Consequences for the camera project

- **Synthetic IMU defaults** (`synth/imu.py`): bias ≈ 0 (±0.02 °/min), random
  walk small, scale error ±0.45 % of yaw rotation — the motion-dependent term
  is the whole story.
- **Uncertainty is predictable:** drift since the last correction ≈ k_i ×
  (yaw rotation travelled). The server knows the rotation travelled. So the
  gate can be *demand-driven* (correct when accumulated rotation × worst-case
  k exceeds budget), and the still-window measurement itself is stable
  because nothing drifts while still.
- **Learn k_i from the camera (new idea, to evaluate):** each camera
  correction Δψ_i paired with the yaw rotation travelled since the previous
  one gives one observation of the tracker's effective scale error. Over a
  few corrections, k_i is estimable per tracker and can be applied
  feed-forward between windows — turning the camera from a periodic reset
  into a calibrator. Not sufficient alone (per-axis/cross-axis/thermal) but
  should cut between-window error substantially. VIP 2018 solved a constant
  heading per sensor; this would be a constant *rate-per-rotation* per sensor.
- **Thermal tilt matters for the estimator:** the IMU-side axis we compare
  against (`heading.py`) is rotated by the tracker's pitch/roll; a 5° tilt
  error moves a horizontal axis' floor heading by up to ~5°·sin(tilt-direction
  mismatch). Small but not zero — evaluate in the harness.
