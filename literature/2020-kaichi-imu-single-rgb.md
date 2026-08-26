# Resolving Position Ambiguity of IMU-Based Human Pose with a Single RGB Camera

- **Authors / venue / year:** Tomoya Kaichi, Tsubasa Maruyama, Mitsunori Tada, Hideo Saito — Sensors 20(19):5453, 2020 (MDPI, open access)
- **Link:** https://doi.org/10.3390/s20195453 ; PMC7582626
- **Code:** none mentioned.
- **Read depth:** abstract + skimmed (via PMC full-text extraction of setup and tables; figures not inspected)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Online fusion of **13 IMUs + one RGB camera** on TotalCapture. Included because it is the only other "single camera + body IMUs" paper found, but it solves *global position* (depth ambiguity) using foot-ground contact + image constraints; **orientation stays IMU-driven and heading drift is not corrected**. Mainly a negative result for us: camera did not improve joint orientation.

## What they do

Dense (13) IMUs on head, sternum, pelvis, limbs, feet; one fixed RGB camera (also an 8-camera variant). Online — uses current and previous frames only. A cost with a ground-contact term that "fuses IMU acceleration and positional measurement from the camera" to fix the root position, plus image-based terms to handle 2D detection failures. Orientation of segments comes from the IMUs as-is.

## Key numbers (with table/figure reference)

- Table 1 (single camera, 15 TotalCapture test scenes): mean 3D position error 13.5 cm (full method); orientation error **8.83°** vs. **8.75° IMU-only** — i.e. no orientation gain from the camera.
- Table 2 (8 cameras, 5 scenes): orientation error 6.17° (Malleson et al. 2017: 6.3°).

## What we can reuse / what to be careful about

- The 8.75° IMU-only orientation error on TotalCapture (13 Xsens IMUs, with magnetometer, short sequences) is a useful reference for what "good" IMU segment orientation looks like in that dataset.
- Careful: does not attempt heading correction, so it does not tell us what a camera can do for yaw. Position-only fusion is not our problem.
- Careful: read depth is skim; numbers come from an automated extraction of the PMC page and should be re-checked against the PDF tables before being quoted elsewhere.

## Open questions this raises

- None specific; superseded by RobustCap/DiffCap for the monocular setting.
