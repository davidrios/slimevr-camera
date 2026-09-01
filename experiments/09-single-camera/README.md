# 09 — Single-camera familiar-pose measurement on MoVi (D36)

**Date:** 2026-09-01 · **Status:** first single-camera result; view-dependence quantified

## What it tests

Exp 07's protocol with 3D joints from **one view** via MotionBERT monocular
lifting (`mono.py` + `tools/motionbert/`, see `literature/2022-zhu-motionbert.md`)
instead of 2-cam triangulation. PG1 (≈frontal) and PG2 (≈90° side view —
verified from truth: the hip lateral axis is 99% in PG1's image plane, 98%
along PG2's depth axis) each evaluated as "the user's one camera".
5 subjects, wholebody-performance 2D, `lite`/`full` checkpoints.

## Result (calibrated MAE °, vs exp 07's 2-cam column)

Per-motion calibrated MAE, PG1 lite (full similar):

| motion | PG1 1-cam | exp 07 2-cam |
|---|---|---|
| crossarms | **1.6** | 4.2 |
| checking_watch | **2.0** | 3.4 |
| taking_photo | **5.3** | 0.9 |
| phone_talking | 10.2 | 4.8 |
| scratching_head | 23.7 | 5.6 |
| sitting_down | 47.1 | 6.3 |
| cross_legged_sitting | 35.4 | 7.2 |

Pooled per bone (PG1 lite): chest 7.4° raw / 13.1° cal, hip 8.7 / 11.2
(calibration *hurts* pooled numbers — see artifact below); shins/thighs
40–130° — catastrophic, dominated by seated motions.
PG2: template matching essentially fails (lite: 0 matched windows in 22
motions; full: 24 windows, chest 13.8° cal).

## Reading

1. **Frontal standing familiar poses survive the loss of the second camera**:
   simple standing idles land at 1.6–5.3° calibrated — inside the 5° budget,
   comparable to 2-cam. This is the case D33 needs for the standing reset pose.
2. **Seated poses currently fail monocular**, twice over: (a) near-horizontal
   bones depth-flip (~130° shin errors — sign-of-z ambiguity, not noise);
   (b) chest/hip stay 11–30°. Part of (b) is a **protocol artifact**: the
   trusted window is the first third of the same segment, which for
   sitting_down is a *different phase* (standing→sitting), so the learned bias
   doesn't transfer and matched-window errors get *worse* with calibration. In
   the product the seated template is learned while seated. MoVi can't test
   that properly (no genuinely recurring poses — same caveat as exp 07).
3. **The pose gate degrades with the measurement**: the descriptor is built
   from the same monocular 3D, so bad 3D produces both false matches
   (standing-phase template matched seated frames on PG1 — never happened with
   2-cam) and total match failure (PG2: descriptor distances explode because
   the hip-width normalizer is depth-dominated from the side and collapses).
4. **View dependence is the big new variable.** Frontal ≈ works; side-on fails
   at the gate before measurement is even attempted. Product-wise this is
   partially fine — reset poses can face the camera, and *the lifted pose
   itself tells us the view quality* (image-plane fraction of the hip/shoulder
   line → decline correction when depth-dominated) — but it must become an
   explicit confidence signal.
5. Checkpoints: `full` slightly better on legs, similar on chest/hip. Caveat:
   `full` was fed the pixel normalization the `global_lite` wild path uses,
   not the crop normalization it was trained with — treat its numbers as a
   lower bound.

## 09b — IMU-prior flip disambiguation + agreement gate (2026-09-01)

Per tracker+window, the measured heading and its depth-mirrored hypothesis
(`mono.mirror_depth`, sign-of-z in the camera frame) compete for closeness to
a simulated drifted IMU heading (truth + constant per-window offset
~N(0, σ); σ=1° in the trusted window). `familiar.choose_by_prior`.

| PG1 lite, calibrated MAE | none | with prior (σ=1–5°, identical) |
|---|---|---|
| chest / hip | 13.1 / 11.2° | 11.6 / 9.7° |
| shins | 51–60° | **24°** |
| thighs | 41–46° | **28–33°** |
| legs p95 | 113–147° | 52–73° |

- **Disambiguation halves the leg error and needs almost nothing from the
  IMU**: σ=1° and σ=5° give identical results — flips are ~180°-class, so
  even a badly drifted prior separates the hypotheses. The pure z-mirror
  explains about half the seated error; the rest is genuine monocular
  degradation (elevation/shape, not a clean flip).
- **The same prior gives an agreement gate** (`dev_prior` column): apply a
  correction only when the (bias-corrected) camera heading agrees with the
  IMU within a tolerance. σ=3°, tol=10°: **38% of correction opportunities
  kept, torso 3.8° / legs 4.7° MAE, worst kept 13.2°** — stable for σ=1–5°.
  This is partly circular in simulation (prior ≈ truth) but it *is* the
  product mechanism: the camera declines rather than mis-corrects; the
  failure mode is "no automatic reset" (today's status quo), never a bad one.
  Opportunistic 30–50% coverage of matched windows is enough for D33.

Ideas still open: torso-scaled view-robust descriptor + view-quality gate
(the side-view gate failure is untouched by 09b); the real seated evaluation
needs exp 08's own-room recording (template learned genuinely in-pose).

Results: `results/exp09_wholebody-performance_{lite,full}.csv` (09b columns:
`mode`, `dev_prior`).
Run: `uv run python experiments/09-single-camera/evaluate.py --subjects 1 2 3 4 5 --ckpt lite --prior-sigmas 1 3 5`
(lifted 3D cached in `data/movi/lift3d/`).
