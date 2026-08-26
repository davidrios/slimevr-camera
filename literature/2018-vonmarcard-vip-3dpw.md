# Recovering Accurate 3D Human Pose in The Wild Using IMUs and a Moving Camera (VIP / 3DPW)

- **Authors / venue / year:** Timo von Marcard, Roberto Henschel, Michael J. Black, Bodo Rosenhahn, Gerard Pons-Moll — ECCV 2018, pp. 601–617
- **Link:** https://openaccess.thecvf.com/content_ECCV_2018/papers/Timo_von_Marcard_Recovering_Accurate_3D_ECCV_2018_paper.pdf (also https://virtualhumans.mpi-inf.mpg.de/papers/vonmarcardECCV18/vonmarcardECCV18.pdf). No arXiv version found.
- **Code:** No public VIP code (RobustCap 2023 confirms: "they do not provide their codes"). Dataset 3DPW at https://virtualhumans.mpi-inf.mpg.de/3DPW/ — non-commercial research licence (no redistribution). Paper says IMU data is part of the release; I could not confirm from the download page that raw per-sensor IMU orientations are in `sequenceFiles.zip` (needs registration + readme check).
- **Read depth:** full read (main paper PDF, text-extracted; supplementary not read)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

The only paper in §A that explicitly models **per-IMU heading (yaw) drift** and solves it from a single camera. Offline batch optimisation, sparse-ish IMUs, 1 camera with unknown pose — structurally the closest prior art to our plan. It also reports joint *angle* error (MPJAE), not just MPJPE.

## What they do

Sensors: 6–17 body IMUs (Xsens-class, orientation + acceleration) plus one hand-held moving phone camera (with its own IMU). Evaluated on TotalCapture with 13 IMUs and 1 static camera of unknown pose; 6-IMU variant also reported. Fully offline; all frames of a sequence are optimised jointly with Levenberg–Marquardt.

Pipeline (Sec. 4): (1) *Initialisation* — fit SMPL joint rotations to the IMU orientations frame by frame with a pose prior (Eq. 4); (2) *Assignment* — associate OpenPose 2D detections with the IMU-tracked person(s) via a binary quadratic program (Gurobi); (3) *Fusion* — minimise `E = E_ori + w_acc E_acc + w_img E_img + w_prior E_prior` (Eq. 12) over all SMPL poses Θ, camera poses Ψ and heading angles Γ.

**How yaw drift is handled (Sec. 3 "Heading Drift", Eq. 2):** the drift is modelled explicitly as a one-parameter rotation `R(γ_s)` about the *vertical* axis, **one angle per IMU sensor**, assumed constant over a sequence ("since the heading error commonly varies slowly"). It enters the measured bone orientation as `R̂_GB = R_GI · R_I'I(γ_s) · R_IS · R_BS` and is recovered jointly with the pose from the image reprojection term. Initial γ is obtained from a rough sensor-to-bone placement prior. The sensor-to-bone offset `R_BS` (our "mounting error") is calibrated from a known initial pose in the first frame (Eq. 1). Camera IMU orientation and acceleration also enter `E_ori`/`E_acc`.

## Key numbers (with table/figure reference)

Table 1, TotalCapture, 13 IMUs, 1 camera, ground-truth-aligned (global position/orientation removed):

| Variant | MPJPE mm | MPJAE ° |
|---|---|---|
| IT (IMU-only init, raw heading) | 55.0 | 16.9 |
| VIP-IT (IMU-only but using VIP's heading angles + init pose) | 28.2 | 12.0 |
| VIP (full) | 26.0 | 12.1 |
| VIP-IMU6 (6 IMUs + video) | 39.6 | 15.3 |
| VIP-2D (GT 2D keypoints) | 15.1 | 10.1 |
| VIP-Cam (GT camera pose) | 25.3 | 12.1 |

- MPJAE = geodesic distance of joint orientations for hips, knees, neck, shoulders, elbows.
- "VIP-IT is only slightly less accurate than VIP validating the importance of inferring drift and accurate initial pose" — i.e. **almost all of the gain from video comes from fixing per-sensor heading and mounting offsets**, not from per-frame image constraints. IMU-only error halves (55→28 mm) once headings are corrected.
- Estimating vs. knowing camera pose costs only 0.7 mm (25.3 vs 26.0).
- Weights (Sec. 5.1): `w_acc=0.2, w_img=1e-4, w_prior=0.006`.
- 2D→3D assignment precision 99.3 %, recall 92.2 % on 3DPW.

## What we can reuse / what to be careful about

- **Reuse the drift model verbatim:** one scalar yaw `γ_s` per tracker about world-up, solved from image evidence. This is exactly our `δψ_i`. Their finding that a per-sequence constant is enough (with Xsens IMUs, ~minutes) supports correcting slowly, in windows.
- **Reuse the calibration-from-known-pose idea:** `R_BS` from first-frame T/A-pose = SlimeVR mounting reset. Camera pose solved jointly from the person = our "extrinsics-from-reset".
- **Accuracy bar:** ~12° MPJAE *after* fusion, with GT 2D giving 10°. This is joint orientation error with 13 IMUs; it includes twist. Heading-only error is not reported separately — we must measure that ourselves.
- Careful: heading drift in their setting is attributed to magnetic disturbance (Xsens with mag). Our gyro-only drift is larger and time-varying, so "constant per sequence" needs windows, not whole sessions.
- Careful: whole-sequence LM optimisation with a body model; no code. We would re-implement a much smaller version (yaw-only unknowns, keypoints from a modern detector).
- 3DPW: usable as test data only if raw IMU orientations are actually in the release (unverified) and only non-commercially.

## Open questions this raises

- With 6 IMUs, error rises to 39.6 mm / 15.3° — how much of that is heading vs. pose ambiguity? (Table 1 does not split it.)
- How small can the "window" be for a per-sensor constant yaw before the estimate becomes noisier than the drift? Their sequences are ~minutes at 60 Hz.
- Does the released 3DPW `sequenceFiles` contain per-sensor IMU quaternions with the raw (drifting) heading, or only the VIP output? Check the readme after registering.
