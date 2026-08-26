# 00 — The problem

## What a SlimeVR tracker is, precisely

Each tracker is a 9-/6-axis IMU (BNO085, BMI270, …) running sensor fusion on
the tracker and sending **orientation only** (a quaternion) to the server.
There is no position sensor. The server builds a kinematic skeleton
(`HumanSkeleton.kt`) from user bone lengths and *derives* joint positions by
forward kinematics from the HMD position down through the chain of tracker
orientations. Positional trackers (Vive/Tundra, OSC, WebSocket bridge) are
supported via a CCD IK solver (`IKSolver.kt`) but are the exception.

Consequence: **orientation error on a proximal bone becomes position error on
every distal bone**, scaled by limb length. A 10° yaw error on the hip tracker
moves the feet by roughly `sin(10°) × leg length ≈ 15 cm`.

## Where the error comes from

- **Pitch and roll** are continuously observable from gravity through the
  accelerometer. They do not integrate error, but accelerometer bias drifts
  with temperature (up to ~5° tilt per hour on some units, drift-lab).
- **Yaw** (heading about world vertical) is *not* observable from gravity.
  Without a magnetometer (most SlimeVR users run mag off because indoor fields
  are unusable) yaw is pure gyro integration. Every gyro bias, scale-factor
  error, cross-axis misalignment, temperature change and g-sensitivity
  integrates into yaw and never leaves.
- David's observation, consistent with the above: the drift is
  **motion-dependent and nonlinear**, not a fixed bias — consistent with
  scale-factor / cross-axis / g-sensitivity errors, which are proportional to
  the rotation actually performed, and with fusion-filter transients during
  fast motion. `../drift-lab/` runs A–D are designed to separate these
  (time-, angle-, shock-dependent components).
- Secondary: **mounting error** (tracker rotated in its strap), which is a
  constant offset per session, and **body/strap slip** during play.

So the drifting quantity is essentially one scalar per tracker: yaw offset
`δψ_i(t)`, slowly varying, occasionally jumping.

## What SlimeVR already does about it

| Mechanism | Where | What it does | Limit |
|---|---|---|---|
| Full / yaw / mounting reset | `TrackerResetsHandler.kt`, `reset/` | User stands in a known pose, presses a button; per-tracker yaw is re-referenced to the HMD's yaw. | Requires the user to notice and act; pose assumption (standing straight, feet forward) is only approximate. |
| Drift compensation | `TrackerResetsHandler.clearDriftCompensation` etc. | Measures yaw change between consecutive resets and extrapolates a linear correction. | Assumes drift is linear in time — exactly what David says it isn't. |
| Stay Aligned | `tracking/processor/skeleton/stayaligned/` | Uses soft priors about relaxed body poses (standing/sitting/lying) to nudge yaw toward plausible alignment. | Prior-based, not measurement-based; can fight real poses. |
| Localizer | `Localizer.kt` | Estimates root position from foot contacts when no 6-DoF device. | Not related to yaw, but shows the server already has "floor contact = still moment" logic we can reuse. |

None of these has an **external heading measurement**. That is the missing
ingredient, and it is exactly what a camera can supply.

## Why a camera, and why it is complementary

| | IMU tracker | Camera + pose model |
|---|---|---|
| Rate | 100+ Hz | 15–60 Hz, can be lower for our purpose |
| Latency | ms | irrelevant (offline) |
| Occlusion | none | limbs hidden behind body/furniture, out of frame |
| Drift | yaw drifts unboundedly | none — each frame independent |
| Absolute heading | no (after reset only) | yes, in camera frame |
| Depth / 3D | n/a | monocular is ambiguous; two cameras triangulate |
| Bone-axis twist | measured directly | weakly observable from silhouettes/keypoints |
| Setup | strap on | place camera, must know its pose relative to world |

The failure modes barely overlap. The IMU is trustworthy right after a reset
and degrades; the camera is trustworthy whenever the body is well seen and
never degrades. That is the standard shape of a fusion problem where one
sensor corrects the other's low-frequency error.

## What we are *not* trying to do

- Replace IMUs with camera tracking (that is a different product: full-body
  optical tracking, with its own occlusion and latency problems).
- Real-time fusion inside the tracking loop. Maybe later; not the goal.
- Model the drift analytically. Accepted as intractable per David.
