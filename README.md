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

## How to navigate

| File | What it is |
|---|---|
| `STATE.md` | **Start here every session.** Current status, decisions made, open questions, next actions. |
| `CLAUDE.md` | Working conventions for the AI side (how to log, what not to assume). |
| `docs/00-problem.md` | The drift problem, what SlimeVR already does about it, why cameras. |
| `docs/01-approach.md` | Proposed architecture: what the camera must provide, when to correct, how to fuse. |
| `docs/02-research-agenda.md` | What we must ground in literature, ranked; candidate papers *to verify*. |
| `docs/03-questions.md` | Questions for David — answered ones move into `STATE.md` decisions. |
| `literature/` | One note per paper actually read, plus `index.md`. Only cite what's in here. |
| `data/` | Data collection plan, formats, and (later) captured runs. |
| `experiments/` | Numbered experiment folders, each with a `README.md` recording result. |
| `notes/` | Scratch thinking; may be wrong; may be deleted. |
| `tools/` | Scripts. |

## Related local work

- `../drift-lab/` — rigid-bar rig measuring raw yaw drift; `DriftLogger.kt` patch in the server. Gives us **baseline drift numbers**.
- `../SlimeVR-Server/` — the fork we would integrate into. Relevant: `reset/`, `tracking/trackers/TrackerResetsHandler.kt`, `tracking/processor/skeleton/{IKSolver,Localizer,stayaligned}`.
- `../SlimeVR-Tracker-ESP/` — firmware (BNO085 / BMI270 builds).
