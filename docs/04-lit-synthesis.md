# 04 — Literature synthesis

Grounded findings only. Each claim traces to a note in `literature/`.
Updated as verification passes complete.

## §A IMU + video fusion  (pass 1, 2026-08-26 — 6 notes)

Notes: `2018-vonmarcard-vip-3dpw`, `2020-zhang-imu-multiview-geometric`,
`2020-kaichi-imu-single-rgb`, `2023-pan-robustcap`, `2025-pan-diffcap`,
`2026-tang-stereo-inertial-poser`.

**Headline: nobody has shipped "camera corrects IMU yaw" as a product, but the
one paper that models per-sensor heading explicitly (VIP, 2018) shows it is
where almost all the fusion gain lives.**

- **VIP (von Marcard 2018)** — offline optimisation over a whole sequence;
  one heading angle per IMU about world-up, constant per sequence, solved
  jointly with pose and camera. Ablation on TotalCapture: IMU-only 55 mm →
  28 mm *just by applying the recovered per-sensor headings* + initial pose.
  13 IMUs + 1 cam: 12.1° MPJAE; 6 IMUs: 15.3°. This is the closest precedent
  to our design and validates the yaw-only framing (D6). No code.
- **Zhang 2020** — 8 IMUs + 4 *calibrated* cams; IMU limb directions
  reinforce 2D heatmaps. Information flows IMU→camera, no drift handling.
  Reusable: bone-direction dot-product residual. MIT code.
- **RobustCap (Pan 2023) / DiffCap (Pan 2025)** — 6 IMUs + monocular,
  real-time, learned fusion. Drift is absorbed implicitly by a root-relative
  IMU branch; camera fixes root/translation. Both explicitly leave
  magnetic/yaw drift open. MIT code, MediaPipe front-end, useful as an
  **evaluation harness** (TotalCapture real IMUs, synthetic IMUs from AMASS).
  Both warn MediaPipe mean-confidence gating is brittle → use stillness +
  temporal stability instead (supports our gate design).
- **Stereo-Inertial Poser (Tang 2026, arXiv)** — 6 IMUs + calibrated stereo.
  Hip/shoulder global rotation error ~10–11° vs 13.4° RobustCap vs 10.8°
  IMU-only; the big win of stereo is translation (23 → 5–9 cm). Trick worth
  copying: build "synthetic stereo" from adjacent cameras of an existing
  multi-view dataset to test a 2-camera setup with no hardware.

**Accuracy reality check.** Full joint-rotation error with camera fusion sits
at ~9–13° on TotalCapture, and fusion barely beats IMU-only in *rotation* there
— but TotalCapture uses Xsens with magnetometers, which barely drift. Nobody
reports a *heading-only* error. Our 5° heading target (D11) is therefore
**unmeasured territory**, not contradicted, and experiment 01 must measure it.

**Design lessons adopted**
1. Parameterise drift as VIP does: one rotation about world vertical per
   tracker, piecewise-constant between corrections.
2. Correct root (hip) yaw first, then children relative to it.
3. Gate on stillness + temporal stability, not on model confidence alone.
4. Use RobustCap/DiffCap code + TotalCapture/AMASS as a harness before
   touching real hardware.

**Unverified:** whether 3DPW ships raw (drifting) per-sensor IMU quaternions;
RobustCap's IMU–camera calibration (in supplementary); Stereo-Inertial Poser
licence.

## §D Camera self-calibration from humans / HMD  (pass 1, 2026-08-26 — 8 notes)

Notes: `2025-lee-spatiotemporal-people-calib`, `2025-lee-steerpose`,
`2024-tang-cascalib`, `2018-takahashi-human-pose-calib-pattern`,
`2021-fei-single-view-distance-pose`, `2026-yang-sports-stick-calib`,
`2025-desousa-colocated-vr-hmd-alignment`, `tool-liv-unreal-mrc-calibration`.

**Headline: extrinsics from people alone reach ~0.5–2° rotation on real data,
comfortably inside our 5° heading budget. Translation/scale is the weak axis —
and the HMD gives us exactly that for free.**

- **Lee 2025 (RA-L)** — multi-cam extrinsics + integer frame sync + person
  association from monocular 3D pose lifting, intrinsics known. Real 4-cam:
  0.4–1° typical rotation, 0–1 frame sync. No code.
- **CasCalib (Tang 2024)** — the only open-source end-to-end pipeline: focal +
  ground plane from upright people, 1-D sync, rotation search, BA. ~1.8°
  rotation; translation weak; sync 4–11 frames when focal is predicted. No
  LICENSE file (ask/assume unusable commercially until clarified).
- **Fei 2021** — single view: floor normal 0.5–2° from ankle/shoulder
  keypoints; focal only 3–12 % (worse with few frames) → **people-only focal
  estimation is not good enough; get intrinsics per camera model once**.
- **Yang 2026** — adding a known-length rigid object drops rotation error ~10×
  (synthetic). Our analogue: known bone lengths, and the HMD.
- **de Sousa 2025** — HMD tracked by external mocap; Umeyama + least-squares
  alignment of frames; 3–5 cm ATE. This is the math for HMD-as-fiducial.
- **LIV / Unreal MRCalibration** — MR-capture tools solve camera pose in
  SteamVR space by PnP on a tracked *controller* held on on-screen crosshairs.
  No published accuracy. Proves the "tracked VR object as fiducial" workflow
  is consumer-acceptable.

**Precedent check.** No paper solves camera extrinsics from a trusted 3D
skeleton at one instant (our "reset moment" idea). It is plain PnP/Kabsch on
~15 joints, geometrically sound, but a single still pose is near-coplanar →
depth/roll degeneracy. **Accumulate several poses/resets**, don't rely on one.
No paper detects an HMD in RGB for camera pose either; Quest MRC internals
unverified.

**Calibration path adopted (v1)**
1. Intrinsics once per camera *model* (checkerboard or lookup) — not from people.
2. Floor plane + gravity: from upright people (Fei/CasCalib style) cross-checked
   with IMU gravity.
3. Scale + world yaw + position: HMD trajectory (SteamVR) vs head keypoint,
   Umeyama + LS with an unknown head-keypoint→HMD offset (de Sousa).
4. Camera–camera relative pose: keypoint correspondences over time (Lee/CasCalib).
5. Refinement: reset-moment skeleton correspondences, accumulated.
6. Clock sync: correlate camera-derived motion against IMU angular velocity
   (replaces CasCalib's 1-D sync); still-moment corrections are insensitive
   to residual offset anyway.
Expected: ≤1° rotation, cm-level position — calibration will not be the
bottleneck; the pose model's heading accuracy (§B) will.

**Unverified:** SteerPose code/licence; Yang 2026 repo; CasCalib licence;
Lv & Nevatia 2006 (walking-human calibration, could not fetch).

## §B Monocular / video body-model pose (rotation accuracy)  (pass 1, 2026-08-26 — 10 notes)

Notes: `2023-goel-hmr2`, `2021-li-hybrik`, `2023-shin-wham`, `2024-wang-tram`,
`2024-shen-gvhmr`, `2025-wang-prompthmr`, `2024-dwivedi-tokenhmr`,
`2023-cai-smplerx`, `2023-kaufmann-emdb`, `2025-ludwig-uplift-rotations`.

**Headline: published per-joint rotation error of SMPL regressors is 22–25°
MPJAE (EMDB, Table 3). Nobody publishes heading-only error. Twist about the
bone axis is known-unreliable. The 5° heading target is NOT supported by
any published number — it has to come from (a) restricting to heading,
(b) still-moment averaging, (c) stereo geometry rather than regression.**

- **HMR2.0/4DHumans, TRAM/VIMO, WHAM** — MIT, CUDA, camera-frame SMPL; no
  rotation metrics published. WHAM's world heading is autoregressive and
  drifts on long clips (GVHMR Fig. 9) — ironic for our purpose; use
  camera-frame mode + our own extrinsics.
- **GVHMR** — gravity-aligned per-frame frame, non-autoregressive, the only
  paper to *plot* global orientation error (bounded). Static-camera mode.
  **Non-commercial licence** → research only.
- **HybrIK** — swing/twist decomposition: swing analytic from 3D joints,
  twist a learned scalar. Twist is near-zero for most joints but wide-range
  at elbow/wrist. EMDB MPJAE 24.5°. MIT. The *structure* (heading from swing
  only, twist from IMU) is exactly our split.
- **PromptHMR (2025)** — best numbers, heaviest stack, licence unverified.
- **SMPLer-X-S (32 M)** — CPU-feasibility candidate for end users.
- **Ludwig 2025** — rotation-supervised keypoint lifter reaches ~9° MPJAE
  in-domain: keypoint-first pipelines are not worse than mesh regressors for
  rotation.
- **EMDB** — the dataset with per-joint rotation GT; authors note lower-arm
  rotation failures that MPJPE hides.

**Consequence for the design**
- Do not ask any model for a rotation. Ask for **3D joint positions** (from
  two cameras: triangulated 2D keypoints; from one: lifted with our bone-length
  priors), derive each bone's floor-projected direction, and average over the
  still window. Heading error then ≈ keypoint error / bone length: 2 cm over a
  40 cm shin ≈ 3°, over a 25 cm forearm ≈ 5°. **Feet/forearms are the tight
  spots; thighs/shins/torso should be fine.** SMPL regressors become a
  fallback for occluded limbs, not the primary path.
- Twist (forearm pronation, thigh internal rotation) stays IMU-only.
- Licences: MIT stack = HMR2.0 / HybrIK / WHAM / TRAM; GVHMR & TokenHMR are
  non-commercial (research-only for us).
- All run on the 3090. Nothing documents CPU inference → end-user deployment
  is an open engineering problem (§F), not a research one.

**Unverified:** PromptHMR/SMPLer-X licence text; absolute degrees in GVHMR
Fig. 9; CPU feasibility of anything.

## §C Sparse-IMU pose & drift handling, §G datasets  (pass 1, 2026-08-26 — 8 notes)

Notes: `2018-huang-dip`, `2021-yi-transpose`, `2022-yi-pip`, `2022-jiang-tip`,
`2024-yi-pnp`, `2025-zuo-tic`, `2025-yi-globalpose`, `datasets-imu-video`.

**Headline: the sparse-IMU literature never handles global yaw drift — it
calibrates once (T-pose / walking step) on magnetometer-aided Xsens and
benchmarks on minute-scale clips. The only online scheme (TIC 2025) fixes
*differential* per-sensor drift and explicitly cannot fix global yaw. That is
precisely the hole a camera fills.**

- **DIP / TransPose / PIP / TIP** — heading from head sensor or T-pose, then
  root-relative normalisation hides yaw from the network; heading ultimately
  comes from the magnetometer (TransPose §5.5.1). Joint angle errors 15–17°.
  PIP: 4.2° *network* drift over 4.6 h synthetic — sensor drift never measured.
- **PNP 2024** — synthesises raw gyro/acc/mag and perturbs calibration in
  training; measures TotalCapture's own calibration as **8.6–12.1° off**.
  → Even research-grade "ground truth" IMU heading is ~10° wrong; our 5°
  target is stricter than what benchmarks themselves achieve.
- **TIC 2025** — first to model time-varying world-drift and mounting
  rotation, estimated online from motion diversity in an ego-yaw frame.
  Without it 6-IMU methods' angular error roughly doubles over ~12 min
  (PNP 15.5° → 30.6°). Fails in low-activity/seated use — the opposite regime
  from ours (we work best when still). Complementary; worth reading in depth
  for the differential-drift part (mounting slip).
- **GlobalPose 2025** — one-step walking calibration; 20-min test without
  growth, but mag-aided. Unverified numbers.

**Datasets** (see `literature/datasets-imu-video.md`)
- **TotalCapture** — 13 Xsens + 8 static cams + Vicon; raw IMU available.
  **Primary test bed**: inject gyro-only yaw drift into the IMU stream, use 2
  of the 8 cameras as "our" pair (Stereo-Inertial Poser trick), measure
  heading recovery. Registration, research-only.
- **3DPW** — 1 moving phone camera; GT is itself IMU-derived. Secondary.
- **CIP** — raw MPU-9250 gyro/acc/mag, CC BY 4.0: lets us measure consumer
  gyro yaw drift ourselves. No video.
- **Nymeria** — 20-min+ sessions, Aria cameras, CC BY-NC; raw IMU unclear.

**Consumer IMU drift numbers**: none in the literature. SlimeVR docs quote
"reset time" only (BNO085 45–60 min, BMI270 10–20 min), methodology unverified.

**Design lessons adopted**
1. Benchmark on TotalCapture with synthetic drift injection before hardware.
2. Treat mounting slip as a separate slow variable (TIC) — the camera
   correction should estimate heading offset *and* watch for mounting change.
3. Don't trust any dataset's IMU heading as ground truth below ~10°; use
   optical GT (Vicon) for heading truth.

## §G2 Multi-view RGB + marker-based 3D GT (for detector-bias measurement)  (2026-08-26, 22 datasets in `literature/datasets-multiview-gt.md`)

**Headline: TotalCapture is the best fit but gated; MoVi is downloadable
today and good enough to start; nothing public has VR-headset wearers with
independent GT.**

Ranked for measuring 2D-detector heading bias (needs GT *not* derived from a detector):
1. **TotalCapture** — Vicon (joint angles), 8 static genlocked 1080p/60 cams,
   IMUs. Email + registration; Surrey's own record lists CC-BY-NC (softer
   than the site text). Request sent 2026-08-26.
2. **Fit3D** (+CHI3D/HumanSC3D) — Vicon 25 joints + SMPL-X rotations, 4 static
   900² /50 fps calibrated cams, constrained indoor fitness motion (close to
   dance/VR regime). Access via IMAR account; PI requirement unverified.
3. **MoVi** — Qualisys 67-marker GT + rotations, 2 hardware-synced calibrated
   FLIR cams (800×600/30) + 2 iPhones, 90 subjects, 17 Noitom IMUs. **Open
   direct download (Borealis Dataverse), no registration.** Low-res, two
   views — which is exactly our deployment geometry.

Runners-up: MAMMAEval (Vicon + studio cams, swing dance, MPI account),
HumanEva (tiny), MPI-INF-3DHP (open, 14 cams, but GT is markerless Captury →
not fully independent). Human3.6M: academic email + named advisor → treat as
unavailable.

**Circular (GT triangulated from a 2D detector) — fine for fine-tuning and
motion content, NOT for bias measurement:** CMU Panoptic, AIST++ (dance),
HuMMan, RICH, EgoBody, EMHI, ASPset.

**VR headsets:** none with marker GT + multi-view RGB. EgoBody (HoloLens2,
circular GT), EMHI (PICO 4, third-person RGB apparently unreleased), WHIP
(2026, Quest 3 + Captury, release unverified). → Headset robustness must
come from **synthetic** data (§H) and our own recordings.

**Decision:** start experiment 04 on **MoVi** now (2 calibrated views, marker
truth, 90 subjects, IMUs as a bonus); move to TotalCapture/Fit3D when
access arrives for higher resolution and more views.

## §H Synthetic data: motion → body → render  (2026-08-27 — 5 notes)

Notes: `2023-black-bedlam`, `2019-mahmood-amass-and-smplx-licences`,
`generative-motion-models`, `synthetic-to-real-domain-gap`,
`synthetic-human-data-generators`.

**Headline: the pipeline is available and open on Linux, but every body /
motion asset in it is non-commercial, and the evidence says synthetic data is
a *supplement* for a 2D detector, never a replacement for real labels. The
one thing nobody has — a VR headset rendered from external cameras — is
exactly our gap, and it may be solvable far more cheaply than by rendering.**

- **BEDLAM (CVPR 2023, 2.0 NeurIPS 2025)** — AMASS motions on SMPL-X bodies
  with simulated clothing, Unreal renders, full GT. Synthetic-only training
  matches real-only for SMPL regressors (3DPW PA-MPJPE 46.6 vs 46.4). Render
  tools are Windows/Unreal; licence is MPI non-commercial for data, code
  *and derived weights*; no 2D keypoint evaluation in either paper.
- **Licences (AMASS, SMPL-X, `smplx`)** — all MPI non-commercial; weights
  trained on them inherit it. Permissive motion exists at the source (CMU
  mocap "free for all uses", ACCAD CC BY, DanceDB/HDM05 CC BY-SA) but the
  AMASS SMPL-X fits re-wrap it in NC terms → a commercial-OK pipeline would
  re-fit from C3D/BVH onto a non-SMPL rigged body. **Decision needed
  (Q19): is any commercial use foreseen?** For a non-commercial open-source
  SlimeVR release everything is usable as-is with NC-labelled weights.
- **Generative motion** — HumanML3D-based models (MDM, MotionGPT, MoMask)
  output joint positions needing an IK fit (twist ambiguity); EDGE and
  AIST++ give SMPL rotations directly (dance). All weights are NC in practice
  via their training data. Text prompts can't express VR play; **David's own
  SlimeVR + headset recordings retargeted to SMPL-X are the highest-value,
  licence-free motion source** for VR-specific movement.
- **Toolchain** — Blender on Linux: MPI SMPL-X add-on (AMASS npz → animated
  body) + XRFeitoria (Apache-2.0; multi-camera, joint export) + BlenderProc /
  Poly Haven HDRIs (CC0) for randomisation; parent our own CC0 HMD +
  controller meshes to head/wrist bones. Skip Unreal.
- **Domain gap for 2D detectors** — consistent pattern across SURREAL,
  PeopleSansPeople, RePoGen, Trampoline: synthetic-only < real-only <
  synthetic-pretrain + real fine-tune. Gains come from covering a *specific*
  gap (RePoGen: unusual viewpoints, ViTPose-H 69 → 81 AP) and saturate after
  a few thousand images; more synthetic can hurt. SynthPose shows projected
  BEDLAM labels fine-tune ViTPose without collapse if real COCO is mixed in
  per batch and a small real set fixes the label-convention mismatch. Recipe:
  mix real, heavy photometric augmentation incl. JPEG/ISO noise (mimics RTSP),
  diverse focals, label adaptation.
- **HMD wearers** — no paper measures 2D keypoint accuracy on a person
  wearing a VR headset from a third-person camera. EgoBody's authors had to
  hand-fix detections. Before any rendering: run off-the-shelf detectors on
  our own footage and label ~200 frames; then test whether a simple
  **headset copy-paste augmentation on COCO images** already closes the gap
  (far cheaper than rendering).

**Design consequences**
1. Synthetic rendering is the *third* data source, after (a) marker-GT
   datasets (MoVi / TotalCapture / Fit3D) and (b) our own recordings with
   IMU-after-reset pseudo-labels; it exists to cover headset/controllers,
   arm-up dance poses, low/wide cheap cameras.
2. Heading-aware fine-tuning (D32) should train on projected-joint labels
   from all three sources with real data mixed in per batch.
3. Licence gate first (Q19); if commercial use is possible, avoid SMPL-X /
   AMASS at render time.
4. Effort (agent estimate): Blender SMPL-X + HMD + camera script ~1–2 weeks;
   first RTMPose fine-tune ~1 week; real labelled VR test set (~200 frames)
   2–3 days — do the test set first.
