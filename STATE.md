# STATE — read first

_Last updated: 2026-08-26 (session 1: scaffold, Q&A rounds 1–3, literature pass 1, PR #1805 analysis)_

## Status

Phase 0 → 1. Framing done (Q1–Q15 answered, D1–D22). Literature pass 1 complete (§A–§D, §G; `docs/04-lit-synthesis.md`, 31 notes). Community search done (`notes/community-prior-work.md`). **Key find: SlimeVR-Server PR #1805 (jabberrock, Stay Aligned author) is a one-shot video-calibration proof of concept that already does camera→IMU yaw + mounting correction.** Fetched locally as branch `pr-1805` in `../SlimeVR-Server` (70 files, +8.5k lines, commit 487e2419, 2026-03-16). **Experiment 01 (synthetic, keypoint level) done:** camera heading error inside still windows < 2° at 10 px noise for all 11 trackers; residual after correction 1–3° dominated by drift between windows. See `experiments/01-synthetic-heading/README.md`. Harness code in `src/slimevr_camera/`.

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
| D13 | 2026-08-26 | Community data: opt-in raw video is acceptable (HMD anonymizes), derived-only as fallback tier | David. |

## Open questions (blocking or shaping)

- Q6b Exact RTSP camera model/resolution/fps. Night mode exists but may not be switchable at will (David) — test: does day mode see 850 nm at all? Which models expose night mode via ONVIF/API?
- Q14 Can the cameras see the Quest 3 Touch Plus controllers' IR LEDs in night mode? (would make them free tracked fiducials)

## Next actions

1. **Experiment 02 — bias, not noise:** run a real 2D detector (RTMPose via rtmlib, MIT) on two-view footage (BEDLAM-style render, or any public multi-view video with 3D GT) to measure *systematic* keypoint offsets and their effect on lateral-axis headings; add extrinsic-error sweep (0.5–2°) and occlusion to the synthetic harness.
1a. **Harness:** add (i) thermal-tilt error on the IMU side, (ii) demand-driven gate on rotation travelled, (iii) online per-tracker scale-error estimation from successive corrections — measure how much it cuts between-window error.
1b. TotalCapture adapter once access is granted (same pipeline, real IMU + Vicon truth).
2. **Recorder (tools/recorder):** 2× RTSP + tracker raw quaternions (reuse `TrackersSource` pattern from PR #1805) + beacon blink decode. Design the ESP32 beacon.
3. Literature pass 2: **§H synthetic data (AMASS + IMU simulation + game-engine rendering, BEDLAM)** — David's suggestion; the layer above the keypoint-level harness. Then §F quantisation/CPU inference; §E consumer IMU drift (CIP dataset); Lv & Nevatia 2006; verify 3DPW raw IMU.

## Log

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
