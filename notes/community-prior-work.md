# Community prior work: camera-assisted IMU drift correction in SlimeVR / VR FBT

Date: 2026-08-26. Research by Claude (web search, GitHub API, local `../SlimeVR-Server` checkout).
Scratch note; may be wrong. Anything not marked "verified" was read only via a summary.

## Headline

**Yes, someone has done it, and it is the Stay Aligned author.** `jabberrock` opened
[SlimeVR-Server PR #1805 "Video calibration PROOF OF CONCEPT ONLY"](https://github.com/SlimeVR/SlimeVR-Server/pull/1805)
(2026-04-08, still open/draft as of 2026-07-13). It streams an Android phone camera into
the server over WebRTC, runs RTMPose (ONNX, COCO-WholeBody keypoints) inside the server,
solves camera extrinsics, then solves *per-tracker* a `TrackerResetOverride(globalYaw, localRotation)`
(i.e. camera-derived yaw reset + mounting reset) by Levenberg-Marquardt, and finally solves
skeleton bone offsets. It replaces `adjustToReference()` in `TrackerResetsHandler.kt` when
an override exists. This is a **one-shot calibration wizard**, not continuous or periodic
correction — but it is the closest existing thing to our thesis and shares the codebase we
would integrate into. Read its code before designing ours (details below).

Nothing else found implements "camera corrects IMU yaw". Everything else is either
(a) camera-*only* FBT, (b) IMU-only drift mitigation, or (c) a feature request that was closed.

## Table of relevant projects / threads

| # | Name | Link | What it does | Status / maturity | Relation to our goal |
|---|---|---|---|---|---|
| 1 | **SlimeVR-Server PR #1805 "Video calibration"** (jabberrock) | https://github.com/SlimeVR/SlimeVR-Server/pull/1805 | Phone camera -> WebRTC -> RTMPose in server -> solves camera pose, per-tracker yaw+mounting override, skeleton offsets. Files: `tracking/videocalibration/{steps/SolveCamera,SolveUpperBodyTracker,SolveNonUpperBodyTracker,SkeletonOffsetsSolver,VideoCalibrator}.kt`, `data/TrackerResetOverride.kt`. Also GUI page + SolarXR RPC additions. | Open draft PR, "PROOF OF CONCEPT ONLY", ~8k lines, binaries on Google Drive, 2 comments. Camera app repo `jabberrock/SlimeVR-Camera-Android` exists (pushed 2026-04-08) but README 404 (private or empty). | **Directly overlapping.** Same problem (yaw + mounting from camera), same server, but one-shot wizard with user-guided poses (forward, bent-over) rather than passive periodic correction. Its `SolveNonUpperBodyTracker` cost = angle between camera-projected tracker Y-axis and 2D keypoint bone direction, over frames with >=60 deg of rotation variety. Camera solve uses HMD/controller poses vs keypoints (upper body is 6DoF-known). Strong candidate to build on or borrow (camera solve, tracker-to-camera delay search of +/-500 ms, snapshot DB). (verified: read source) |
| 2 | **SolarXR-Protocol PR #204** (jabberrock) | https://github.com/SlimeVR/SolarXR-Protocol/pull/204 | Adds RPCs `ConnectToWebRTCRequest/Response`, `StartVideoTrackerCalibrationRequest`, `CancelVideoTrackerCalibrationRequest`, `VideoTrackerCalibrationProgressResponse`, `VideoTrackerCalibrationCamera`. | Open WIP. | Shows the protocol path jabberrock chose (RPC-driven wizard, video via WebRTC into the server). (verified: diff) |
| 3 | **SlimeVR-Server issue #1455** "Older IMU rotation and position self calibrate with camera?" | https://github.com/SlimeVR/SlimeVR-Server/issues/1455 | User asks for a HMD-mounted or static camera used *only for calibration/drift realignment*, not FBT. | Closed (completed), 2025-06. **Eirenliel (lead): "It was actually something that we wanted to try in the future when we have more space on our roadmap or more resources. Or if someone makes that..."** | Maintainer is receptive to exactly our idea. #1805 is presumably "someone making that". (verified: API) |
| 4 | **SlimeVR-Tracker-ESP issue #347** "webcam based optical tracking and calibration (2 to 4 webcams)" | https://github.com/SlimeVR/SlimeVR-Tracker-ESP/issues/347 | Proposes RGB LED on each tracker + webcams for optical tracking to eliminate drift. | Closed "not planned"; Eirenliel: "Out of scope." Long argument pointing to PSMoveServiceEx. | Marker-based (LED) variant. Rejected because it needs hardware changes. Our approach (markerless, body pose) avoids that objection. (verified: API) |
| 5 | **PSMoveServiceEx** (Timocop) + `PSMoveServiceEx-SlimeVR-Tracker-ESP` | https://github.com/Timocop/PSMoveServiceEx , https://github.com/Timocop/PSMoveServiceEx-SlimeVR-Tracker-ESP | PS Eye / webcam colour-bulb optical *position* tracking; SlimeVR/owoTrack IMUs supply orientation. Requires SlimeVR Server for pose. | Active-ish, niche. Discussion #19: "You can't fix orientation yaw drift without magnetometers... optical shapes would track terribly with RGB cameras." | Hybrid IMU+optical exists here, but optical gives *position* of a bulb, not heading; yaw drift explicitly unsolved. Not read in depth. |
| 6 | **SlimeVR "Constellation Tracking"** (official, hardware) | https://www.crowdsupply.com/slimevr/slimevr-full-body-tracker (updates "Epic New Things", 2025-08-18) | IR LEDs on trackers + camera base stations + IMU; SlimeVR's own answer to drift. SLAM (inside-out) explored and near-abandoned. | "First prototypes in production" (Aug 2025). Closed hardware path; no public code found. | Confirms SlimeVR itself sees optical+IMU as the fix, but via new hardware. Our software-only approach is complementary for existing trackers. (crowdsupply page 403'd on fetch; from search snippets only) |
| 7 | **ju1ce/April-Tag-VR-FullBody-Tracker** (ApriltagTrackers) | https://github.com/ju1ce/April-Tag-VR-FullBody-Tracker | Camera-only FBT with printed AprilTag cubes; outputs SteamVR trackers; forks add OSC (orsnaro/April-Tag-VR-noSteam). | Mature, popular, camera-only. | Not fused with IMUs. Useful reference for camera calibration UX (single camera + known marker gives absolute pose cheaply — a possible "known yaw reference" for our camera extrinsics). |
| 8 | **ju1ce/Mediapipe-VR-Fullbody-Tracking** | https://github.com/ju1ce/Mediapipe-VR-Fullbody-Tracking | Single-camera MediaPipe pose -> 3 SteamVR trackers or VRChat OSC trackers. Manual yaw slider to align. | WIP, 589 stars, 62 open issues. README says "works less accurately, needs far more room" than AprilTag. No SlimeVR/IMU mention. | Camera-only; the MediaPipe-to-VR plumbing is prior art but the depth ambiguity it suffers from is why we want cameras only for *heading*, not position. |
| 9 | **Driver4VR** | https://www.driver4vr.com/ , https://steamdb.info/patchnotes/10112944/ | Commercial; webcam/phone AI body tracking, Kinect, PS Move; emulates Vive trackers. | Commercial, closed. No evidence of IMU-drift correction. | Camera-only alternative; not a fusion. |
| 10 | **HybridTrak** (Yang et al., CHI 2022) | https://hci.stanford.edu/publications/2022/CHI2022_HybridTrak.pdf | Fuses inside-out HMD+controller 6DoF with single webcam 2D pose via neural net -> 3D full body. | Academic; no public code found. | Closest academic "camera + VR tracking" fusion, but fuses with the HMD (drift-free), not with IMU trackers. Candidate literature note, unverified beyond abstract. |
| 11 | **FusePose** (arXiv 2208.11960) | https://arxiv.org/pdf/2208.11960 | Multi-view images + IMU bone vectors; explicitly models IMU drift and decides when to replace bone vectors. | Academic. | Relevant literature for the fusion rule; unverified (abstract only). Belongs in `docs/02-research-agenda.md`. |
| 12 | **Pico Motion Tracker** (commercial) | https://skarredghost.com/2024/09/11/pico-motion-tracker-impressions/ | IMU + 12 IR LEDs seen by headset cameras; optical used for calibration and to correct cumulative IMU error when in view. | Shipping product. | Proof the "optical only corrects IMU error" model works commercially; hardware-bound. Issue #1455 was likely inspired by it. |
| 13 | **SlimeVR-Server issue #951** "Drift compensation should take minutes instead of resets" | https://github.com/SlimeVR/SlimeVR-Server/issues/951 | Feature request re: existing linear drift-compensation. | Closed, no body. | Shows dissatisfaction with time-linear compensation. |
| 14 | **Stay Aligned** (jabberrock, server v0.16.0, 2025-07-01) | https://github.com/SlimeVR/SlimeVR-Server/releases/tag/v0.16.0 , https://vyrovr.com/2025/07/01/slimevr-server-update-introduces-stay-aligned/ | Slowly nudges yaw toward relaxed-pose priors (standing/sitting/lying). Follow-ups: #1468, #1669, #1530, #1673. | Shipped; default recommendation for drift. | Prior-based, not measurement-based. Our camera measurement could feed the same "slow yaw correction" plumbing (`stayaligned/`). |
| 15 | **SlimeVR-Feeder-App** | https://github.com/SlimeVR/SlimeVR-Feeder-App | OpenVR app that sends HMD/controller/Vive-tracker poses to the server (protobuf). | WIP but shipped with installer. | This is how the server gets its drift-free HMD pose — the reference our camera must be registered to. |
| 16 | **moslime/moslime** | https://github.com/moslime/moslime | Sony Mocopi -> SlimeVR bridge. README: sending IMU accel to SlimeVR "doesn't help with drift". | Active. | Not camera; irrelevant beyond confirming drift is the shared pain. |

Not found (searched, nothing relevant): Reddit threads on r/SlimeVR combining webcam
and trackers (Reddit is not indexed well by the search tool and could not be fetched
directly); any SlimeVR fork with MediaPipe/webcam yaw correction other than #1805; any
Warudo/XR Animator feature that uses a camera to correct IMU tracker yaw (Warudo can
run camera pose as a *secondary* source, but that is pose blending, not drift correction).

Could not access: SlimeVR Discord (#dev-forum / #beta-testing-forum, where #1805 was
presumably discussed); jabberrock's Google Drive binaries; the camera app README;
crowdsupply update pages (HTTP 403); `docs.slimevr.dev/server/stay-aligned.html` and a
VMC doc page (404 — those pages do not exist in the docs repo; docs cover OSC, reset
bindings, SteamVR mixing only).

## How SlimeVR accepts external tracking data

Verified against the local checkout `../SlimeVR-Server` (`server/core/src/main/java/dev/slimevr/`)
and the vendored `solarxr-protocol/schema/`.

| Path | Direction | What it carries | Where | Notes |
|---|---|---|---|---|
| **SlimeVR UDP tracker protocol** | tracker -> server | quaternion (+ accel, flags) per sensor | `tracking/trackers/udp/TrackersUDPServer.kt` | Native tracker input; owoTrack, moslime, SlimeTora, slimevr-wrangler all emulate it. Orientation only. |
| **VRChat OSC receiver** | app -> server | `/tracking/vrsystem/{head,leftwrist,rightwrist}/pose`, `/tracking/trackers/*/position` and `/rotation` | `osc/VRCOSCHandler.kt` (lines ~43-50, 411-498) | Creates `Tracker(hasPosition=true, hasRotation=true)` and `server.registerTracker()`. Applies a yaw offset slerp so received trackers align with HMD. Docs: https://docs.slimevr.dev/server/osc-information.html |
| **VMC receiver** | app -> server | `/VMC/Ext/Bone/Pos`, `/VMC/Ext/{Hmd,Con,Tra}/Pos`, `/VMC/Ext/Root/Pos` | `osc/VMCHandler.kt` (lines ~77-81, 196-298) | Maps VMC bones to `TrackerPosition`; creates trackers with device origin `VMC`. Has "set the Quaternion to shift received VMC yaw". No public docs page. |
| **WebSocket VR bridge** | browser/app <-> server | `config` + `pos_changed` style JSON; HMD and computed trackers with position | `websocketapi/WebSocketVRBridge.kt` | Legacy JSON bridge (used by the web/Quest client). Creates `hasPosition=true` trackers. |
| **Feeder App / SteamVR driver bridge** | SteamVR -> server | HMD, controllers, Vive/Tundra trackers (position + rotation), protobuf over named pipe | `bridge/`, `steamvr/`, https://github.com/SlimeVR/SlimeVR-Feeder-App | Vive tracker *positions* are currently ignored by the skeleton ("treated as Slime trackers"; https://docs.slimevr.dev/tools/steamvr-trackers-mixing.html). |
| **SolarXR (FlatBuffers over WebSocket, port 21110)** | GUI/apps <-> server | `data_feed/*` is server -> client only (`TrackerData` has rotation, position, `rotation_reference_adjusted`, `rotation_identity_adjusted`); `rpc.fbs` has `ResetRequest{reset_type: Yaw/Full/Mounting}`, `DriftCompensationSettings`, `ResetsSettings`, `ResetStayAlignedRelaxedPoseRequest`, and (in PR #204) the video-calibration RPCs. | `solarxr-protocol/schema/`, `protocol/rpc/RPCHandler.kt`; https://github.com/SlimeVR/SolarXR-Protocol | **There is no SolarXR message to push a tracker pose or a yaw correction into the server.** From outside, one can only (a) read raw tracker rotations, (b) trigger a reset, (c) change settings. Node bindings: https://github.com/SlimeVR/slimevr-node |
| **OSC / VMC / SteamVR outputs** | server -> apps | computed skeleton | `osc/*`, driver | For reading the *result* of a correction, not for injecting one. |

Consequences for us:

1. An **external** process (Python, GPU) can subscribe to SolarXR `data_feed` for every
   IMU tracker's raw rotation + the HMD pose at ~100 Hz, so offline/asynchronous
   camera-vs-IMU comparison needs no server changes. This is the cheapest experiment path.
2. Applying a correction from outside is limited to `ResetRequest`, which uses the HMD's
   yaw and assumed pose — it cannot take a measured per-tracker yaw. So a real correction
   needs a server-side hook. PR #1805's `TrackerResetsHandler.trackerResetOverride`
   (a per-tracker `(globalYaw, localRotation)` that bypasses `adjustToReference`) is
   exactly such a hook, and a per-tracker "set yaw offset" RPC would be a small addition.
   Alternatively, feed the correction into `stayaligned/` as a measured target instead of a
   pose prior.
3. Injecting fake positional trackers via OSC/VMC is possible but pointless for yaw:
   the skeleton ignores or only weakly uses external positions (CCD `IKSolver.kt`).

## Gaps (what nobody has done)

- **Continuous / periodic, unattended camera correction of IMU yaw.** #1805 is a guided
  wizard (forward pose, bent-over pose, wave limbs through >=60 deg) that runs once. No one
  re-solves yaw every few minutes during "still moments" without user action.
- **Using the HMD as the camera-to-world anchor for ongoing tracking**, plus quantifying
  camera heading accuracy per limb (which limbs/poses give a usable yaw observation).
  #1805 does solve the camera from HMD/controllers, but there is no published accuracy.
- **Any evaluation data**: no dataset or numbers on how much camera correction reduces
  end-effector error vs. Stay Aligned or resets. `../drift-lab/` baselines plus a
  camera ground truth would be new.
- **Two-camera / multi-view triangulation for heading** — every hobby project is
  single-camera 2D (or single camera + markers).
- **Detecting strap slip / mounting change mid-session** from camera evidence.
- **Correction fusion policy** (when to trust the camera, how to blend, how to handle
  occlusion) as a measurement-driven replacement for Stay Aligned's priors. FusePose-style
  threshold rules exist in academia, nothing in the SlimeVR ecosystem.
- Maintainer stance is favourable (Eirenliel in #1455) as long as no tracker hardware
  change is required (#347 rejection).

## Suggested next actions (for STATE.md, David to confirm)

- Pull `jabberrock/SlimeVR-Server` branch `jabber-video-calibration-4` into a worktree and
  read `SolveCamera.kt`, `SolveNonUpperBodyTracker.kt`, `SnapshotsDatabase.kt`. Decide:
  build on it, or borrow only the camera solve + reset override.
- Ask jabberrock (Discord #dev-forum) about accuracy findings and whether periodic
  re-solve was considered.
- Write literature notes for HybridTrak and FusePose only after actually reading them.

## Local verification (2026-08-26)

PR #1805 fetched into `../SlimeVR-Server` as branch `pr-1805`: single commit
`487e2419` "Video calibration" (2026-03-16, Jabberrock), 70 files, +8551/−78.
Server-side package `dev.slimevr.tracking.videocalibration/` with
`VideoCalibrator.kt`, `steps/SolveCamera.kt`, `SolveUpperBodyTracker.kt`,
`SolveNonUpperBodyTracker.kt`, `SkeletonOffsetsSolver.kt`, `data/TrackerResetOverride.kt`,
`sources/RtmposeOnnxPipeline.kt` (bundles a 54 MB RTMPose body7 256×192 ONNX),
`networking/{WebRTCManager,MDNSRegistry}.kt` for a phone camera, plus a
double-precision ktmath (`QuaternionD`, `Matrix3D`) and a 1k-line GUI page.
