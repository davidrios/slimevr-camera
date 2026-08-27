# 02 — Research agenda

Status 2026-08-27: §A, §B, §C, §D, §G (+§G2 multi-view marker-GT datasets)
and §H are grounded — see `04-lit-synthesis.md` and `literature/index.md`
(37 notes). §E (consumer IMU drift) is covered by drift-lab's own
measurements; §F (quantisation / CPU inference) is deferred until a model
is chosen. The candidate lists below are kept as written for the record.

## A. IMU + video fusion for human pose (closest prior art)  — priority 1

Question: has anyone fused sparse body IMUs with 1–2 RGB cameras for
drift-free pose, and what accuracy do they report on heading / global
orientation?

Candidates (unverified):
- von Marcard et al., "Recovering accurate 3D human pose in the wild using
  IMUs and a moving camera" (VIP, ECCV 2018) — produced the 3DPW dataset.
  Sparse IMUs + monocular video, offline optimization. Very close to our
  setting.
- Zhang et al., "Fusing wearable IMUs with multi-view images for human pose
  estimation" (CVPR 2020).
- Pan et al., "Fusing monocular images and sparse IMU signals for real-time
  human motion capture" (RobustCap, SIGGRAPH Asia 2023).
- Any 2024–2026 follow-ups (search: "IMU" + "monocular" + "human pose" +
  "fusion", CVPR/ICCV/ECCV/SIGGRAPH/3DV).

## B. Monocular / body-model pose estimation that outputs joint rotations — priority 1

Question: which models output per-joint *rotation* (SMPL/SMPL-X pose
parameters), how accurate is rotation error (MPJAE, not just MPJPE), and
specifically how bad is twist about the bone axis? Do they run on CPU at all (for end users)? CUDA is fine for research.

Candidates: HMR2.0 / 4DHumans, HybrIK, WHAM (world-grounded, uses camera
motion), TRAM, SMPLer-X, TokenHMR, MotionBERT (lifting), PromptHMR / 2025
successors. Also video-temporal ones (VIBE, TCMR, GLoT) since we have video
not frames.

## C. Sparse-IMU-only pose (what the IMU side of the literature does about drift) — priority 2

DIP (Huang 2018), TransPose (Yi 2021), PIP (Yi 2022), TIP, IMUPoser, DiffusionPoser,
PNP (2024). Relevant for: how they handle yaw drift in practice, what they
report as inherent error, and whether their learned priors could replace
Stay Aligned's hand-written ones.

## D. Camera extrinsic self-calibration from humans — priority 2

"Human as calibration object": estimating multi-camera extrinsics from 2D
keypoint correspondences, and single-camera extrinsics + floor from body
priors / bone lengths / gravity. Search terms: "human pose camera calibration",
"extrinsic calibration from human keypoints", "floor plane estimation
monocular human".

## E. Yaw drift characterization of consumer IMUs — priority 2

To set the bar. Also overlaps `../drift-lab/`. Gyro scale factor,
g-sensitivity, cross-axis; papers on BNO085/BMI270-class parts; any
SlimeVR/community measurements.

## F. Quantization / fine-tuning of pose models — priority 3

Later. Only once B has picked a model family. Target is end-user CPU/iGPU, not our 3090.

## G. Datasets we could evaluate on — priority 2

3DPW (IMU + video + SMPL ground truth) is potentially exactly our test set.
Also TotalCapture (IMU + multi-view), AMASS/DIP-IMU (IMU only), Human3.6M.

## How to run a verification pass

For each candidate: find the actual paper (arXiv/venue page), read abstract +
method + results tables, check for code and backend support, write
`literature/YYYY-author-short.md`, update `index.md`, and update the relevant
section in `docs/` with what was learned, deleting the "unverified" caveat.
Prefer primary sources over blog posts.

## H. Synthetic training/eval data from mocap + game-engine rendering — priority 2 (added 2026-08-26, David's suggestion)

Question: can we generate unlimited (video, IMU-with-drift, ground truth)
triples by taking motion (AMASS mocap; generative motion models such as MDM /
MotionGPT-class for arbitrary VR-like movement), simulating IMUs on it (as
DIP/TransPose/PIP/PNP do), and rendering it from two virtual cameras in a game
engine (BEDLAM, CVPR 2023, does exactly this in Unreal with SMPL-X GT; also
SynBody, AGORA)? Sub-questions: licences of AMASS sub-datasets and BEDLAM for
a project that ships a consumer model; adding a VR headset + controllers to
the avatar; domain gap of RTMPose-class detectors on renders vs real RTSP
footage. Candidates (unverified): BEDLAM (Black et al. 2023), AMASS (Mahmood
2019), MDM (Tevet 2022), PNP's IMU synthesis code, SynBody.
