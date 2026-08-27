# 04 — Real 2D detector heading bias on MoVi (in progress)

**Started:** 2026-08-26 · **Status:** first results (RTMPose-m body, subjects 1–3); wholebody / larger models running

## Hypothesis

Averaging inside a still window removes *noise* (exp 01) but not the
*systematic* keypoint offsets of a real 2D detector (hip placed low, ankle on
the shoe, shoulder on the deltoid…). Those shift lateral-axis headings when
the person is seen obliquely. Question: how large is that bias per bone,
per viewing angle, for an off-the-shelf detector on 2 real low-res cameras?
Target D19: ≤5° long bones, ≤8–10° feet/forearms.

## Data: MoVi (`literature/datasets-multiview-gt.md`)

- 2 hardware-synced calibrated FLIR cameras (PG1, PG2), 800×600 @ 30 fps —
  a two-camera pair like ours, at roughly 4–5 m.
- Qualisys marker GT → Visual3D **segment frames** (4×4 affine, 120 Hz):
  pelvis, thorax, head, thighs, shanks, feet, upper arms, forearms, hands.
  True per-bone orientation, so the same-axis heading comparison
  (`slimevr_camera.heading`) applies directly — no keypoint-definition
  ambiguity on the GT side.
- 21 motions per subject incl. `dancing_rm`, `sitting_down`,
  `cross_legged_sitting`, `stretching`, `walking` — several are natural
  "still-ish" or constrained-motion regimes.
- Pilot: subjects 1–5, round F (≈3 GB video + 1.8 GB GT). Licence:
  non-commercial research; data stays local (`data/movi/`, gitignored).
- Note: the 2020 README says access requires an institutional Dataverse
  account; in 2026 the API serves the files directly (files unrestricted).
  Terms still apply.

## Plan

1. Verify calibration convention by reprojecting markers onto a frame
   (MATLAB row-vector convention, transposed K, radial distortion k1,k2).
2. Run RTMPose (rtmlib, body/wholebody, CPU or GPU) on both views for the
   pilot subjects; cache 2D keypoints + scores.
3. Undistort, triangulate (DLT) → 3D joints; derive per-bone axis
   (`heading.estimate_all`) and compare with the GT segment frame's same
   axis: error per frame, per bone.
4. Split into still windows (from GT angular speed) vs. moving; report
   **mean (bias) and std (noise)** of heading error per bone, and bias vs.
   body yaw relative to the camera baseline.
5. Repeat for a second detector (wholebody for toes; ViTPose if easy) and
   for single-view + bone-length lifting as the 1-camera baseline.

## Open items

- GPU: this machine has only the RX 9060 XT (Q18). rtmlib on CPU is fine
  for 800×600 pilot volume.
- Kinematic-tree "waist" has no GT segment in MoVi (pelvis→thorax only);
  evaluate hip + chest and note waist as interpolated.

## Interim results (2026-08-26, RTMPose-m "body-balanced", subjects 1–3, 40k bone-frames)

Method: detector 2D → undistort → DLT triangulation → per-tracker axis
(`heading.estimate_all`) → floor heading vs the **same fixed local axis of the
verified Visual3D segment frame** (`SEG_LOCAL_AXIS`, fitted from marker joint
centres). "Reset-referenced" = per-subject median subtracted (what a full
reset absorbs). Upper arms excluded: Visual3D's upper-arm frame has no stable
twist, so no ground truth for that axis.

| bone | per-frame sd (still) | **1-s rolling-mean sd** | 1-s p95 | reset-ref. bias |
|---|---|---|---|---|
| chest | 6.4° | **5.1°** | 10.7° | 0.8° |
| hip | 8.3° | **7.2°** | 14.8° | 0.6° |
| shin L / R | 7.8 / 7.5° | **6.1 / 5.3°** | 11.8 / 10.6° | 0.4° |
| thigh L / R | 14 / 18° | **11.4 / 10.3°** | 29 / 22° | ±2° |

Cross-checks: detector-triangulated knees/ankles/elbows are within 25–35 mm
of marker joint centres (calibration, sync, undistortion are right);
per-subject constant offsets are small (< 5°) except thighs.

### Finding: the error is not white noise

Averaging 30 frames barely reduces it (per-frame sd 6–14° → 1-s mean sd
5–11°). The detector's heading error is **slowly varying and pose-dependent**
(e.g. thigh −30° in `cross_legged_sitting`, hip +9° in a frontal-facing
window). Experiment 01's assumption — window averaging removes the noise —
holds for pixel jitter, **not** for a real detector. With this detector at
800×600 / 4.5 m, **the 5° budget is not met** for hips/thighs; chest and
shins are borderline.

Not yet controlled: still windows are rare in MoVi (few subjects stand
still), so window stats have n=2–18; only 3 subjects; low resolution.
Pending: wholebody-performance and body-performance (RTMPose-x) runs, all 5
subjects, 5-s windows, per-yaw-bin bias with more data.

### What this implies for the project (tentative)

- Fine-tuning the detector for our regime (D28) is not optional polish —
  it is the difference between meeting the budget or not. Pose-dependent
  heading bias is exactly what a heading-aware loss on our own data would
  target.
- The correction should use a *longer* observation than one still window
  where possible, and weight bones by their measured reliability (chest/shin
  > hip > thigh).
- Two views at 800×600 from 4.5 m is a pessimistic setup; resolution and
  baseline are cheap to improve.

## Update: 5 subjects, and a bigger detector (2026-08-26)

**All 5 pilot subjects, body-balanced** (47k bone-frames, 66 still windows):
1-s rolling-mean sd — chest 5.1°, hip 7.5°, shins 8.0 / 9.6°, thighs 12.5 /
12.9°. Same picture as 3 subjects; window-level MAE chest 3.6°, hip 5.7°
(n=22 / 33 windows).

**Model size does not fix it.** Subjects 1–2, 1-s rolling-mean sd,
RTMPose-m "body-balanced" → RTMPose-x "wholebody-performance":
chest 4.9 → 4.65°, hip 7.4 → 6.7°, shin L/R 6.7/5.2 → 6.3/5.2°,
thigh L/R 10.4/7.8 → 11.2/8.0°. Within noise. → The pose-dependent heading
error is **structural to how these detectors place joints**, not a capacity
problem. Fine-tuning on our regime with a heading-aware objective is the
lever, not a bigger backbone.

**Feet are the best bone when still** (wholebody gives toes): still-frame
per-frame sd 4.9 / 2.4°, MAE 1.9 / 1.6° (L / R); 1-s rolling sd 7.1 / 5.9°
when moving is included. Heel→toe is a long, nearly horizontal, well-seen
axis. This reverses the synthetic-era assumption (D19) that feet would be the
hard case: **feet and chest are the most reliable heading sources; thighs the
least.**

## Update 2026-08-27: all three detectors on 5 subjects (run on vulcanus)

1-s rolling-mean sd (°), reset-referenced, 5 subjects:

| bone | RTMPose-m body-balanced | RTMPose-x body-performance | RTMPose-x wholebody-performance |
|---|---|---|---|
| chest | 5.1 | 5.1 | 5.2 |
| hip | 7.5 | 7.0 | 7.2 |
| shin L / R | 8.0 / 9.6 | 7.9 / 10.0 | 8.3 / 10.1 |
| thigh L / R | 12.5 / 12.9 | 13.2 / 13.5 | 12.5 / 12.9 |
| foot L / R | — | — | 10.8 / 5.9 (moving incl.); still MAE ~1.7 |

Confirms on the full pilot: **detector size is irrelevant to heading error**;
the bias is structural. Foot L's larger moving-frame sd comes from
occlusion/side view in some motions — feet are excellent when still.

### Seated / idle-like motions (subjects 1–2, 1-s mean |error|, wholebody)

| bone | sitting_down | cross_legged_sitting | phone_talking | checking_watch |
|---|---|---|---|---|
| chest | 1.9 | 3.4 | 4.5 | 3.6 |
| feet L / R | 1.9 / 2.2 | 5.8 / 6.5 | 0.7 / 1.3 | 1.2 / 1.1 |
| hip | 6.4 | 8.8 | 5.8 | 7.2 |
| shin L / R | 3.4 / 2.0 | 5.5 / 5.5 | 5.4 / 3.3 | – / 4.9 |
| thigh L / R | 10.1 / 4.6 | 16.6 / 11.6 | 3.5 / 6.6 | – / 5.3 |

For the "automatic full reset in a familiar pose" scope (D33): chest and
feet are inside budget in seated/idle poses without any calibration; hips
need the per-pose bias learned in the trusted window (within-pose residual
~2°, exp 05); cross-legged sitting hides the feet/knees and is the hardest
seated pose.
