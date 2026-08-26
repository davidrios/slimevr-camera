# PR #1805 "Video calibration PROOF OF CONCEPT" — code analysis

_Branch `pr-1805` in `../SlimeVR-Server`, commit 487e2419 vs `main`, 70 files, +8.5k lines (incl. 54 MB ONNX). Paths below are relative to `server/core/src/main/java/dev/slimevr/`; `VC/` = `tracking/videocalibration/`. Line numbers are from `git show pr-1805:<path>`._

## TL;DR

It is a one-shot **mounting + heading calibration wizard** (phone camera over WebRTC, 6-DoF HMD + SteamVR controller required), not a drift corrector. The camera is used in only two of six steps. The per-tracker fit solves 5 unknowns (global yaw + full local mounting quaternion) from a *walk-in-a-circle* sequence, using a **2D projected-direction residual** in a single view. There is no triangulation, no stillness gate, no persistence, no repeated correction. The integration hook (`TrackerResetOverride`) replaces the whole reset chain rather than adding a heading delta. Recommendation at the end: **borrow specific pieces, reference the rest**.

## 1. Camera extrinsics — `VC/steps/SolveCamera.kt`

- **Observations**: one correspondence stream only: the **RIGHT_HAND tracker position** (SteamVR controller, `tracker.position`) vs the **RIGHT_WRIST 2D keypoint** (`SolveCamera.kt:44,72`; LEFT_HAND commented out `:71`). HMD pose is *not* used for extrinsics (TODO at `:211`). Correspondences are thinned to ≥5 cm apart (`:38,157`) and need ≥100 (`:39,45`) → the user draws a "∞ loop" (GUI string `translation.ftl` `video-calibration-instruction-calibrate_camera`), ~5 m of controller path.
- **Unknowns (7)**: extra **yaw about world Y** applied on top of the phone-supplied `cameraToWorld` (`:246`), camera origin (3), and the **wrist offset in the controller frame** (3, `:190,217-219`). So rotation is 1-DoF: pitch/roll are *trusted from the phone's own orientation* (`PhoneWebcamSource.kt:282-285`, `OfferResponse.cameraToWorld`, `:352-358`).
- **Intrinsics**: not solved. `fx,fy,tx,ty` come from the phone app in the SDP answer (`PhoneWebcamSource.kt:283`, `CameraIntrinsic.kt`). Pinhole, **no distortion model** (`CameraIntrinsic.kt:15-24`). Camera frame is OpenCV-style (x right, y down, z forward; `project` requires z>0.1 `:16`).
- **Solver**: Apache commons-math3 `LevenbergMarquardtOptimizer` with a forward-difference numerical Jacobian, eps 1e-6 (`VC/util/NumericalJacobian.kt:9-33`). Residual = pixel error of projected wrist (`SolveCamera.kt:194-203`); unprojectable points get residual 1e6 (`:201-202`).
- **Search**: brute force over camera delay −300…+300 ms step 20 (`:61`) × 19 initial yaw placements at 3 m radius (`:81-82`, `placeCamera :165-178`) = 589 LM solves; keeps lowest RMS (`:88-110`). This grid search *is* the clock-sync strategy (see §5).
- **Assumptions**: phone orientation is gravity-correct; controller is tracked; wrist keypoint ≈ rigid offset from controller; no image-coverage check (TODO `:74`); `zeroMatches` centroid computed then unused (`:49-54`).

## 2. Per-tracker fit

### 2a. `TrackerResetOverride` — `VC/data/TrackerResetOverride.kt`
`bone = Yaw_Y(globalYaw) * rawTracker * localRotation` (`:14-19`, `twinNearest(IDENTITY)` for sign). Parameters: **1 global yaw (rad) + 1 full local quaternion (4 floats, normalised inside `buildTrackerReset`)** = 5 params (`SolveNonUpperBodyTracker.kt:281-284`, `SolveUpperBodyTracker.kt:104-107`). This is exactly "heading + mounting" and replaces the `gyroFix/mountingOrientation/attachmentFix/mountRotFix/yawFix` chain.

### 2b. Upper body (UPPER_CHEST/CHEST/WAIST/HIP) — `VC/steps/SolveUpperBodyTracker.kt`
**Uses no camera at all.** Residuals (`:26-54`): (i) forward-pose frames: full quaternion angle between `bone` and the forward reference (`:36`); (ii) bent-over frames: bone X axis must stay parallel to reference X (`:43`), and bone Y must be within 30° of the reference pitched forward 45° (`:47-49`, hinge loss). 64 seeded starts (4×4×4 over global yaw, local yaw, local roll `:109-122`), best by `calcError` then one LM (`:75-95`). So the "bend over" pose is purely to disambiguate torso mounting roll/pitch from IMU data — same idea as SlimeVR's mounting reset but from two poses.

### 2c. Legs and upper arms — `VC/steps/SolveNonUpperBodyTracker.kt`
- Bone ↔ keypoints map (`:33-40`): thigh = HIP→KNEE, shin = KNEE→ANKLE, upper arm = SHOULDER→ELBOW. Tracker +Y is assumed to point from the distal to the proximal joint (`:156`).
- **Residual** (`:212-248`): (i) forward-pose frames: angle between the *horizontal projection* of bone Z and the reference Z (`:225-227`; Z = backwards per `CaptureForwardPose.kt:17`) — constrains heading only; (ii) each matched video frame: `camera.project(bone.Y_world, midpoint2D, depth=1.0)` gives a 2D image vector; residual = **signed 2D angle** between that and the 2D keypoint bone direction (`:234-241`, `Camera.kt:20-25`, `Vector2D.kt:72`). Unprojectable → 1e6.
- **Data needs**: ≥120 frames after thinning to ≥5° tracker rotation change (`:42,167-187`), bone ≥40 px long (`:167`), and at least one pair of frames ≥60° apart in tracker rotation (`:189-201`, "enoughRotation") → GUI says "Walk around in a small circle". This is needed because 5 unknowns from a single view of a single pose are degenerate; rotation variety separates global yaw from local mounting.
- **Delay**: a second brute-force sweep, ±500 ms step 10 around the camera delay (`:78-126`) = 101 × (64 seeds + LM). The per-tracker delay is stored separately (`VideoCalibrator.kt:64,323`).
- **Poses asked for** (`translation.ftl`): "Move your right controller in a ∞ loop" (camera), "Stand straight and face forward" (`CaptureForwardPose.kt`: HEAD raw rotation level within 20° `:25,46`, stable ≤5° for ≥2 s and ≥30 snapshots `:23-26,53-67`; reference = head yaw only `:71-75`; keeps last 50 snapshots `:79`), "Carefully lean forward" (`CaptureBentOverPose.kt`: stable 1 s, torso trackers ≥30° from forward `:31,72-85`), "Walk around in a small circle". There is **no "wave"** step in this commit (arm trackers are solved by the walk step).

## 3. Integration hook — `tracking/trackers/TrackerResetsHandler.kt`

- Field `var trackerResetOverride: TrackerResetOverride? = null` (`:120`). In `adjustToReference()` (`:206-233`) the override **short-circuits the entire chain** (`:209-212`): `mountingOrientation`, `gyroFix`, `attachmentFix`, `mountRotFix`, `tposeDownFix`, `yawFix`, `constraintFix` are all skipped. It is a *replacement*, not additive.
- Applied through `Tracker.getRotation()`/`getAdjustedRotationForceStayAligned()` (`Tracker.kt:306,326`), i.e. **after** Stay Aligned's raw-space yaw correction (`Tracker.kt:300`) and **before** drift compensation (`:183`). `adjustToIdentity` (`:241-248`, used by `getIdentityAdjustedRotation` `Tracker.kt:348`) is *not* overridden → identity-space consumers diverge from bone-space output while an override is active.
- **Persistence**: in-memory only; not saved to config. Cleared by `resetFull` (`:270`) and `resetMounting` (`:412`). **Not cleared by `resetYaw`** (`:367-405`), which only updates `yawFix` — so a yaw reset becomes a silent no-op while an override is active (bug).
- The wizard sets it directly from a coroutine thread and then calls `postProcessResetFull(reference)` (made public, `:353`) to clear `needReset` and reset filtering (`VideoCalibrator.kt:261-262,320-321`). No Stay Aligned reset, no drift-compensation bookkeeping.
- **Could a background process call it repeatedly?** Mechanically yes — it is a plain `var` read on every rotation query; write `TrackerResetOverride(currentYaw + Δψ, local)` any time. But (a) you must first synthesise `local` equivalent to the user's existing mounting/attachment fixes or you throw them away; (b) every user reset wipes it; (c) yaw reset is broken meanwhile. For periodic heading correction the **better hook is the existing Stay Aligned slot**: `Tracker.kt:300` multiplies `rotationAroundYAxis(stayAligned.yawCorrection)` in raw space *before* the reset chain — exactly a per-tracker Δψ that composes with all resets. Nothing in this PR is needed for that.

## 4. Pose pipeline — `VC/sources/RtmposeOnnxPipeline.kt`, `HumanPoseSource.kt`

- **Model**: `rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.onnx` (54 MB, committed to the repo, loaded from next to the jar `HumanPoseSource.kt:39`). SimCC heads `simcc_x [1,K,384]`, `simcc_y [1,K,512]` (`:47,173-223`), argmax decode, score = min(xScore, yScore) (`:220`). K = 17 body keypoints; the `CocoWholeBodyKeypoint` enum has 133 entries but only the first 17 are ever produced (`:420`).
- **Detector**: YOLOX code exists but is **disabled** — the whole frame is the person box (`:69-73,96-100`). The frame is resized non-uniformly to 192×256 (`:154-157`, `resizeImage :445`) → aspect distortion; user must fill the frame.
- **Preprocessing**: RGB /255, no mean/std (`:463-481`). rtmlib applies ImageNet mean/std on the 0–255 image for this checkpoint; **verify** the export — if normalisation is not baked in, accuracy is degraded.
- **Runtime**: `com.microsoft.onnxruntime:onnxruntime:1.24.3` CPU artifact (`build.gradle.kts:+86`); `useCudaIfAvailable=false` by default and `addCUDA` would throw with the CPU jar (`:54,82-91`). ALL_OPT graph level (`:75`). Single `ReentrantLock` around inference (`:65,95`).
- **Confidence**: hard threshold 0.5 → `visible` (`:53,111`); `HumanPoseSource.kt:67-69` drops invisible joints entirely. No weighting downstream.
- **FPS**: no target; images come through a `CONFLATED` channel (`PhoneWebcamSource.kt:86`) so frames are dropped while inference runs. Hot path also **writes two JPEGs per frame to disk** (`PhoneWebcamSource.kt:333`, `HumanPoseSource.kt:76-81`) and re-encodes to I420 to broadcast an annotated preview over WebRTC (`:83-89`).

## 5. Data capture — `VC/snapshots/*`, `VC/sources/SnapshotsDatabase.kt`, `VC/util/DebugOutput.kt`

- **Trackers**: `TrackersSource` snapshots every server tick at 120 Hz (`VideoCalibrationService.kt:137`, `ScheduledInterval.kt`) with `rawTrackerToWorld`, `adjustedTrackerToWorld`, and position for HEAD/hands only (`TrackersSource.kt:91-101`; **errors if HMD/hands lack position** `:99`). Timestamp = `TimeSource.Monotonic.markNow()` on the server (`:83`).
- **Images**: `ImageSnapshot.instant` = **server monotonic time at WebRTC frame receipt** (`PhoneWebcamSource.kt:300,335`); the WebRTC capture timestamp is ignored. So camera latency (encode + network + decode) is unknown and is recovered by the brute-force delay sweeps (§1, §2c). No IR beacon, no phone clock.
- **Matching**: `SnapshotsDatabase.match` (`:56-87`) shifts pose instants by a delay and picks the nearest tracker snapshot within `maxJitter = 2/120 s` (`VideoCalibrationService.kt:63`).
- **What is recorded** (`DebugOutput`, dir `<config>/VideoCalibration…` `:575-578`, wiped on start `:66`): `camera.txt` (13 numbers `:89-114`), `1_webcam/webcam_<ms>.jpg` raw frames (`:116-120`), `2_poses/pose_<ms>.jpg` **annotated images only — keypoints are not serialised** (`:122-135`), `trackers.pfs` via existing PoseFrameFormat with raw+adjusted rotation and position (`:181-218`). The e2e test replays exactly this (`test/.../VideoCalibrationServiceTests.kt:107-186`): re-runs RTMPose on the JPEGs and replays the PFS at 120 Hz in real time.
- **Reusable for our offline experiments?** Partially: format is simple and the PFS reader exists. But single camera, JPEG, receipt-time stamps, hard-coded Windows paths in the test (`:47,54`), no keypoint dump. Our own recorder (2×RTSP + PFS/quaternion log + beacon timestamps) is a small job and we would design the timestamps properly.

## 6. Skeleton offsets solver — `VC/steps/SkeletonOffsetsSolver.kt` + `tracking/processor/skeleton/refactor/*`

- Fits **6 lengths** (torso split 25/25/25/25 into upper-chest/chest/waist/hip, hips width, upper leg, lower leg, neck, head; `:110-117,175-192`) by LM on the **pixel reprojection error** of FK joint positions (shoulders, shoulder-midpoint, hips, knees, ankles; `:85-101,194-208`) against 2D keypoints over every 5th frame of the whole session (`:61,211-212`), using the already-solved `TrackerResetOverride`s (`:40-59`). Post-hoc fudge: half the neck moved into upper chest, +8 cm ankle-to-heel (`:139-154`).
- Requires the 879-line **`refactor/Skeleton.kt` + `SkeletonUpdater.kt`**: a stateless re-implementation of `HumanSkeleton` FK that takes a snapshot map instead of live trackers. Useful *as a pattern* (batch FK over recorded quaternions is exactly what our benchmark harness needs) but it duplicates upstream logic and will rot.
- **Relevance to us**: low-medium. Monocular, needs a solved camera, and bone lengths are not our problem. The reprojection-residual structure is the piece worth remembering if we ever refine calibration with accumulated reset poses (D15).

## 7. Reusability verdict

**Cleanly reusable (small, self-contained, correct or trivially fixable)**
- `VC/data/Camera.kt`, `CameraExtrinsic.kt`, `CameraIntrinsic.kt` (pinhole model, tested in `CameraTests.kt`) — add distortion.
- `VC/util/NumericalJacobian.kt`, the LM boilerplate pattern (commons-math3 is already a server dependency).
- `VC/util/ScheduledInterval.kt`, `TrackersSource.kt` + `DebugOutput.saveTrackerSnapshots` (120 Hz raw-quaternion recorder to PFS).
- `SnapshotsDatabase.match` nearest-neighbour association with a delay parameter.
- `ktmath` additions: `QuaternionD`, `Vector3D`, `Vector2D`, `Matrix3D`, `EulerAnglesD`, `Quaternion.toDouble()` — double-precision math is genuinely useful for solvers.
- `RtmposeOnnxPipeline.kt` SimCC decode (`:173-223`) if we want in-server inference later (fix crop/normalisation first).
- `CaptureForwardPose.kt` stillness/level gate logic as a template for our "still moment" gate.

**Tightly coupled to the wizard / phone flow**
- `VideoCalibrationService.kt`, `VideoCalibrator.kt` (state machine + flatbuffer progress messages), `RPCHandler.kt` additions, `PhoneWebcamSource.kt`, `WebRTCManager.kt`, `MDNSRegistry.kt` (`_slimevr-camera._tcp`), the whole GUI page, the solarxr-protocol submodule bump, Windows-only `webrtc-java` native classifier (`build.gradle.kts:+88`).
- `SolveCamera.kt` (controller-only, single cam, grid-searched delay), `SolveUpperBodyTracker.kt` (IMU-only two-pose mounting), `SolveNonUpperBodyTracker.kt` (needs walking, 5 unknowns, monocular).

**What would have to change for periodic 2-camera still-moment correction**
1. Replace the 5-param fit with a **1-param yaw fit per tracker** (mounting known from the last user reset): residual = heading of triangulated bone direction vs FK bone heading. The camera-frame part of `SolveNonUpperBodyTracker` becomes unnecessary; a 2-view triangulation is not present anywhere in the PR.
2. Extrinsics from the HMD trajectory (and both hands), not one controller; add cam–cam solve; solve from a single accumulated dataset, not per session.
3. Real timestamps at capture (RTSP PTS + beacon, D17) instead of ±500 ms brute force.
4. Apply Δψ through `stayAligned.yawCorrection`-style raw-space yaw (`Tracker.kt:300`) or a new additive field, **not** `trackerResetOverride`.
5. Keypoint logging, confidence weighting, detector/letterboxing, GPU EP, and removal of per-frame disk I/O.

**Bugs / math concerns found**
- `Vector2D.angleTo` (`ktmath/Vector2D.kt:72`) is `atan2(b) − atan2(a)` **without wrapping** → residuals jump by ±2π for nearly-aligned vectors; LM will see spurious huge errors. Must wrap to (−π, π].
- `Camera.project(vector, origin, depth=1.0)` (`Camera.kt:20-25`) projects a **1 m long vector placed at 1 m depth**; under perspective the 2D direction of a finite segment depends on depth, and a bone pointing toward the camera puts the tip at z ≤ 0.1 → `null` → residual 1e6 (`SolveNonUpperBodyTracker.kt:242-244`). Should use the differential projection or a tiny vector at the true depth.
- Quaternion parametrised by 4 free floats then normalised (`:282`) → 1-D gauge freedom, rank-deficient Jacobian (LM damping hides it).
- `resetYaw` does not clear `trackerResetOverride` (see §3); identity-adjusted path ignores it.
- `SolveNonUpperBodyTracker.kt:83-85` `return null` inside the delay sweep aborts the whole tracker if any single shifted delay has <120 matches (should `continue`).
- `close()` returns early if `yoloSession` is null, so the pose session is never closed (`RtmposeOnnxPipeline.kt:510-521`).
- Whole-frame non-letterboxed crop + probable missing mean/std normalisation (§4).
- Yaw convention: `rotationAroundYAxis` is a right-handed rotation about +Y (`QuaternionD.kt:75`); `placeCamera` negates the yaw with a hand-wavy "RHS" comment (`SolveCamera.kt:175`) — it is only an initial guess, so harmless, but signals the convention was found empirically. `globalYaw` is radians throughout; degrees appear only in logging (`KTMathExtensions.kt`).
- Hard-coded `C:\Users\yilan\...` paths in tests (`VideoCalibrationServiceTests.kt:47,54`), `println` instead of `LogManager` in the pipeline, and the PR touches `TrackersUDPServer` (`trafficClass = 0x10`) and the build deps unrelated to the feature.

## Recommendation (Q15)

**Do not fork the branch.** Its architecture (one-shot wizard, phone/WebRTC, 5-unknown monocular fit, override-replaces-reset) is orthogonal to periodic 2-camera Δψ correction, and the parts we would keep are <10% of the diff. **Borrow**: `Camera*` pinhole classes, `NumericalJacobian`/LM pattern, `TrackersSource` 120 Hz PFS recorder, `SnapshotsDatabase.match`, ktmath double types, the SimCC decoder, and the forward-pose stillness gate. **Reference**: the observation that torso mounting is solvable from two IMU-only poses; the reprojection-residual structure; the finding that the correct in-server hook for a heading delta is the Stay Aligned raw-space yaw slot, not `TrackerResetOverride`. Worth pinging jabberrock on Discord: the branch stalled at proof-of-concept with several solver bugs, and a per-tracker "external yaw correction" API in `Tracker`/SolarXR would serve both efforts.
