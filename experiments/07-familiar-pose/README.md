# 07 — Familiar-pose gate + in-pose measurement on MoVi (markerless main line)

**Date:** 2026-08-31 · **Status:** first end-to-end result on MoVi

## What it tests (D33 pipeline, steps i–ii, on real detector data)

Learn a heading-invariant pose template + the camera's per-pose heading bias
from the first third of an idle-like motion (standing in for the trusted
post-reset window); on later frames that match the template, take the in-pose
measurement (`familiar.py`); score the correction an automatic full reset
would apply against segment-frame truth.

## Result (5 subjects, RTMPose-x wholebody, 2 cameras, 46 matched bone-windows)

| bone | raw MAE | **after per-pose bias** | p95 (cal) |
|---|---|---|---|
| chest | 5.9° | **3.7°** | 8.3° |
| hip | 6.7° | **3.5°** | 11.2° |
| shin L / R | 7.8 / 8.0° | **4.8 / 4.7°** | 8.9 / 12.7° |
| thigh L / R | 13.1 / 3.0° | 18.3 / 7.0° | 24 / 9.3° |

Per motion (calibrated MAE): taking_photo 0.9°, checking_watch 3.4°,
crossarms 4.2°, phone_talking 4.8°, scratching_head 5.6°, sitting_down 6.3°,
cross_legged_sitting 7.2°.

## Reading

- **The pipeline works end to end on real detector data: chest, hip and
  shins land inside the 5° budget once the per-pose bias from the trusted
  window is applied** — hip improves 6.7° → 3.5°. This is the automatic-full-
  reset measurement path validated at small scale.
- Thighs stay unreliable (knee-plane estimator; cross-legged worst) — as
  everywhere else. In the real product thighs/shins follow the reset pose
  assumption; here they are measured only as a stress test.
- 9 of ~35 motion segments never re-matched the template — matching threshold
  and window logic need tuning, and MoVi's 3–8 s motions are a weak proxy for
  recurring idle poses.
- n is small (4–15 windows per bone). The real evaluation needs the own-room
  recordings with genuinely recurring poses (exp 08, blocked on the beacon
  hardware).
