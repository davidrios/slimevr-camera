# Numbers from ../drift-lab (read 2026-08-26)

Source: `drift-lab/logs/20260825_101112_runA_test.csv` — 63 min, 8 × BNO085 on
the rigid bar, static (|acc| std 0.011–0.016 g), mag off, Stay Aligned and
drift compensation off, raw `getRawRotation()` at 10 Hz, temps 32–38 °C.
Heading = floor projection of the quaternion's forward axis.

| tracker | yaw change over 63 min | rate |
|---|---|---|
| 12 | +164° | +2.60 °/min |
| 13 | +162° | +2.56 °/min |
| 14 | −130° | −2.05 °/min |
| 15 | −93° | −1.48 °/min |
| 16 | −41° | −0.64 °/min |
| 17 | −278° | −4.41 °/min |
| 18 | +41° | +0.65 °/min |
| 19 | +14° | +0.23 °/min |

**Static yaw drift of these BNO085 units: 0.2–4.4 °/min, sign and magnitude
per unit, roughly linear over an hour.** That is 5–10× the bias I had assumed
in the synthetic IMU model (±0.5 °/min) — defaults updated to ±3 °/min.
Caveat: whether the rate is linear or has structure needs `analyze.py`
(relative rotation between bar-mounted units); this is just endpoint/duration.

The `runX_*` logs (16 and 14 min, 100 Hz) had one tracker worn and moved
(thigh, upper arm) while the others stayed on the bar; the bar itself was
apparently moved (still trackers show up to 12 °/min apparent yaw), so they
do not separate drift from real rotation without the relative analysis.

Implications for the camera project:
- With corrections every ~35 s (experiment 01 cadence), 4.4 °/min alone leaves
  up to ~2.6° between windows — still inside budget, but the cadence matters.
- A correction every 5–10 min would remove 20–40° per tracker: the value of
  the project in one number.
- Motion-dependent (scale-factor) drift is NOT measurable from these runs;
  needs drift-lab runs B/C (turntable / known angle).

What drift-lab cannot give: camera-side detector bias — there is no video.
