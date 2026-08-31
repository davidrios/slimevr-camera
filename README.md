# slimevr-camera

Camera-assisted drift correction for SlimeVR IMU trackers.

**Thesis.** IMU trackers drift (dominantly in yaw, the one axis gravity cannot
pin down) and the error is motion-dependent, so it cannot be modelled away.
Cameras plus modern AI pose estimation have the opposite failure profile:
noisy, occlusion-prone, frame-by-frame, but *drift-free*. Fuse the two —
not in real time, but as an occasional high-confidence correction (every few
minutes, during moments the user is nearly still) — using 1–2 cheap cameras
and essentially zero user calibration.

This is a research project run collaboratively between David and Claude across
many sessions. Nothing here is a product yet.

**Where it stands (2026-08-31):** the product shape is an *automatic full
reset in familiar poses* (D33). The full markerless chain — calibration,
triangulation, observable-axis headings, pose templates, per-pose bias,
in-pose measurement — is coded and passed its first test on MoVi (chest/hip
3.5°, shins 4.7° MAE, inside the 5° budget). Next: the first own-room
recording session (exp 08, needs the beacon hardware). The retroreflective-
marker track is parked but ready (D35). Details in `STATE.md` and the report.

## How to navigate

| File | What it is |
|---|---|
| `STATE.md` | **Start here every session.** Current status, decisions made, open questions, next actions. |
| `CLAUDE.md` | Working conventions for the AI side (how to log, what not to assume). |
| `docs/00-problem.md` | The drift problem, what SlimeVR already does about it, why cameras. |
| `docs/01-approach.md` | Proposed architecture: what the camera must provide, when to correct, how to fuse. |
| `docs/02-research-agenda.md` | What we must ground in literature, ranked; candidate papers *to verify*. |
| `docs/03-questions.md` | Questions for David — answered ones move into `STATE.md` decisions. |
| `docs/04-lit-synthesis.md` | Grounded findings per research-agenda section (§A–§H), each traced to `literature/`. |
| `docs/05-report-2026-08-26.md` | Consolidated report with figures (`docs/figures/`); shareable page built by `tools/build-report.py`. |
| `docs/06-recorder-beacon.md` | Own-room recorder + sync-beacon design and session protocol. |
| `literature/` | One note per paper actually read, plus `index.md`. Only cite what's in here. |
| `data/` | Data collection plan, formats, and (later) captured runs. |
| `experiments/` | Numbered experiment folders, each with a `README.md` recording result. |
| `notes/` | Scratch thinking; may be wrong; may be deleted. |
| `src/slimevr_camera/` | Python package: skeleton/geometry/heading/pipeline core, `synth/`, `data/movi.py`, `recorder/`. |
| `firmware/beacon/` | Arduino/ESP32 sketch for the serial-driven sync LED. |
| `tools/` | `vulcanus-setup.sh` (GPU box), `build-report.py`. |

## Related local work

- `../drift-lab/` — rigid-bar rig measuring raw yaw drift; `DriftLogger.kt` patch in the server. Gives us **baseline drift numbers**.
- `../SlimeVR-Server/` — the fork we would integrate into. Relevant: `reset/`, `tracking/trackers/TrackerResetsHandler.kt`, `tracking/processor/skeleton/{IKSolver,Localizer,stayaligned}`.
- `../SlimeVR-Tracker-ESP/` — firmware (BNO085 / BMI270 builds).
