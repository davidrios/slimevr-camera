# Datasets with multi-view static RGB + detector-independent 3D ground truth (§G, for D28 / exp 04)

- **Read depth:** dataset web pages, download/licence pages and originating papers (arXiv/CVF PDFs) fetched 2026-08-26 by four parallel verification passes; nothing downloaded. "Unverified" marks facts we could not confirm on a primary page.
- **Date read:** 2026-08-26

**Purpose.** Measure the *systematic* limb-heading bias of 2D detectors (RTMPose etc.) by triangulating their keypoints from ≥2 static calibrated cameras and comparing against 3D truth that does **not** come from a 2D detector. Secondary: fine-tuning data for VR-room conditions. The circularity trap: many "3D GT" sets are OpenPose/HRNet/CPM triangulations, so a detector evaluated on them inherits the annotator's bias and looks better than it is. Those are flagged **circular** below.

## Comparison table

GT column: **marker** = optical marker mocap (independent); **markerless-commercial** = image-based system (Captury), independent of *our* detector but not of image cues; **circular** = triangulated from a 2D keypoint detector.

| Dataset | Year | RGB cameras (n, static?, res/fps, class) | Calib. shipped | 3D GT | Rotations? | Size | Motion / VR headset | Access |
|---|---|---|---|---|---|---|---|---|
| **TotalCapture** | 2017 | 8 static, 1080p 60 Hz, studio gantry, genlocked | stated "calibrated"; file format unverified (community toolboxes use them) | **marker** Vicon, 21 joints | yes (angles, BVH) | 5 subj, 1.89 M frames | ROM/walk/acting/freestyle; no VR | email to a.gilbert@surrey.ac.uk, registration, non-commercial (Surrey record says CC-BY-NC); institutional approval (per our earlier note) |
| **Human3.6M** | 2014 | 4 static Basler piA1000 1000×1000 50 Hz, industrial, hardware-synced with Vicon | yes (incl. fitted distortion) | **marker** Vicon T40 ×10 | yes | 11 actors, 3.6 M poses | everyday scenarios; no VR | academic-address form + advisor/PI name, manual approval; companies by email |
| **HumanEva-I/II** | 2006/07 | I: 7 static (4 gray Pulnix 644×488 + 3 colour UniQ 659×494) 60 Hz, software sync; II: 4 Basler 656×490 60 Hz, hardware sync | yes | **marker** Vicon 120 Hz | angles available (distributed format unverified) | 4 subj, ~40 k mocap frames | walk/jog/box/gesture; no VR | self-service sign-up + click-through licence, non-commercial; site TLS cert broken, use http |
| **MPI-INF-3DHP** | 2017 | 14 static (5 chest-high, 5 at 45°, 3 top, 1 knee; some fisheye), 25/50 fps, green-screen studio; resolution unverified | yes (`camera.calibration` per seq) | **markerless-commercial** (The Captury, paper §5 ref [68]) | no (positions only) | 8 actors, >1.3 M frames | exercise/sport/dance-ish; no VR | **open direct download** (flip `ready_to_download=0` in conf after reading licence), non-commercial, no redistribution |
| **Fit3D** | 2021 | 4 static 900×900 50 Hz, studio | yes (2 camera models) | **marker** Vicon, 25 joints + GHUM/SMPL-X | yes | 11 subj, ~3 M skeletons | fitness exercises; no VR | site account (IMAR non-commercial licence); institutional signature not stated, unverified |
| **CHI3D / HumanSC3D** | 2020/21 | 4 static synced with 10-cam Vicon; res/fps unverified (same IMAR rig) | unverified | **marker** Vicon + GHUM/SMPL-X | yes | 6 subj / 631 seq; 1,032 seq | two-person contact, self-contact; no VR | site account, IMAR licence |
| **MoVi (BMLmovi)** | 2020 | 2 static FLIR Grasshopper2 800×600 30 Hz hardware-triggered + 2 unsynced hand-held iPhone 7 | yes for the 2 FLIR (<0.2 px reproj.) | **marker** Qualisys ×15, 67 markers, 120 Hz; also 17 Noitom IMUs | yes (Visual3D + MoSh++ SMPL via AMASS) | 90 subj, 17 h video | everyday + sports; no VR | **open direct download** on Borealis Dataverse after accepting non-commercial terms |
| **OpenCap validation** | 2023 | 5 iPhones, static, ~60 fps (model/res unverified) | calibration images | **marker** + force plates, OpenSim IK | OpenSim joint angles | 10 subj, walk/squat/STS/jumps | no VR | SimTK account, Apache-2.0 use agreement |
| **MAMMAEval** | 2025 | 32 (16 for Singles) static IO Industries 2056×1504 30 Hz, studio | yes | **marker** Vicon → MoSh++ SMPL-X | yes | 17 couple **dance** + 22 single + 16 extra seqs | West-Coast-Swing dance; no VR | MPI portal register/sign-in; terms unverified |
| **HUM4D** | 2026 | 6 static RealSense D455 RGB-D, 720p **15 fps**, consumer | yes | **marker** Vicon ×44, 56 markers | SMPL/SMPL-X | 3 actors, 52 seq, 84 k frames | dynamic, occlusion, multi-person; no VR | **no download page found yet**; licence unstated |
| **Human4K** | 2026 | 8 static 4K studio, 15 fps | yes | **marker** Vicon → SMPL-X | yes | 11 actors/dancers, 6 M images | daily/sports/**dance**; no VR | "released when accepted" — not available |
| **BadmintonGRF** | 2026 | 8 static DJI Osmo Action 4, 1080p ~120 fps, consumer | unverified | **marker** Vicon ×8 + force plates | unverified | 10 subj, 156 trials | badminton; no VR | Tier 1 (mocap) Zenodo CC BY-NC; raw video Tier 2 institutional agreement |
| **WHIP** | 2026 | 120-cam Captury rig, static, 30 Hz; **RGB release unverified** (Edmond repo bot-blocked) | unverified | **markerless-commercial** (Captury) | skeletal | 14 subj, 7 h, 50 actions | daily/sports; **Meta Quest 3 worn** + phones/watches/insoles | Edmond DOI 10.17617/3.ZGVC7M; CC BY-NC-ND 4.0 (paper) / CC BY-SA 4.0 (page) — conflicting, unverified |
| **EMHI** | 2024 | 8 static Azure Kinect 30 Hz — **third-person RGB apparently not released** | via OptiTrack alignment | **circular** (HRNet triangulation + IMU head/wrist constraints; validated vs marker fits) | SMPL | 58 subj, 885 seq, 28.5 h, 3 lighting conditions | 39 VR/social actions; **PICO 4 HMD + leg trackers** | Baidu-pan link; CC BY 4.0 per paper |
| **EgoBody** | 2022 | 3–5 static Azure Kinect 1080p 30 Hz + moving HoloLens2 | implied, files unverified | **circular** (OpenPose + Kinect depth SMPL-X fit) | SMPL-X | 36 subj, 125 seq, 220 k frames | indoor social; **one subject wears HoloLens2** | online licence signature by email, CC BY-NC-SA + terms |
| **CMU Panoptic** | 2016 | 480 VGA 25 fps + 31 HD 1080p 30 Hz + 10 Kinect, static dome, SfM calibrated | yes | **circular** (CPM 2D detector triangulated over 480 views, §5) | no | 65 seq, 5.5 h | social games, dance, ROM; no VR | open direct download, research-only, no redistribution |
| **AIST++** | 2021 | 9 static 1080p (fps/sync unverified); cameras *estimated* by bundle adjustment, not measured | estimated params | **circular** (unnamed 2D detector triangulated, SMPL fit with mean shape) | SMPL pose | 30 dancers, 1,408 seq, 5.2 h | **dance**; no VR | annotations direct; videos under AIST Dance DB academic terms |
| **HuMMan** | 2022 | 10 static Azure Kinect 1080p 30 Hz + iPhone 12 Pro Max | implied | **circular** (HRNet-w48 triangulation, SMPL fit) | SMPL | 1000 subj, 400 k seq | 500 actions; no VR | Google Form, S-Lab non-commercial |
| **RICH** | 2022 | 6–8 static 4K 30 Hz (+ moving cam) | unverified | **circular** (AlphaPose/OpenPose, multi-view SMPLify-X, "pseudo-GT") | SMPL-X | 22 subj, 142 videos | outdoor scene contact; no VR | MPI account click-through |
| **ASPset-510** | 2021 | 3 consumer cams, outdoor, manual sync | yes | **circular** (2D keypoint triangulation) | no | 17 subj, 510 clips | sports; no VR | **CC0**, Internet Archive |
| **EMDB** | 2023 | 1 **moving** iPhone 13 Pro Max | ARKit poses | EM sensors, then image refinement with OpenPose (partly circular) | SMPL | 10 subj, 58 min | outdoor walking; no VR | application form + approval |
| **HSC4D** | 2022 | **none** (IMU + LiDAR only) | n/a | IMU+LiDAR optimisation | SMPL | 1 subj, ~250 k IMU frames | large-scale walk/climb | site down 2026-08-26; CC BY-NC-SA 3.0 per README |

Not qualifying (verified 2026-08-26, one line each): SportsPose (HRNet triangulation, only *validated* vs Qualisys), Harmony4D (ViTPose triangulation), EgoExo4D (detector + manual), FreeMan (detector-based), Motion-X/++ (monocular pseudo-GT), AthletePose3D (Qualisys *video* markerless), DNA-Rendering/ActorsHQ/MVHumanNet (MVS/keypoint annotations), FineDance/Inter-X/CoMPAS3D (Vicon/OptiTrack but no RGB released), ParaHome (RGB not released), Nymeria/RELI11D (single moving camera, Xsens GT), HOT3D/EgoBody3M (headset-only views), EgoAvatar/EgoRelight (Quest 3 + dome but Captury GT, 3–4 subjects), BEDLAM/EgoPoseVR (synthetic), MVPose3D (IMU suit GT, no download link found).

## Per-dataset notes

**TotalCapture.** Confirmed: Vicon marker GT with joint angles, 8 static genlocked 1080p/60 cameras, 13 Xsens IMUs. Access is an email to the Surrey contact with registration; the Surrey Open Research record labels it CC-BY-NC, which is friendlier than the "no redistribution" text on the site — worth citing in the access request (D23). Remains the only set with IMU + static multi-view + marker GT. Calibration file distribution not confirmed from the page text but every downstream paper (VIP, PNP, Zhang 2020) used it.

**Human3.6M.** Gold-standard marker GT (10 Vicon T40) with 4 industrial 1000×1000 cameras that are hardware-synced to the mocap; distortion-fitted camera parameters shipped. Access is the strictest: registration only from an academic e-mail with a named advisor/PI, manual approval; companies email separately. David has no institution (D23), so treat as likely unavailable.

**HumanEva.** Old, low-resolution (≈650×490) machine-vision cameras, 4 subjects, but marker GT and self-service registration with click-through licence — no PI approval seen. Useful as a *free* sanity set for a detector-bias script; too small and too low-res to be the main measurement.

**MPI-INF-3DHP.** GT is The Captury (commercial image-based markerless system; paper §5 and ref [68]). The paper does not describe Captury's internals, so whether it uses a learned 2D detector is unverified; what is certain is that GT is derived from the same images, so it is not independent in the way marker data is. It is the only open-direct-download multi-view set with 14 calibrated cameras; positions only, no rotations. Usable as a secondary set with the caveat recorded.

**Fit3D / CHI3D / HumanSC3D (IMAR).** Same institution as Human3.6M but a separate portal with a site account; the pages say "logged in with a valid account" and do not mention institutional signature — whether the registration form demands one is unverified. Vicon GT with 25 joints plus GHUM/SMPL-X rotations, 4 static 900×900/50 cameras with intrinsics for two camera models. Fitness motion (Fit3D) is "constrained indoor motion" of the kind we care about. Best candidate after TotalCapture if the account is granted without a PI.

**MoVi.** 15-camera Qualisys marker GT (67 markers) with joint rotations, plus two *hardware-triggered, calibrated* FLIR cameras (only 800×600, 30 Hz) — exactly a two-camera pair like ours — plus two unsynced iPhones. 90 subjects, open direct download from Borealis Dataverse after accepting non-commercial terms, no registration. Also carries 17 Noitom IMUs. The weakness is a narrow baseline/two views only and low resolution; the strength is zero access friction.

**OpenCap validation data.** Five consumer iPhones + marker mocap + force plates, 10 subjects, biomechanics-grade OpenSim angles. Small, but it is the one marker-GT set captured with the kind of cameras users own. SimTK account, Apache-2.0-style use agreement.

**MAMMAEval.** MPI-IS 2025: Vicon → MoSh++ SMPL-X with 32 (or 16) static 2056×1504 studio cameras; contains couple dance (West Coast Swing) and single sequences. Standard MPI portal registration (same as RICH: account + click-through, no PI signature observed on that portal). Best dance-with-marker-GT option; terms unverified.

**HUM4D (2026).** Consumer RealSense D455 RGB-D at 720p/15 fps in a ring, 44-camera Vicon GT, deliberately hard motion/occlusion. Closest hardware analogue to a cheap-camera rig, but only 3 actors, and no download page was found yet (licence unstated). Watch.

**Human4K (2026)** and **BadmintonGRF (2026).** Human4K: 8 static 4K cameras at 15 fps + Vicon, dancers, "released when accepted". BadmintonGRF: 8 DJI Osmo Action consumer cameras + Vicon, but raw video requires an institutional agreement. Both watch-list.

**WHIP (2026).** Only dataset with a Meta Quest 3 on the subject plus a professional capture rig. GT is Captury (markerless, image-based), and it is unverified whether any of the 120 RGB views are released (Edmond repository blocked our fetch; licence text conflicts between paper and page). If the videos are there, it becomes the best VR-headset set for *fine-tuning*, not for bias measurement.

**EMHI (2024).** Large (28.5 h, 58 subjects, PICO 4 + leg trackers, three lighting conditions) and CC BY 4.0, but GT is HRNet triangulation with IMU constraints (circular) and the release appears to contain only egocentric stereo + IMU + SMPL — no third-person Kinect RGB (unverified: Baidu-pan link only). Useful for VR-action motion priors, not for our measurement.

**EgoBody.** Confirmed headset content: the camera-wearer (HoloLens2) is visible in the 3–5 static Kinect views. GT is OpenPose + depth fitting (circular). Access by signing the online licence via email. Marginal: HoloLens2 is visually unlike a Quest, and the GT is detector-derived, but it is a real "person with HMD from fixed cameras" set with SMPL-X rotations.

**CMU Panoptic, AIST++, HuMMan, RICH, ASPset-510.** All confirmed circular: Panoptic uses CPM (Wei et al. 2016) over 480 views; AIST++ triangulates an unnamed detector through cameras that were themselves estimated by bundle adjustment from 2D poses; HuMMan HRNet-w48; RICH AlphaPose/OpenPose SMPLify-X ("pseudo-GT" in the authors' words); ASPset triangulates 2D keypoints. Panoptic's 480-view triangulation averages out random detector error but not bias shared across views (e.g. a consistent hip-centre offset), so it cannot be used to measure that bias. AIST++ is the only dance set at scale, ASPset the only CC0 one — both fine for fine-tuning, not for bias measurement.

**EMDB, HSC4D.** Neither has static multi-view video (EMDB: one moving iPhone; HSC4D: no camera). Listed for completeness; HSC4D site was unreachable.

## Recommendation (ranked for measuring detector heading bias)

1. **TotalCapture** — marker GT with angles, 8 static calibrated 1080p/60 views, IMUs on top; already our benchmark (D18). Friction: email + registration, institutional approval likely (D23 pending).
2. **Fit3D** (and CHI3D/HumanSC3D from the same rig) — Vicon + 4 static calibrated 900×900/50 cameras, rotations, constrained indoor exercise motion. Friction: IMAR site account; PI requirement unverified — try it.
3. **MoVi** — Qualisys + 2 hardware-synced calibrated FLIR cameras, 90 subjects, rotations, **no registration**. Low resolution and only two views, but it is the fastest way to get a real detector-bias number this week.
4. **MAMMAEval** — Vicon + 16–32 studio cameras, dance; MPI portal account. Best for the dance regime.
5. **HumanEva** — free, marker GT, tiny/low-res; sanity check only.
6. **MPI-INF-3DHP** — open download, 14 calibrated views, but Captury GT (image-based) — use with the caveat.
Watch-list: HUM4D, Human4K, BadmintonGRF (2026, all Vicon + consumer/4K cameras, not yet accessible).

For fine-tuning (secondary): AIST++ (dance, 9 views), CMU Panoptic, HuMMan, EMHI (VR actions, but egocentric-only release), EgoBody (HMD wearer visible), WHIP if videos ship. None combines VR headsets + multi-view consumer RGB + marker GT; the VR-headset-in-view gap is one we will have to fill with our own recordings (recorder, next action 3) or synthetic renders (§H).

## Open questions this raises

- Does the IMAR (Fit3D) account form require an advisor/institution like Human3.6M's? One attempt settles it.
- Does WHIP's Edmond deposit include RGB views, and under which licence?
- Are TotalCapture calibration files in the standard release (all evidence says yes; confirm on receipt).
- Is Captury's tracking (3DHP, WHIP GT) detector-based? Not answerable from the papers.
