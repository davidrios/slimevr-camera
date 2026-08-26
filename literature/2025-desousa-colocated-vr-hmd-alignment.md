# Co-Located VR with Hybrid SLAM-based HMD Tracking and Motion Capture Synchronization

- **Authors / venue / year:** Carlos A. Pinheiro de Sousa, Niklas Gröne, Mathias Günther, Oliver Deussen (U. Konstanz) — GI VR/AR Workshop 2025 (arXiv 2509.06582)
- **Link:** https://arxiv.org/abs/2509.06582
- **Code:** https://github.com/niklas-groene/Co-Located-VR — no LICENSE file (GitHub API: license null); Unity project, unverified contents.
- **Read depth:** skimmed (HTML: alignment section, results)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Documented case of the §D(c) idea in reverse: a Quest 2 HMD (with reflective markers) is tracked by an external system, and the fixed transform between the HMD's own 6-DoF frame and the external frame is solved from the two trajectories. Same math as "camera sees HMD → solve camera pose", with the camera-side pose replaced by mocap.

## What they do

Record HMD poses in its inside-out (SLAM) frame and in the OptiTrack frame simultaneously. Umeyama similarity alignment of the two trajectories for initialisation, then least-squares refinement of the fixed transform: min Σ_t ‖T_eye^W(t) − T_mocap^W(t)·T_mocap→eye‖² over all timesteps (a hand-eye / AX=XB-style problem solved directly on poses). After alignment, users run on inside-out tracking only; mocap is used to re-align when drift exceeds a threshold.

## Key numbers (with table/figure reference)

- Absolute trajectory error after alignment: **3.1–4.9 cm RMSE** single user, ~5.2 cm multi-user; no rotation error reported.
- Sample count not stated in the extracted text (whole trajectories).

## What we can reuse / what to be careful about

- Reuse: the exact objective for "HMD as moving fiducial": if a camera can measure the HMD's 6-DoF pose per frame (or even just its 3D position via a pose model's head keypoint), the same Umeyama + refinement gives camera↔SteamVR extrinsics. Position-only correspondences (head keypoint vs. HMD position over a trajectory) already determine R,t if the trajectory is non-planar-ish or gravity is known.
- Careful: cm-level ATE includes SLAM drift; not a camera-calibration accuracy figure. Marker-based mocap, not RGB.

## Open questions this raises

- Nobody in the papers found solves a *camera's* pose from an HMD seen in RGB; the closest documented practice is the mixed-reality-capture calibration tools (see tool-liv-unreal-mrc-calibration.md).
