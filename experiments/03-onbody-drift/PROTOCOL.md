# 03 — On-body drift vs gross motion (protocol, David's proposal 2026-08-26) — OPTIONAL, see D26

**Status:** optional. Per D26 the system must not depend on any offline
drift model; this run only calibrates the *harness* for David's own units and
bounds the cadence for one hardware set.

**Goal:** measure σ_m — how much unpredictable yaw error each tracker
accumulates per unit of gross motion — on the real body, with real straps,
absolutely (not just relatively). This number sets the required camera
correction cadence (exp 02 revision).

**Idea:** full tracker set worn; full reset in a *known pose*; move; return to
the same known pose and hold still; repeat. At every hold, the true yaw of
each tracker equals its yaw at the reset (same pose), so the logged raw yaw
minus its value at reset is the accumulated error. Consecutive holds give
per-interval increments; the logged quaternions give the gross motion in
between. Regress increment² against gross motion → σ_m per tracker.

## Why not BVH

`BVHRecorder` streams the processed `HumanSkeleton` (after mounting, resets,
filtering, leg tweaks, Stay Aligned). It measures the corrections, not the
drift. Use `DriftLogger` (`SLIMEVR_DRIFTLOG=1 … _HZ=100`) — raw
`getRawRotation()`, already validated in drift-lab. A BVH alongside is fine as
a secondary record of what the user *saw*.

## The known pose is the noise floor — use a jig

Human pose repeatability is ~3–5° per joint freehand, the same order as the
signal. Make it mechanical:
- feet: tape outlines on the floor, heels against a wall skirting;
- hips/chest: back and shoulders flat against a wall or door frame;
- arms: elbows/forearms resting on a fixed object (table edge, chair arms) or
  hands on two taped marks on the wall;
- head: HMD yaw from SteamVR is a trusted reference anyway.
Repeatability check: do 3 holds in a row with ~10 s of tiny motion between
them. The spread of yaw across those is the floor; intervals must accumulate
several × that to be measurable.

## Procedure

Settings: mag off, Stay Aligned off, drift compensation off (it is inert
anyway), DriftLogger on at 100 Hz. Note wall-clock of every event.

1. Warm up trackers 15–20 min on the body (thermal).
2. Enter the jig pose. Full reset. Hold still 20 s. (t₀)
3. Move for interval *i* — vary the *amount* across intervals, keep the *kind*
   representative: walking around, sitting/standing, arm gestures, some
   turning, a bit of vigorous play. Suggested: 1, 2, 5, 5, 10, 10 min.
4. Return to the jig pose. Hold still 20 s. Do NOT reset (a reset discards
   the accumulated-error reading). Tap detection or a note marks the hold.
5. Repeat 3–4. Optionally one long final interval (15–20 min).
6. Reset at the end if you want to keep playing; it is irrelevant to the data.

(No rigid bar exists — drift-lab used a table. If two spare trackers can be
taped rigidly to one object on a limb, their relative drift is jig-free
truth for that limb; optional.)

## Analysis (to write: `analyze.py` in this folder)

- Detect holds automatically: gyro speed < threshold for > 10 s, plus the
  noted times.
- Per tracker, per hold: yaw error = heading(q(hold)) − heading(q(t₀)), using
  the same-axis definition from `slimevr_camera.heading`.
- Gross motion per interval: ∑ |rotvec(q_t q_{t−1}⁻¹)| (all axes, degrees).
- Fit: E[Δψ²] = σ_m² · G + floor². Report σ_m per tracker and per body part,
  and whether increments look Gaussian/independent (random walk) or show a
  consistent sign (systematic → partly calibratable after all).
- Feed σ_m into `synth/imu.py` and rerun exp 02 to get the cadence answer.

## What it also measures for free

- Strap/mounting slip: a yaw error that *jumps* at a hold and stays.
- Thermal tilt: pitch/roll at each hold vs t₀.
- Whether feet/ankles (extensions) differ from thighs — feeds D19.
