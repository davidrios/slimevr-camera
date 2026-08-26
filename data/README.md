# Data

## What we need to capture (first experiments)

Synchronized:
- Tracker **raw** quaternions (`getRawRotation()`, as in drift-lab's
  `DriftLogger`, 10–100 Hz) plus the server's adjusted rotation and skeleton
  joint positions, with timestamps.
- Reset events (full/yaw/mounting) with timestamps — these mark the
  high-trust intervals.
- Camera video (or, once we have a model chosen, the extracted keypoints/poses
  per frame with confidences), with frame timestamps on the same clock.
- Metadata: tracker assignment, IMU type, firmware, mag on/off, user bone
  lengths, camera model/resolution/fps, camera placement description.

## Clock sync

TBD. Options: server timestamps both streams if the camera is captured by the
same machine; otherwise a visible/audible sync event (clap + tap-on-tracker,
which the firmware already detects via `TapDetection`).

## Format

Proposal: one directory per run `data/runs/<stamp>_<label>/` with
`imu.csv`, `events.json`, `meta.json`, `video.mp4` (gitignored) and
`poses/*.npz` (derived, committed if small).

## Privacy

Video stays local. Only derived data is shared. Community donation design is
in `docs/01-approach.md`.
