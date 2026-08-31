# Retroreflective tape on trackers — David's idea, 2026-08-28 — **PARKED 2026-08-31 (David: back to markerless for now)**

Everything is ready to resume: marker-mode camera presets (`recorder/camera_ctl.py`),
blob/bar/ring estimators with tests (`markers.py`), the analysis tools
(`tools/tape_test.py`, `tools/tape_analyze_video.py`), and the v2 test protocol below.

**Idea.** In night mode the cameras flood the scene with IR from emitters
around the lens and film the return. Retroreflective tape sends light back
toward its source, so patches on the trackers appear as saturated blobs —
the passive-marker principle of Vicon/Qualisys, with the surveillance
camera's own illuminator as the ring light. No change to tracker hardware.

**What it would change**
- **Position without a pose estimator.** Blob centroids in two views →
  triangulated 3D position of each *tracker* (not a body joint), at
  pixel-centroid precision (sub-pixel → ~mm at 4 m with 1080p). Exp 04/06's
  structural detector bias does not apply to blobs.
- **Orientation from patterns.** Two or three patches per tracker in a known
  layout (e.g. 5 cm apart) give the tracker's heading directly: 2 mm
  triangulation error over 50 mm ≈ 2°; three non-collinear patches give
  full 3-DoF orientation → the mounting-independent **tracker** frame is
  measured, which is exactly what the IMU reports. That is the cleanest
  possible comparison (no bone-axis conventions at all).
- **Identification.** Which blob is which tracker: predicted from the
  SlimeVR skeleton (IMU + FK) and the HMD position, plus the per-tracker
  pattern geometry. Blobs also feed the beacon/fiducial logic for free.
- **The pose estimator becomes optional/secondary** — body context, occlusion
  handling, and the untaped parts (head, hands).
- Same idea is SlimeVR's "Constellation" (active IR LEDs + base stations);
  this is the passive, zero-hardware-change version.

**Risks / unknowns**
- Night mode only (B/W). Does the camera stay in night mode under room
  light, or can it be forced (ONVIF/API)? — ties to Q6b.
- Illuminator power and blob size at 3–5 m; auto-exposure reacting to
  bright blobs (blooming); other retroreflective objects in the room
  (shoes, jackets, safety strips).
- Tape on a curved case: reflection angle range (typical tape works to
  ~40–60° off-axis; corner-cube spheres are better) — pick patch placement so
  at least two patches face each camera in the common poses.
- Occlusion by the body (thigh trackers seated).

**Feasibility test (David, 10 minutes):** put 2–3 patches on one tracker at
measured separations, camera in night mode, stand at 3–5 m, capture a frame
from each camera. Look for saturated blobs; note blob diameter and whether
they survive ±45° tilt. Then I write the blob detector + triangulation and
check the triangulated patch-to-patch distance against the ruler (a
GT-free accuracy test).

## First test, 2026-08-28 (camera 2 "VR1", 1080p20, wide lens, marker mode: night vision Normal + IR LED on + targety=15)

- Recording: 90 s, David holding the taped tracker at several positions
  ~3–5 m from the camera, 10-s holds. Files: `tape-test/cam2_tape_143609.*`.
- **The tape retroreflects** — patches reach 255 (saturated) against a
  background of ~55–65 (≥4–5× contrast) — but the blobs are **small: radius
  ~1.5–2.5 px (3–6 px across)** at this distance with this wide-angle lens,
  and the tracker case edges and David's glasses produce saturated pixels of
  similar size. Detection is feasible but marginal; identification would
  lean on geometry/prediction.
- Static clutter: window/TV edges give many saturated pixels; masking the
  window and subtracting an empty-room background handles most of it.
- What would make it robust: larger patches (≥2×2 cm; the current ones look
  ~1 cm), microprismatic tape, testing at night (no daylight window),
  targety ≈ 10, cameras closer or a narrower lens (this one is very wide:
  few px per cm at 4 m). Two or three patches per tracker in a known layout.
- Camera control recipe now scripted (`recorder/camera_ctl.py`): night
  vision Normal (`setlampattrex&-lamp_mode=0`) + IR LED on
  (`setinfrared&-infraredstat=open`) + `setimageattr&-image_type=<active
  profile>&-targety=15`.

## Marker design v2 (2026-08-28, after test #1)
Test #1 used three 1.5×1.5 cm patches (one on top, two at the case edges —
already at the size limit). Measured scale ≈ 3 px/cm at 3–5 m with the wide lens.
- **Bar + dot per tracker** instead of three dots: a 4.5×1.5 cm bar across the
  case top gives a ~12 px blob whose elongation is a 3D line from two views
  (= tracker in-plane axis / heading); a small dot at one end fixes direction.
  Bar length / dot count can identify trackers.
- **Reflective band on the strap** (2 cm wide, David's idea "tape on myself"):
  a ring around the limb → ellipse in each view → limb axis (tilt) for free,
  larger and angle-tolerant. Running-safety bands are exactly this.
- Next test: night, window dark, targety≈10, one tracker with bar+dot and a
  strap band on the thigh; holds at 2/3/4/5 m + slow turn.
