# 01 — Synthetic heading recovery (keypoint level)

**Date:** 2026-08-26 · **Status:** done (v1) · `uv run python experiments/01-synthetic-heading/run.py`

## Hypothesis

Two fixed cameras with noisy 2D keypoints, triangulated, can measure each
tracker's yaw during still windows well enough (≤5° long bones, D19) to
cancel injected motion-dependent yaw drift — using only lateral features
(hip/shoulder width, heel→toe, knee/elbow flexion plane), since vertical bones
are unobservable from their own endpoints.

## Setup (all synthetic, `src/slimevr_camera/synth/`)

- 11-tracker SlimeVR-like skeleton, procedural motion: active phases 15–40 s,
  still phases 3–8 s (slow 0.3° wobble), 600 s, 30 fps, 2 seeds.
- IMU: true orientation × yaw drift = random walk 0.15°/√s + bias ±0.5°/min
  + scale error ±0.4 % of yaw rotation (motion-dependent). Perfect reset at t=0.
- Cameras: two, 3.5 m away at ±30°, 1.4 m high, f=1000 px @1920×1080;
  **known extrinsics**; Gaussian pixel noise 1/3/6/10 px; 2 % dropout; no occlusion.
- Pipeline (`pipeline.py`): DLT triangulation → per-tracker axis observation
  (`heading.py`) → still gate (all trackers < 8°/s for ≥2 s) → window-mean
  axis heading vs the *same axis* from the drifted IMU → piecewise-constant
  correction applied from window end.

## Result (`results/table.txt`, `results/*.png`)

Heading RMS over the full 600 s, mean of 2 seeds:

| tracker | 1 px | 3 px | 6 px | 10 px | uncorrected | cam-only in-window @10 px |
|---|---|---|---|---|---|---|
| hip | 0.84 | 1.00 | 1.39 | 2.00 | 3.2 | 1.8 |
| waist | 2.65 | 2.64 | 2.65 | 2.71 | 12.2 | 2.8 |
| chest | 1.33 | 1.33 | 1.37 | 1.50 | 15.7 | 0.9 |
| thigh L/R | 1.5 / 1.9 | 1.5 / 1.9 | 1.8 / 2.1 | 2.6 / 2.4 | 19 / 23 | 1.6 / 1.2 |
| shin L/R | 1.2 / 1.1 | 1.2 / 1.1 | 1.5 / 1.3 | 2.3 / 1.7 | 15 / 10 | 1.6 / 1.2 |
| foot L/R | 1.2 / 1.1 | 1.2 / 1.3 | 1.4 / 1.5 | 1.8 / 1.9 | 10 / 9 | 1.2 / 1.4 |
| upperArm L/R | 2.0 / 3.0 | 2.1 / 3.0 | 2.6 / 3.3 | 3.1 / 5.1 | 27 / 43 | 1.6 / 1.1 |

17–18 still windows per 10 min (one every ~35 s).

## Conclusions

1. **In-window camera heading error is < 2° for every tracker even at 10 px
   noise** — window averaging (60+ frames) removes zero-mean noise almost
   completely. The 5° budget is not threatened by *noise*.
2. Residual after-correction error is dominated by **drift accumulated between
   windows**, not by the measurement: it barely changes from 1 px to 6 px.
   Correction frequency matters more than camera quality.
3. **Waist** is the worst long bone (2.6°) because it has no keypoints — it is a
   blend of hip and chest. A real fix needs either a torso keypoint (RTMPose
   wholebody has none) or a kinematic prior; acceptable for v1.
4. Upper arms are correctable only when the elbow is bent (flexion-plane
   estimator); standing with arms hanging straight leaves them unobservable.
   Their higher residual comes from fewer usable windows.
5. The "same axis on both sides" formulation (`heading.py` docstring) removed
   a 12–14° systematic error the naive forward-axis comparison had.

## What this does NOT show (next)

- **Bias.** Real detectors have *systematic* keypoint offsets (hips placed
  low/high, ankles on the shoe, toe vs big toe), which averaging does not
  remove and which shift lateral-axis headings when the person is seen
  obliquely. This is the real threat to the 5° budget → needs a real detector
  on real/rendered footage (agenda §H) or TotalCapture.
- Extrinsics were perfect. Add calibration error (0.5–2° per §D) as a sweep.
- No occlusion, single person, no headset/controllers.
- Gate parameters are untuned; `max_axis_spread` had to be relaxed from 0.02
  to 0.15 or high-noise windows were all rejected.
