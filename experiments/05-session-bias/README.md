# 05 — Can the post-reset IMU window calibrate the detector's bias? (quick test)

**Date:** 2026-08-26 · **Status:** quick test on exp 04 data (MoVi, RTMPose-m, 5 subjects); no new code beyond the inline analysis recorded here.

## Hypothesis (David)

The SlimeVR body model is trustworthy for a short window after a full reset in
a known pose. Use that window to learn the camera detector's bias per
user/room/camera placement; afterwards the bias-corrected camera corrects the
IMU. Periodic resets bound the horizon.

## Test 1 — calibrate on the first 30/60 s, evaluate on the rest

Per subject and bone, learn (a) a constant offset, (b) offset per 30°/15° bin
of body yaw, from the first N seconds; evaluate residual sd on the remaining
frames (1-s rolling-mean error). Result: **no improvement** (chest 4.8 → 5.1°,
hip 7.8 → 7.9°, thighs 11.6 → 11.7°; yaw-binning makes it worse). Unfair to
the idea, though: MoVi's first minute is kicking/dancing and the test frames
are 20 other motions — the calibration never sees the poses it is asked about.

## Test 2 — within similar poses: first half of each motion → second half

| bone | uncorrected sd | per-subject constant | per-motion offset (1st half) | **within-motion residual sd (median)** |
|---|---|---|---|---|
| chest | 5.4° | 5.5° | 5.0° | **1.8°** |
| hip | 8.5° | 8.4° | 7.9° | **2.1°** |
| shin L / R | 7.6 / 6.5° | 7.6 / 6.0° | 6.6 / 5.3° | **2.6 / 1.9°** |
| thigh L / R | 12.5 / 9.3° | 12.3 / 9.3° | 13.0 / 9.2° | **5.3 / 1.9°** |

## Reading

- **Within one pose family the error is nearly constant (~2° sd).** The
  bias is a deterministic, repeatable function of pose and view — not noise.
  That is the good news: it is learnable.
- **But a constant learned a few seconds earlier does not transfer** (pooled
  residual barely drops): the bias changes as the pose evolves within a
  motion (seconds timescale). A per-session constant, or a yaw-bin table, is
  the wrong model.
- **What would work:** a pose-conditioned correction — a model that maps the
  detected pose (limb directions, joint angles, view direction) to a heading
  correction. Learned globally from diverse data (= the fine-tuning bet,
  D28) and refined per session in the trusted post-reset window (David's
  idea). The two are the same mechanism at different scales; the session
  window supplies the user/room/camera-specific residual.
- Practical corollary for the correction loop: prefer correcting in poses
  that were seen during the trusted window (e.g. the reset pose itself, or
  the user's habitual idle stance) — there the learned bias is directly
  applicable and the residual is ~2°, inside budget.

## Caveats

MoVi motions are 3–8 s; "first half / second half" is a weak proxy for a
VR session where the same idle poses recur for minutes. Only body-balanced
keypoints; 5 subjects.
