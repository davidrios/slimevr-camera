# 02 — Learning the gyro scale error from camera corrections

**Date:** 2026-08-26 · **Status:** done (v1) · `uv run python experiments/02-scale-learning/run.py`

## Hypothesis

Per drift-lab (`../../notes/drift-lab-numbers.md`), yaw error ≈ k_i × signed
yaw rotation travelled, k ≈ ±0.4 %, ~zero at rest. Then successive camera
corrections give observations `Δcorrection = −k_i × travel`, so k_i can be
estimated per tracker (RLS, `pipeline.ScaleLearner`) and applied feed-forward
between windows, relaxing the required correction cadence.

## Setup

As experiment 01 (2 cameras, 3 px noise, perfect extrinsics), 20 min × 3
seeds, but with the IMU model **aligned to drift-lab**: bias ±0.02 °/min,
random walk 0.02 °/√s, **signed** scale error ±0.45 %. Motion now includes
in-place turns (2/min, ±90–360°) because a signed scale error needs *net*
rotation to act on; pure oscillation cancels. Three still-window cadences.
Learner: prior k ~ ±2 %, camera noise 1°, ignores intervals with < 45° net travel.

## Result (`results/results.json`, `results/*.png`)

Heading RMS over 20 min (includes the learning phase), mean of 3 seeds:

| still window every | long bones: reset only | + learned k | upper arms: reset | + k | k̂ abs. error |
|---|---|---|---|---|---|
| ~35 s | 0.77° | 0.62° | 0.79° | 0.70° | 0.05 % |
| ~2 min | 1.28° | 0.93° | 1.60° | 1.45° | 0.03 % |
| ~5 min | 1.83° | 1.68° | 2.05° | 2.05° | 0.04 % |

Seed 0, k_true → k̂ (%): hip 0.41→0.37 / 0.44 / 0.36 across cadences; thigh
0.30→0.36 / 0.24 / 0.36; foot −0.14→0.01 / −0.15 / −0.13.

## Conclusions

1. **k is learnable** from the camera alone: ~0.03–0.05 % absolute (≈10 %
   relative) after 20 min, at any cadence, with no user action.
2. **The gain is modest (≈20–30 % at ≤2 min cadence, ~nil at 5 min)** —
   because with drift-lab's error model the reset-only residual is already
   small: **1.8° at a 5-minute cadence, inside the 5° budget.** With a signed
   scale error, back-and-forth limb motion cancels; only net turning
   accumulates error (≈0.4 % × 300°/interval ≈ 1.2° here).
3. At 5 min cadence only 4 windows fit in 20 min, so k̂ arrives too late to
   help within the run; over a multi-session lifetime (k_i is a hardware
   constant, persistable) the feed-forward would apply from the first minute.
4. **Implication for design (the real result):** correction frequency
   requirements are driven by *net rotation* (turning), not by time. A
   demand-driven gate on accumulated |net yaw| × k_max is the right trigger,
   and a still moment every few minutes is enough for long bones.

## Caveats

- Yaw-axis scale only. Real error is per-axis + cross-axis + thermal; a bone
  rotating about tilted axes will show effective k varying with pose.
  Learnability of a *pose-dependent* k is untested.
- Turning frequency in real VR play is unknown (Q16); games with lots of
  spinning make cadence matter more.
- `pipeline.yaw_rate` integrates the world-up component of angular velocity;
  for large tilts this is not exactly "heading change" (coning-like terms).
- Experiment 01's table was produced before the IMU model was aligned to
  drift-lab (bias ±0.5 °/min, |rate|-based scale error); its conclusions on
  camera noise stand, its residual magnitudes are pessimistic.

## Revision (same day) — the "net turning" conclusion was wrong

David's field observation: drift appears with modest movement and no
turning. Physically right: per-axis scale errors + cross-axis misalignment +
gravity-correction leakage produce yaw increments on *any* rotation about
non-parallel axes (rotate X, then Y, then back: net zero, residual about Z ∝
θ·φ·Δk). Those increments do not cancel and their sign depends on the motion
sequence — effectively a **random walk driven by gross 3D motion**. If the
error were predictable we would calibrate it and this project would not
exist. The turntable's yaw-scale factor is the *predictable* part, and it is
not the dominant one.

The IMU model now has `motion_rw_deg_per_sqrt_deg` (σ_m): yaw std per
√(degree of gross rotation), **magnitude unmeasured**. Sweep, 20 min × 2 seeds
(`results/results_mrw*.json`), long bones / upper arms, reset-only:

| σ_m (°/√°) | every ~35 s | every ~2 min | every ~5 min |
|---|---|---|---|
| 0.02 | 0.9 / 1.2 | 1.7 / 2.3 | 2.2 / 4.0 |
| 0.05 | 1.7 / 2.1 | 3.2 / 4.2 | 4.3 / 7.8 |
| 0.10 | 3.2 / 3.9 | 6.1 / 7.8 | 8.2 / 14.8 |

Revised conclusions:
1. **Learning k is useless or harmful** once the unpredictable term is present
   (it fits the random walk: +scale is worse at 2 min cadence). Dropped from
   the design; keep the code as an ablation.
2. **Cadence matters, and the required cadence depends on σ_m**, the one
   number nobody has measured. Residual ∝ σ_m × √(gross motion since last
   correction). At σ_m = 0.05 a 5-minute cadence just misses the 5° budget
   on long bones and clearly misses on arms.
3. **Measure σ_m next (drift-lab run E):** the differential method works on a
   *moving* rigidly-coupled rig — relative rotation between bar-mounted units
   must stay constant however the bar moves; only common-mode error is
   invisible, and relative drift is exactly what deforms the skeleton. Strap
   the bar to a thigh/forearm, move modestly for 10–15 min at 100 Hz, and
   regress relative yaw variance against gross rotation. That gives σ_m
   without any camera.
4. Trigger design: gate on **gross motion** since last correction (∑|ω|dt,
   all axes), not on net yaw (D25 revised).
