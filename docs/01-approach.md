# 01 — Approach (v2, 2026-08-26 — revised after literature pass 1; see `04-lit-synthesis.md`)

## One-line version

Periodically, when the user is nearly still and well seen by the camera,
estimate each limb's **heading** from the camera, compare to the heading
implied by the tracker, and apply the difference as a yaw correction — the
same operation the existing yaw reset performs, but with a measured reference
instead of an assumed pose.

## Pipeline

```
            ┌──────────────┐        ┌───────────────────────────────┐
 camera ──► │ pose model   │ ─────► │ per-limb 3D direction (cam)   │
            │ (2D/3D/SMPL) │        │ + per-joint confidence        │
            └──────────────┘        └──────────────┬────────────────┘
                                                   │ extrinsics T_world←cam
 IMU quats ─────────────────────► FK skeleton ──► per-limb 3D direction (world)
                                                   │
                       stillness / confidence gate ◄┘
                                                   │
                                   Δψ_i per tracker, applied like a yaw reset
```

Components:

1. **Pose model → 3D joints, not rotations (D16).** SMPL regressors publish
   22–25° per-joint rotation error and twist is unreliable (§B). So: 2D
   keypoints per camera (RTMPose-class), triangulated across the 2 cameras
   into 3D joints; each bone's floor-projected direction gives heading.
   Expected heading error ≈ keypoint error / bone length → ~3° shin,
   ~5° forearm, worse on feet. Averaging over the still window helps.
   Monocular 3D lifting with our known bone lengths is the single-camera
   fallback; SMPL regressors only for occluded limbs.
2. **Camera-to-world extrinsics (D15).** Literature says people-only
   extrinsics reach 0.5–2° rotation but weak scale/translation (§D). Path:
   intrinsics once per camera *model* (not from people — 5–20 % focal error
   otherwise); floor/gravity from upright people cross-checked with IMU
   gravity; scale + world yaw + position from the Quest 3 trajectory vs. head
   keypoint (Umeyama + LS, de Sousa 2025); cam–cam relative pose from keypoint
   correspondences over time; refine with *accumulated* reset-moment
   skeletons (a single still pose is near-coplanar → degenerate). PR #1805
   already solves camera pose from HMD/controller poses — reuse candidate.
   Stretch: Touch Plus controllers' IR LEDs as free tracked fiducials (Q14).
3. **Gate.** Only correct when: body angular velocity low for N seconds
   (from IMU), limbs visible in both cameras, camera-side joints temporally
   stable. Do *not* gate on model confidence alone — RobustCap/DiffCap report
   MediaPipe confidence gating is brittle (§A). Stillness also makes
   clock-sync error irrelevant.
3b. **Clock sync (D17).** Coded blinking LED (ESP32 on the tracker network,
   IR or visible) in view of both cameras; blink times reported to the server
   → every frame is stamped on the server clock regardless of RTSP latency.
   Doubles as a fixed fiducial. See `notes/ir-beacon-idea.md`.
4. **Correction (D14).** Drift model per VIP 2018: one rotation about
   world-up per tracker, piecewise-constant between corrections. For each
   tracker `i`, `Δψ_i = ψ_i^cam − ψ_i^imu`, low-passed over several gated
   windows; correct the hip/root first, children relative to it (§A lesson).
   Watch mounting slip as a separate slow variable (TIC 2025). Apply through
   PR #1805's `TrackerResetOverride` hook into `TrackerResetsHandler` — SolarXR
   has no yaw-correction message, so a server hook is required.

## Why heading and not full pose

- Heading of a limb segment = direction of the bone projected on the floor.
  From two cameras this is a triangulation. From one camera it needs depth,
  which the pose model estimates (poorly), **but** we also know the user's
  bone lengths (SlimeVR has them) and the HMD height — strong priors that a
  monocular model does not use. Worth exploiting.
- Twist *about* the bone axis (e.g. forearm pronation) is the hardest thing
  for a camera and the easiest thing for an IMU that was recently reset. We
  should not ask the camera for it unless the literature says models are good
  at it now.
- Reduces the fusion to a scalar per tracker, which is what drifts.

## Why two cameras might be cheap insurance

Stereo from two arbitrary webcams needs their relative pose, but that can be
solved from the person themselves (keypoint correspondences over time) — the
"human as calibration object" line of work. Then depth ambiguity largely
vanishes. Worth checking whether one camera + body priors is already enough
before insisting on two.

## Model size / on-device

Latency is irrelevant for research. For *users*, RAM/VRAM and GPU vendor
matter (many have no discrete GPU). Plan: research on the RTX 3090 with the
most accurate model available, then quantize (int8 / fp16) toward CPU/iGPU,
then fine-tune on community data **in our specific regime** (indoor, single
person, near-still, VR headset on the face — headsets confuse face/head
keypoints). Fine-tuning target is not general accuracy but heading accuracy
under our gate.

## Data we can collect for free

Every SlimeVR user who opts in could provide synchronized
`(tracker quaternions, camera video)` where the first minutes after a reset
are high-quality pseudo-ground-truth for heading. That is a self-supervised
signal at scale. Privacy: David's view is that opt-in raw video is within reach — the HMD
covers the face, so it is largely anonymized already. Plan two tiers:
raw video (opt-in) and derived-only (keypoints/poses). Raw video is far more
valuable for fine-tuning.

## Product shape (D33, 2026-08-26): automatic full reset in familiar poses

We do not correct arbitrary motion. During the manual full reset (and the
user's habitual idle stances) the SlimeVR body model is trusted; the camera
learns what those poses look like and what its own bias is there. Whenever the
user is later seen in such a pose, the system performs the equivalent of a
full reset automatically: pelvis, chest and feet headings plus bone directions
are measured (all well-observed in a standing stance; feet ~1.7°, chest
~3–4°), and thighs/shins follow the same pose assumption the manual reset
makes. Heavy activity that drifts the trackers a lot is followed by a manual
reset, as today. The user is a participant: the system may ask for the reset
pose when its confidence is low. Success = the manual-reset horizon under
everyday movement grows from minutes to a session.

## Principle: the IMU is a black box (D26/D27)

Tracker sets in the field vary without bound (sensors, builds, straps,
firmware). We do not model their drift offline. The camera is the only ground
truth; each unit's drift statistics are learned at runtime from the
corrections the camera applies to it, and used only to decide *when* the
next correction is needed. Research investment goes to making the camera
side robust in diverse real conditions, which is where AI training pays off.

## Validation plan

- **Benchmark first (D18):** TotalCapture — raw Xsens IMU + 8 static cameras
  + Vicon. Inject gyro-only yaw drift, pick 2 cameras as "ours", measure
  heading recovery vs Vicon. No hardware needed. RobustCap/DiffCap MIT code
  is the harness.
- **Then hardware:** experiment 01 with the 2 RTSP cameras + 11 trackers.

## Prior art to build on

SlimeVR-Server **PR #1805** (jabberrock): one-shot wizard doing exactly
camera→IMU yaw + mounting correction with a phone camera and in-server
RTMPose. Analysis in `notes/pr-1805-analysis.md`. Our delta: periodic,
unattended, still-moment gating, 2 fixed cameras, beacon sync.

## Risks / things that could sink this

- Camera-derived heading turns out to be ±10° on short bones (feet,
  forearms) — literature gives no heading-only number (§A/§B). → TotalCapture
  benchmark measures this before hardware.
- Extrinsics-from-reset is too noisy without an HMD anchor (standalone users).
- Users don't have a camera with a clear view of their play space.
- Pose models fail on VR users (headset, controllers, odd poses like lying).
