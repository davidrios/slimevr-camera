# Multi-Camera Self-Calibration in Sports Motion Capture: Leveraging Human and Stick Poses

- **Authors / venue / year:** Fan Yang, Changsoo Jung, Ryosuke Kawamura, Hon Yung Wong — arXiv 2604.17567 (April 2026), CC0
- **Link:** https://arxiv.org/abs/2604.17567 ; project https://fandulu.github.io/sport_stick_multi_cam_calib/
- **Code:** https://github.com/fandulu/sport_stick_multi_cam_calib — MIT (GitHub API). Content of the repo not inspected (may be benchmark data only — unverified).
- **Read depth:** skimmed (HTML: method, main results table)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Adds a **rigid object of known length** (bat/club/stick) to human keypoints for multi-camera extrinsics + metric scale. Analogue for us: a VR controller or the HMD as a rigid known-geometry object, or simply known bone lengths. Also reports a comparison against human-pose-only methods, which is a useful accuracy reference.

## What they do

Synchronised multi-view video, intrinsics known. Detect 2D human keypoints + stick endpoints (YOLOv11 fine-tuned). Jointly estimate extrinsics, 3D keypoint trajectories and global scale; the stick's known length fixes scale and its rigidity adds constraints. Evaluated on synthetic data for golf/baseball/hockey/kendo with 3–10 cameras; real-world qualitative validation.

## Key numbers (with table/figure reference)

- Main table (synthetic): their method rotation **0.020°**, translation **0.1 cm**; human-pose-only baselines 0.22–0.27°, 3–7 cm; learning-based baselines 0.08–0.19°, 10–12 cm; 77 % / 86 % better than an ArUco baseline. All synthetic → optimistic.
- No two-camera result.

## What we can reuse / what to be careful about

- Reuse: the accuracy *ordering* — a rigid known-length object improves extrinsics ~10× over people alone; our HMD/controller or known-bone-length skeleton plays that role.
- Careful: synthetic numbers with perfect-ish detections; 3+ cameras; synchronised.

## Open questions this raises

- Is a SlimeVR skeleton with known bone lengths (many rigid segments) as good as a stick? Probably better in principle since it has more segments, worse in practice since joints are soft.
