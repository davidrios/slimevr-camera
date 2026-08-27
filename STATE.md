# STATE — read first

_Last updated: 2026-08-26 (session 1: scaffold, Q&A rounds 1–3, literature pass 1, PR #1805 analysis)_

## Status

Phase 0 → 1. Framing done (Q1–Q15 answered, D1–D22). Literature pass 1 complete (§A–§D, §G, §G2, §H; `docs/04-lit-synthesis.md`, 31 notes). Community search done (`notes/community-prior-work.md`). **Key find: SlimeVR-Server PR #1805 (jabberrock, Stay Aligned author) is a one-shot video-calibration proof of concept that already does camera→IMU yaw + mounting correction.** Fetched locally as branch `pr-1805` in `../SlimeVR-Server` (70 files, +8.5k lines, commit 487e2419, 2026-03-16). **Exp 04 first result (MoVi, RTMPose-m, 3 subjects): real-detector heading error is pose-dependent, not white — 1-s averaging leaves 5–11° sd (chest 5, hip 7, shins 5–6, thighs 10–11); 5° budget NOT met by an off-the-shelf detector at 800×600/4.5 m. Fine-tuning (D28) is load-bearing.** Bigger detector (RTMPose-x wholebody) does NOT help → structural. Feet (toes from wholebody) are the *best* heading source when still (MAE ~1.7°), thighs the worst. Experiments 01–02 (synthetic) done. Exp 02 (revised): drift is a motion-driven random walk of unmeasured magnitude σ_m; residual ∝ σ_m·√(gross motion since last correction); required cadence unknown until σ_m is measured (Q17). camera heading error inside still windows < 2° at 10 px noise for all 11 trackers; residual after correction 1–3° dominated by drift between windows. See `experiments/01-synthetic-heading/README.md`. Harness code in `src/slimevr_camera/`.

## Working hypothesis (validated by VIP 2018 ablation; heading accuracy still unmeasured)

The correction we actually need is **per-tracker yaw offset** (heading about world vertical), applied occasionally. Pitch/roll are gravity-referenced and do not drift. Position in SlimeVR is derived by forward kinematics from orientations, so yaw drift on a bone *is* the position drift of everything distal to it. If the camera can tell us each limb's heading with a few degrees of accuracy during a still moment, that is enough — we do not need full real-time 3D pose fusion. See `docs/01-approach.md`.

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
| D13 | 2026-08-26 | Community data: opt-in raw video is acceptable (HMD anonymizes), derived-only as fallback tier | David. |

## Open questions (blocking or shaping)

- **Q17 Measure σ_m** — protocol agreed in principle: `experiments/03-onbody-drift/PROTOCOL.md` (worn set, reset in a jigged known pose, move, return + hold, repeat; DriftLogger raw @100 Hz, not BVH). Waiting on David to run it.
- Q16 (demoted) net turning per minute in VR play — matters only for the minor yaw-scale term.
- Q6b Exact RTSP camera model/resolution/fps. Night mode exists but may not be switchable at will (David) — test: does day mode see 850 nm at all? Which models expose night mode via ONVIF/API?
- Q14 Can the cameras see the Quest 3 Touch Plus controllers' IR LEDs in night mode? (would make them free tracked fiducials)

## Next actions

1. **David — hardware for the own-room recorder:** flash `firmware/beacon/beacon.ino` on any Arduino/ESP32 with a visible LED (+ optional 850 nm IR), plug into the recording PC; mount the 2 RTSP cameras (~2–3 m high, ±30–45° in front); rebuild the server from the `drift-logger` branch (commit 8fe456e1 adds HMD/controller positions). Then a first session per `docs/06-recorder-beacon.md` §protocol.
2. **Claude — session tooling:** `events` marking tool (reset / pose labels with wall time); run-folder assembler (`data/runs/<stamp>_<label>/`); loader for own recordings mirroring `data/movi.py` (frame→wall via beacon, DriftLogger, BVH, HMD).
3. **Automatic full reset in familiar poses (D33) — the build target:** familiar-pose detector (templates learned while trusted: standing reset + seated idle); in-pose measurement of pelvis/chest/feet headings and bone directions (3-DoF, D31); per-pose bias learned in the trusted window (D32); application through the full-reset path; confidence → prompt. Evaluate first on MoVi still stances, then on own recordings.
4. **HMD gap, cheap first (§H):** off-the-shelf detectors on own headset footage; label ~200 frames; test headset copy-paste augmentation on COCO before any rendering.
5. **Runtime scheduler:** per-unit drift statistics from successive corrections; bone weighting per D30.
6. Later: TotalCapture adapter (validation only, D34) if access is granted; exp 03 (optional); literature §F (CPU inference/quantisation) when a model is chosen; Blender render pipeline only if the cheap HMD test fails.

## Reports

- Session 1 (2026-08-26): `docs/05-report-2026-08-26.md` (figures in `docs/figures/`); shareable page https://claude.ai/code/artifact/607b9343-0b9e-49be-a738-fd80362a6b70 (redeploy from `scratchpad/slimevr-camera-report.html` builder in session history — regenerate from the md if lost).

## Log

- 2026-08-26 — Q18 answered: RTX 3090 is in `vulcanus` (david@192.168.15.27, SSH). GPU work goes there (see CLAUDE.md §7).
- 2026-08-26 — Exp 04 interim: detector heading error is temporally correlated / pose-dependent; averaging doesn't fix it (see experiment README). vulcanus GPU set up (65 fps RTMPose-m, cu12 ORT via pyproject).
- 2026-08-26 — Exp 04 started on MoVi: loader, download, calibration verified, detection running. Datasets now live on /mnt/data2 (root volume 95 % full).
- 2026-08-27 — Recorder + beacon implemented (host-driven serial LED, Manchester counter code, ffmpeg copy capture, correlation+fit decoder). Ready for hardware.
- 2026-08-27 — Q19 → D34: shipped model treated as commercial-adjacent; NC datasets eval-only; clean training data = own + community + permissive mocap.
- 2026-08-27 — §H synthesis written (5 notes): Blender/XRFeitoria route; all body/motion assets NC (Q19); synthetic supplements real, never replaces; HMD-on-avatar from external cameras is a genuine gap.
- 2026-08-27 — Exp 04 complete on 5 subjects × 3 detectors (vulcanus): model size irrelevant, confirmed. Seated/idle motions: chest & feet inside budget as-is; hips need per-pose calibration; cross-legged is hardest.
- 2026-08-27 — Seated relaxed idle added as primary target pose (UX: no more stand-up resets while seated).
- 2026-08-26 — D33: scope = automatic full reset in familiar poses; user is a participant; heavy-activity drift handled by manual reset.
- 2026-08-26 — David's notes: IMU-after-reset is the calibration source for the camera (D26 revised); correction must be 3-DoF not yaw-only (D31). Exp 05 planned.
- 2026-08-26 — §G2 dataset verification: MoVi chosen to start exp 04 (D29); no headset datasets exist.
- 2026-08-26 — D28: fine-tuning for VR conditions is the core bet; dataset verification (multi-view + marker GT) and BEDLAM/§H feasibility agents launched.
- 2026-08-26 — David: no offline drift model (D26); effort goes to camera-side robustness + AI training (D27). Exp 03 demoted to optional. No rigid bar exists (protocol fixed).
- 2026-08-26 — Exp 03 protocol written (David's known-pose return procedure; BVH rejected as post-correction, DriftLogger instead; jig for pose repeatability).
- 2026-08-26 — Exp 02 revised after David's objection: 'net turning' conclusion retracted; motion-driven random walk added to IMU model; σ_m measurement (drift-lab run E) proposed. D25 rewritten.
- 2026-08-26 — Exp 02 done (`experiments/02-scale-learning/`): k learnable, gain modest, cadence is driven by net turning (D25, Q16). Also found the IMU-model bias edit had silently failed earlier — now truly aligned.
- 2026-08-26 — drift-lab FINDINGS read (after a wrong first read caused by the t₀ placeholder pitfall): static drift < 1 °/h; drift is gyro **scale factor** +0.43 % / −0.23 %, opposite signs per unit; thermal tilt 0.8–5.7°. Synthetic IMU defaults now match. New idea: learn per-tracker scale error from successive camera corrections (`notes/drift-lab-numbers.md`).
- 2026-08-26 — Experiment 01 done: harness works; noise is not the threat, bias and correction frequency are. Key formulation: compare the *same physical axis* on camera and IMU sides (drift rotates every axis' floor projection equally). David suggested game-engine/generative synthetic data → agenda §H.
- 2026-08-26 — PR #1805 deep-read: monocular 2D projected-direction residual, walk-in-circle for limbs, torso IMU-only; several math bugs; borrow <10% (pinhole classes, LM+numerical Jacobian, recorder, SimCC decoder). Integration slot decided (D22).
- 2026-08-26 — Q&A round 3: per-bone target (D19), PR #1805 reference-only (D20), specific camera OK (D21).
- 2026-08-26 — Community search: PR #1805 found and fetched; maintainers favourable (issue #1455); SolarXR has no yaw-correction message — PR #1805's hook is the integration path.
- 2026-08-26 — §C/§G synthesis: IMU literature never fixes global yaw (TIC 2025 explicitly can't); TotalCapture chosen as benchmark (D18).
- 2026-08-26 — David proposed IR beacon sync (D17); extensions noted in `notes/ir-beacon-idea.md`.
- 2026-08-26 — §B synthesis: SMPL regressors 22–25° MPJAE; pivot to triangulated joints → geometric heading (D16). Q13 raised.
- 2026-08-26 — §D synthesis: calibration is not the bottleneck (≤1–2° achievable); HMD-as-fiducial is consumer-precedented (LIV) but unpublished.
- 2026-08-26 — §A synthesis written: VIP 2018 is the precedent; heading-only accuracy is unmeasured in literature; RobustCap/DiffCap = evaluation harness.
- 2026-08-26 — Q&A round 1 answered (D6–D10). Literature pass 1 launched.
- 2026-08-26 — Project scaffolded. Prior work surveyed: `drift-lab` (rigid bar yaw-drift rig, DriftLogger patch), `sensordump` (2024 raw dumps + toy Kalman), server internals (resets, Stay Aligned, IKSolver, Localizer).
