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
