# STATE — read first

_Last updated: 2026-09-01. Conventions: `CLAUDE.md`. Full narrative: `docs/05-report-2026-08-26.md` + shareable page (see Reports)._

## Status — one paragraph

The product shape is settled (D33): an **automatic full reset in familiar poses** — the camera learns what the user's reset pose and idle stances look like while the IMU is trusted (right after a manual reset), and later re-performs the equivalent of a full reset whenever such a pose recurs. **The main line is now single-camera (D36).** Exp 09 (MotionBERT monocular lifting on MoVi, per view) says: **frontal standing familiar poses stay inside the 5° budget with one camera** (1.6–5.3° calibrated on simple standing idles, vs exp 07's 2-cam 3.5–4.7° pooled); **seated poses and side-on views currently fail** (shin depth-flips ~130°; the side view can't even match templates — descriptor normalizer collapses). Part of the seated failure is a protocol artifact MoVi can't fix (no genuinely recurring poses) → the real seated test is exp 08's own-room recording, now one camera. Leading mitigations: IMU-prior flip disambiguation (drift ±few° vs 180° flips), torso-scaled descriptor, view-quality gating. Retroreflective markers parked (D35); 2-cam triangulation parked (D36).

## What is established (with where it's proven)

- Drift is motion-driven and unpredictable per unit; no offline model (D24–D26; drift-lab FINDINGS).
- Off-the-shelf 2D detectors have a structural, pose/view-dependent heading error (5–13° after averaging) unchanged by model size, resolution, or dataset (exps 04, 06; MoVi + TotalCapture). Within one pose it is ~2° repeatable → learnable (exp 05, D32).
- Bone reliability: feet ≈ chest > shins > hip > thighs (D30). Vertical bones need lateral features; compare the same physical axis on camera and IMU sides (exp 01).
- Calibration is not the bottleneck (~0.5–2° from people; HMD fixes scale) (§D synthesis, D15).
- Licences: NC datasets (MoVi, TotalCapture, AMASS/SMPL-X/BEDLAM) are evaluation-only; training data = own recordings + community donations + permissive mocap (D34).
- Single camera (exp 09, MotionBERT lifting): frontal standing poses ≈ 2-cam quality (1.6–5.3° cal); near-horizontal bones depth-flip ~180°; side-on view fails at the pose gate itself; the lifted pose exposes view quality (image-plane fraction of the lateral axis) as a usable confidence signal. Monocular 3D degrades gate and measurement *together*.

## Decisions

| # | Date | Decision | Why |
|---|---|---|---|
| D1 | 2026-08-26 | Offline/occasional correction, not real-time fusion | User can tolerate minutes between corrections; lets us wait for high-confidence windows and use heavier models. |
| D2 | 2026-08-26 | Target: 1–2 cheap cameras, near-zero user calibration | Consumer constraint set by David. |
| D3 | 2026-08-26 | Ground in literature before building | Novel enough that memory/web-search alone are unreliable. |
| D4 | 2026-08-26 | Compute: RTX 3090 24 GB (CUDA) locally for model work; rent cloud GPUs if training needs more | David also has an RX 9060 XT 16 GB (ROCm); CUDA-only research code is not a blocker. |
| D5 | 2026-08-26 | Python 3.12 + uv projects for all code | Best library support (David); reproducible envs. |
| D6 | 2026-08-26 | Yaw-only correction is the target; moderate accuracy first (~5° heading proposed) | David: yaw dominates. |
| D7 | 2026-08-26 | Target setup: SteamVR PC + Quest 3 + 2 cheap surveillance cameras; 11 BNO085 trackers | HMD 6-DoF pose is available as a visible anchor for camera extrinsics. |
| D8 | 2026-08-26 | User doing (multiple) full resets in camera view is acceptable setup | Simple user input OK; complex calibration not. |
| D9 | 2026-08-26 | Skip drift baseline as a prerequisite | Must be robust to unknown per-environment drift anyway. |
| D10 | 2026-08-26 | Open-access literature only | No institutional access. |
| D11 | 2026-08-26 | Accuracy target v1: limb heading within 5° | David confirmed. |
| D12 | 2026-08-26 | Cameras are cheap RTSP IP cameras | Implies software clock sync, latency handling. |
| D14 | 2026-08-26 | Drift model = one rotation about world-up per tracker, piecewise-constant between corrections (VIP 2018 parameterisation) | Validated by VIP ablation: recovering per-sensor heading gives most of the fusion gain. |
| D15 | 2026-08-26 | Calibration v1: intrinsics per camera model once; floor from people + IMU gravity; scale/yaw/position from HMD trajectory; cam–cam from keypoints over time; refine with accumulated reset poses | Literature: people-only extrinsics ≈0.5–2° rotation but weak translation/scale; HMD fixes scale. Single reset pose is degenerate. |
| D16 | 2026-08-26 | Camera side estimates 3D *joint positions* (2-cam triangulation of 2D keypoints; SMPL regressors only as fallback); heading derived geometrically; twist stays IMU-only | Published SMPL rotation error is 22–25° MPJAE; twist unreliable. Heading from triangulated joints ≈ keypoint error / bone length. |
| D17 | 2026-08-26 | Clock sync v1: ESP32-driven coded blinking LED (IR or visible) in camera view, reporting blink times to the server; doubles as a fixed fiducial | David's idea; sync-from-motion fails during still windows. See `notes/ir-beacon-idea.md`. |
| D18 | 2026-08-26 | First benchmark = TotalCapture with synthetic gyro-only yaw drift injected, 2 of its 8 cameras as our pair, Vicon as heading truth | Only dataset with raw IMU + multi static cams + optical GT; avoids hardware until the method is validated. |
| D19 | 2026-08-26 | Accuracy target v1 is per-bone: 5° long bones (thigh/shin/torso/upper arm), ~8–10° feet/forearms; feet deprioritised | David: feet are the least concern. |
| D20 | 2026-08-26 | PR #1805 is reference only; we build clean | David; no relationship with the author. Borrow specific math/hook ideas per `notes/pr-1805-analysis.md`. |
| D21 | 2026-08-26 | Requiring a specific camera model (or a hacked one) for forced night mode / IR is acceptable | David. Keeps IR-beacon and controller-LED options open. |
| D22 | 2026-08-26 | Integration slot = the existing Stay Aligned raw-space yaw correction in `Tracker.kt:300`, not PR #1805's `TrackerResetOverride` (which replaces the whole reset chain and is cleared inconsistently) | `notes/pr-1805-analysis.md` §3/§7. |
| D23 | 2026-08-26 | TotalCapture: primary use is offline method development/evaluation. Fine-tuning a model on it and releasing weights openly (non-commercial) is a realistic future use; the access request asks the licensor explicitly whether that is within the terms. If they say no, restrict to evaluation only and fine-tune on community-donated/synthetic data. **Pending licensor's answer.** (Revised 2026-08-26; was "never train anything shipped".) | Licence text (research-only, no commercial use, no redistribution) does not address derived model weights; David's view is that open non-commercial fine-tuning is a legitimate research use, so ask rather than pre-emptively forbid. Signature requirement: David has no institution → may be refused. |
| D24 | 2026-08-26 | Drift model refined: per-tracker yaw error ≈ k_i × yaw rotation travelled (k ≈ ±0.45 %), ~zero at rest; thermal tilt up to ~5° is a separate pitch/roll error | drift-lab/FINDINGS.md turntable + run A. Supersedes the bias assumption in D14's random-walk picture; VIP-style piecewise-constant correction still applies. |
| D25 | 2026-08-26 (rev.) | Drift model = unpredictable random walk driven by *gross* 3D motion (σ_m, unmeasured) + minor yaw-scale term. Correction trigger = demand-driven on gross motion since last correction. Scale-learning dropped (fits noise). | David: drift appears with modest movement, no turning; predictable error would be calibrated away. Exp 02 revision: residual ∝ σ_m·√(gross motion); cadence requirement hinges on σ_m. |
| D26 (rev.) | 2026-08-26 | **No offline drift model.** Tracker error is unknown per unit. Two complementary truths: the **IMU body model is trusted for a short window after a full reset in a known pose**; the **camera is drift-free but biased**. The post-reset window calibrates the camera (extrinsics *and* the detector's pose/view-dependent bias, per user/room); the bias-corrected camera then corrects the IMU until the next reset. Periodic user resets bound the horizon (minimise error over ~10–30 min, not forever). Exp 03 becomes optional (harness calibration for David's units). | David: variability across tracker sets makes extrapolation from a few datapoints impossible. |
| D27 | 2026-08-26 | **Research effort goes to the camera side:** pose-estimation robustness in diverse real conditions (rooms, lighting, cheap RTSP cameras, headset+controllers, clothing, occlusion). AI training is expected to pay off there, not in IMU modelling. IMU-side experiments stop after exp 02. | David. Self-supervised signal: IMU is trustworthy for a while after a reset → pseudo-labels for limb heading in the wild. |
| D28 | 2026-08-26 | Core bet: fine-tune a pose estimator for VR full-body-tracking conditions (fixed room, 1–2 fixed cheap cameras, headset+controllers, constrained/dance-like motion). Side benefit: cheap mocap for games/film. Plan: BEDLAM-style synthetic pipeline starts now; TotalCapture (or equivalent marker-GT multi-view set) for detector-bias measurement when access arrives. | David. |
| D29 | 2026-08-26 | Experiment 04 (detector heading bias) starts on **MoVi** (open download, 2 calibrated synced cams, Qualisys marker GT); TotalCapture/Fit3D later | Only marker-GT multi-view set with zero access friction; 2 views matches deployment. No public set has headset wearers → synthetic for that. |
| D30 | 2026-08-26 | Bone reliability order for heading (real detector): feet ≈ chest > shins > hip > thighs; upper arms unmeasurable on MoVi. Weight corrections accordingly; D19's 'feet are the hard case' is reversed. | Exp 04 on MoVi, 5 subjects, two detector sizes. |
| D31 | 2026-08-26 | Correction target is a **full 3-DoF per-tracker offset** (yaw + tilt + mounting), not yaw only. Camera supplies tilt from bone direction (well observed for long/vertical bones) and yaw from lateral features; IMU pitch/roll drift thermally (0.8–5.7°/h, drift-lab) and straps slip. | David: yaw-only resets leave visible drift in other directions. |
| D32 | 2026-08-26 | Detector bias is a repeatable function of pose+view (within-pose sd ~2°). Correction model = pose-conditioned, learned globally (fine-tuning) and refined per session in the post-reset window; prefer correcting in poses seen during that window. | Exp 05 on MoVi. Marries David's 'IMU is short-term truth' with the exp 04 finding. |
| D33 | 2026-08-26 | **Product scope: automatic full reset in familiar poses.** Correct only when the user is in a pose the trusted window already saw — the reset pose itself or habitual idle stances. After heavy activity (dance routine) the user does a manual full reset; we don't try to correct arbitrary motion. Goal = extend the manual-reset horizon from minutes to a session under everyday movement. The user is an active participant: the system may prompt for a reset or ask for the reset pose when confidence is low. | David. Exp 05: within-pose residual ~2°. **Seated relaxed idle is a primary target pose** (David: having to stand up straight, arms down, for every reset is one of the most annoying parts of SlimeVR; users are often seated). Also simplifies observability: in the reset stance the camera only needs pelvis/chest/feet headings + bone directions (all well-observed); thighs/shins follow the same pose assumption the manual full reset already makes. |
| D34 | 2026-08-27 | **Treat the shipped model as commercial-adjacent** (open source, not sold, but used with hardware SlimeVR sells). Training data must be licence-clean: own recordings, community donations under our terms, permissive source mocap (CMU, ACCAD; DanceDB/HDM05 CC BY-SA) on a non-SMPL body if rendered. NC datasets (MoVi, TotalCapture, Fit3D, AMASS/SMPL-X/BEDLAM) are for evaluation and prototyping only. Ask MPI for written permission in parallel. | Q19 answered by David; MPI licence text is purpose-based and overrides the code licence; WHAM/4D-Humans precedent is untested. Not legal advice. |
| D35 | 2026-08-31 | Retroreflective markers **parked** (not dropped): main line is markerless (D33 familiar-pose automatic reset). All marker tooling stays ready — camera presets, blob/bar/ring estimators, test protocol in `notes/retroreflective-tape-idea.md`. | David: 'leave this ready for next time, but back to no reflective tape'. |
| D13 | 2026-08-26 | Community data: opt-in raw video is acceptable (HMD anonymizes), derived-only as fallback tier | David. |
| D36 | 2026-09-01 | **Main line is single-camera.** Evaluate how far one camera gets (exp 09: single-view rerun of exp 07 on MoVi, monocular 3D from cached 2D keypoints through the same familiar-pose pipeline, per view). Two-camera refinement stays a later option; triangulation code kept. Simplifies exp 08 (one camera, no cam–cam extrinsics/sync). | David: any camera the user has laying around is a much more reasonable ask than two; refine with two later if necessary. |

## Open questions

- Q21 OpenIPC on the cameras (HiChip/Hipcam; SoC marking or UART banner needed; prefer Ethernet). Parked until David opens a case.
- Q14 Do the cameras see the Quest Touch Plus IR LEDs in night mode? (free fiducials; untested)
- Template-matching threshold tuning (exp 07: ~¼ of segments never re-matched).
- Exp 03 (on-body drift, optional); Fit3D account (backup dataset).

## Next actions

1. **Done (exp 09) → follow-ups to pick from, with David:** (a) IMU-prior depth-flip disambiguation in `familiar.py` (simulate drifted IMU = truth + few ° noise); (b) torso-scaled, view-robust descriptor + view-quality gate; (c) try a stronger monocular estimator later. None blocks exp 08.
2. **David — exp 08 hardware (now one camera):** flash `firmware/beacon/beacon.ino` on a Wemos D1 mini (LED on D1/GPIO5 + resistor; `firmware/beacon/README.md`), plug into the recording PC; one camera mounted; rebuild the server from the `drift-logger` branch (8fe456e1). Session protocol: `docs/06-recorder-beacon.md`.
3. **First session → exp 08:** record per protocol (events via `python -m slimevr_camera.recorder.events`); Claude assembles the run (`recorder/session.py`), decodes frame times (`recorder/decode.py`), calibrates the camera (D15 path, simplified by D36: Umeyama HMD-trajectory + floor only, no cam–cam), runs the familiar-pose loop on genuinely recurring poses, measures the real reset-horizon extension.
4. Then: pose-conditioned correction model (D32) trained on licence-clean data; runtime scheduler with bone weighting (D30); server integration through the Stay Aligned yaw slot (`Tracker.kt:300`, D22) extended to 3-DoF (D31).
5. Parked, ready to resume: two-camera triangulation (D36; code stays in `pipeline.py`); retroreflective markers (D35, `notes/retroreflective-tape-idea.md`); OpenIPC (Q21); TotalCapture further subjects (validation only).

## Code map (details in CLAUDE.md)

`src/slimevr_camera/`: skeleton/geometry/heading/pipeline (core), `familiar.py` (D33 templates + in-pose measurement), `mono.py` (D36 monocular lifting glue: COCO↔H36M-17, world conversion), `markers.py` (parked marker track), `synth/`, `data/movi.py` + `data/totalcapture.py` (verified loaders), `recorder/` (capture, beacon, decode, events, session, camera_ctl). `tools/motionbert/` = isolated uv env for the MotionBERT lifter (checkpoints in `/mnt/data2/.../models/motionbert/`, lifted 3D cached in `data/movi/lift3d/`). Experiments 01–07, 09 each with README + results. GPU box `vulcanus` via `tools/vulcanus-setup.sh`.

## Reports

- Session report (kept current): `docs/05-report-2026-08-26.md`; shareable page https://claude.ai/code/artifact/607b9343-0b9e-49be-a738-fd80362a6b70 (rebuild: `uv run python tools/build-report.py OUT.html`, republish same scratchpad path).

## Session log (condensed)

- 2026-08-26 — Scaffold; Q&A rounds 1–2 (targets, setup, licences); literature pass 1 (§A–§D, §G; 31 notes); PR #1805 found, fetched, deep-read (reference only, D20/D22); exps 01–02 (synthetic harness; axis formulation; drift model revised to motion-driven random walk after David's objection); beacon idea (D17).
- 2026-08-27 — D26 revised (IMU trusted post-reset ↔ camera drift-free), D31 (3-DoF), D33 (familiar poses, seated idle), D34 (licence policy); exp 04 completed (3 detectors × 5 subjects); exp 05 (per-pose repeatability); §G2+§H syntheses; recorder + beacon built and verified; DriftLogger extended (HMD/controllers).
- 2026-08-28 — TotalCapture access granted; loader + conventions verified; exp 06 (1080p same as 800×600; IMU floor 2–3°/6–10°; no recurring poses in TC); cameras probed and fully scripted (hi3510 CGI, `image_type` profiles, `targety` exposure, night-vision recipe); tape test #1 (patches saturate but 3–6 px; marker design v2: bar+dot, strap ring; estimators written and tested).
- 2026-08-31 — Marker track parked (D35); `familiar.py` + exp 07: measurement path inside budget on MoVi. Handoff cleanup.
- 2026-09-01 — D36 single-camera main line (David). MotionBERT chosen + set up (`tools/motionbert/`, `mono.py`, literature note); exp 09 run (5 subjects × PG1/PG2 × lite/full): frontal standing inside budget, seated + side view fail; view dependence + IMU-prior flip idea documented.
