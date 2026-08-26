# CasCalib: Cascaded Calibration for Motion Capture from Sparse Unsynchronized Cameras

- **Authors / venue / year:** James Tang, Shashwat Suri, Daniel Ajisafe, Bastian Wandt, Helge Rhodin (UBC / Linköping / Bielefeld) — IEEE FG 2024
- **Link:** https://arxiv.org/abs/2405.06845
- **Code:** https://github.com/jamestang1998/CasCalib — **no LICENSE file** (GitHub API: license null). Python 3.8, PyTorch; PyTorch3D needed for multi-view bundle adjustment. Inputs: frames + 2D pose JSON (MMPose-COCO or AlphaPose). Outputs: focal, ground-plane normal + offset, 3D ankles, time offsets, extrinsics.
- **Read depth:** skimmed (HTML paper + README)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

The only open-source pipeline found that does the whole §D chain from people alone: per-camera **focal + ground plane** (single view, §D(b)), then **time sync + extrinsics** across sparse cameras (§D(a),(d)). Designed for exactly "a few consumer cameras, no sync, no checkerboard".

## What they do

Cascade: (1) single-view: assume people stand upright with constant height h; ankle–shoulder pairs give a DLT for focal length and ground-plane normal, RANSAC on shoulder reprojection + angle consistency. (2) time sync: 1-D search aligning ankle-distance-over-time curves between cameras. (3) rotation: 2-D search aligning the ankle point clouds on the ground plane, then ICP. (4) bundle adjustment over everything. 2D detector: HRNet via mmpose.

## Key numbers (with table/figure reference)

(From the HTML text; not table-by-table verified.) Focal error ~11 % on vPTZ; sync error 4–11 frames when the focal is itself predicted (better with GT focal); rotation error **1.82°** on EPFL Terrace; translation error reported as a large squared quantity (138 m² avg) — i.e. translation is the weak part. Datasets: Human3.6M (4 cams, 1 person), EPFL Terrace/Laboratory (4 cams), vPTZ (3–4 cams). Degrades beyond ~15 px keypoint noise.

## What we can reuse / what to be careful about

- Reuse: the code as a baseline to run on our own two-camera footage within a day; the single-view ground-plane stage is what we need even with one camera.
- Careful: no licence → cannot redistribute; fine for experiments. Constant-height assumption is trivially satisfied for us (one known user, SlimeVR knows the height) — we could feed h directly instead of assuming a population mean. Periodic motion (walking in circles) breaks their sync; we can use IMU-derived motion signals for sync instead. Translation accuracy is poor; we should not rely on it for metric camera position — use bone lengths / HMD.

## Open questions this raises

- How does the ground-plane normal accuracy compare with taking gravity from the IMUs and only solving camera yaw + height?
- Their sync from ankle distance curves vs. our option of correlating camera-observed joint speed with IMU angular rate.
