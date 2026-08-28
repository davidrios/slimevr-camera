# 06 — TotalCapture: detector error at 1080p and the end-to-end loop (in progress)

**Started:** 2026-08-28 · TotalCapture is validation-only (D34).

## Data
S1, sequences walking1 / freestyle1 / acting1 (60 Hz; IMU, Vicon and video
frame-aligned). Camera pair **cam1 + cam8** (42° apart, ~5 m, 2.4 m high —
close to David's room); cam2 + cam7 (118°) as the wide alternative.
Reference = Vicon bone frames' fixed local axes (hip lateral +X, knee-flexion
normal −X for thighs/shins, chest ≈ +X; foot axis fitted from data because
TotalCapture has no toe joint). Loader conventions verified
(`slimevr_camera/data/totalcapture.py`).

## Stage A — detector heading error, walking1, cam1+cam8, RTMPose-x wholebody

1-s rolling-mean error (reset-referenced), continuous walking:

| bone | sd | MAE | p95 |
|---|---|---|---|
| chest | 5.7° | 4.8° | 11.0° |
| foot L / R | 8.5 / 6.3° | 4.4 / 3.7° | 14 / 11° |
| hip | 8.4° | 7.1° | 16.0° |
| shin L / R = thigh L / R | 11.3 / 10.3° | 6.2 / 4.9° | 36 / 20° |

**Finding: 1080p from 5 m gives the same error as MoVi's 800×600 from 4.5 m**
(chest 5.1–5.2, hip 7.0–7.5, thighs 12.5–13.5 there). Resolution does not
fix the pose-dependent bias any more than model size does — consistent with
a structural, learnable bias (exp 05, D32).

## Stage B — end-to-end loop
Calibrated Xsens bone orientation (R_ig·R_i·R_ib⁻¹) vs Vicon is **2–3° for
hip/chest, 5–10° for legs/feet** (the floor: a real IMU with a good
calibration). Injected drift (exp 02 model) adds ~1°/min here. walking1 has
no still windows (continuous walking); the single 0.5-s window found made
things worse — as D33 predicts, corrections belong in still, familiar poses.
Next: freestyle1 / acting1 (pauses expected), then a proper familiar-pose
gate rather than a stillness threshold.

## freestyle1 (cam1+cam8, RTMPose-x wholebody), 2026-08-28

Stage A, 1-s rolling mean: chest 4.9°, feet 5.3 / 2.9°, hip 8.6°,
thighs/shins 5.2 / 8.1° — same picture as walking1 and MoVi; feet again the
best when observable.

Stage B: **TotalCapture cannot test the familiar-pose loop.** Performers
never pause: the only still-and-familiar window in a 1-minute clip is the
opening stance itself (0.8–1.6 s), so the "correction" is applied from the
trusted window and then nothing recurs. The one early correction also shows
the known hip bias (~7°) being written into the IMU — exactly why the
per-pose bias must be learned first (D32). Conclusion: TotalCapture is a
detector-error and IMU-floor benchmark (stage A), not an end-to-end one;
the end-to-end loop needs sessions with recurring idle poses — David's own
recordings (exp 07, once the recorder hardware is up).

The IMU floor itself is a useful number: calibrated Xsens vs Vicon is
2–3° for hip/chest and 6–10° for legs on these clips — a research-grade IMU
with a careful calibration is *already* off by more than our 5° budget on
the legs, which says the legs' "truth" in any IMU-vs-camera comparison is
soft and the camera's own accuracy on legs is not the only limit.
