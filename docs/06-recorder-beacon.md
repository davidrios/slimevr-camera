# 06 — Own-room recorder and sync beacon (design, 2026-08-27)

Purpose: capture licence-clean data in David's room — 2 RTSP cameras, 11
trackers, Quest 3 — with every camera frame stamped on the tracker clock.
This is both the evaluation ground for the automatic full reset (D33) and
the training set (D34).

## Clock architecture (D17, refined)

- **One clock: the recording PC's wall clock.** SlimeVR's `DriftLogger` logs
  raw tracker quaternions with `wall_ms` (server `currentTimeMillis`) at
  100 Hz; the BVH recorder logs the processed skeleton at 100 fps. If the
  recorder runs on the same PC as the server, no synchronisation is needed
  at all; on a second machine, LAN NTP (≈1 ms) is plenty.
- **The beacon is driven by that PC over USB serial** (`firmware/beacon/`,
  any Arduino/ESP32; `'1'`/`'0'` toggles the LED, echo carries `micros()` for
  latency checks). The host (`recorder/beacon.py`) logs the wall time of
  every transition it commands (USB latency ~1–2 ms). No clock, no WiFi, no
  NTP on the microcontroller.
- **Code:** 200 ms symbols (≥ 3 frames at 15 fps); each 7.2 s word = sync
  `1110` + Manchester-coded 16-bit counter (a transition every ≤ 2 symbols
  lets the decoder track fps drift; the counter makes any window unique).
- **Cameras** record with `ffmpeg -c copy` (`recorder/capture.py`): no
  re-encode, original frames, packet-arrival PTS as a fallback.
- **Decoder** (`recorder/decode.py`): auto-locates the blinking pixel
  (temporal variance), binarizes, cross-correlates against the host log for
  the absolute offset, then least-squares fits `wall_s = a·frame + b` on
  transition times. Verified on a synthetic video with unknown start and a
  1.2 % fps error: absolute time within 20 ms, residual < 25 ms
  (`tests/test_beacon.py`). Sub-frame accuracy is available if ever needed
  (exposure-weighted transitions); still-moment corrections don't need it.
- **Bonus:** the LED blob's pixel position is a fixed fiducial per camera
  (camera-bump detection; one known world point if measured).

## LED choice

Visible LED works in day and night mode; 850 nm IR only in night mode (day
IR-cut filter). Ship visible + optional IR in parallel; keep it dim enough
not to bloom (a 3 mm LED behind a diffuser, pointed at the cameras).

## What a session produces (`data/runs/<stamp>_<label>/`)

| file | source | clock |
|---|---|---|
| `cam1.mkv`, `cam2.mkv` + `.start.json` | `capture.py` | frame → wall via decoder |
| `cam1.times.csv`, `cam2.times.csv` | `decode.py` | wall_s per frame |
| `beacon.csv` | `beacon.py` | wall_s per LED transition |
| `driftlog_*.csv` + `.meta.json` | server `DriftLogger` (raw rotations, 100 Hz) | wall_ms |
| `*.bvh` | server BVH recorder (processed skeleton) | 100 fps from server |
| `events.json` | manual: reset times, pose labels ("standing reset", "seated idle") | wall |
| `meta.json` | trackers, assignments, camera models/placement, user bone lengths | — |

Still to confirm in the server: whether `DriftLogger` records the HMD/controller
poses (position + rotation) — they anchor camera extrinsics (D15). If not, a
one-line addition to the logger.

## Session protocol v1 (ties to D33)

1. Beacon on, cameras recording, DriftLogger + BVH on. Warm up 10 min.
2. Standing full reset in view of both cameras; hold 10 s. Mark event.
3. Sit in the habitual relaxed pose; hold 10 s. Mark ("seated idle").
4. Normal VR-style activity 5–10 min (talk, gesture, sit/stand, walk a bit).
5. Return to the seated idle pose; hold 10 s. Mark. Repeat 3–5 a few times.
6. Occasionally a full standing reset (mark) — gives fresh truth intervals.
7. End with a dance-like burst, then a reset (the "user resets after heavy
   activity" case).

Everything after each reset is IMU-trusted for minutes → pseudo-labels for
headings; every return to a marked pose is a test of the familiar-pose
detector; the beacon gives frame-accurate alignment throughout.

## Hardware shopping list

- Wemos D1 mini (David has spares) — see `firmware/beacon/README.md` for wiring (LED on D1/GPIO5).
- 1× visible LED (+ optional 850 nm IR LED), 2 resistors, small diffuser.
- 2 RTSP cameras (have), mounted ~2–3 m high at ±30–45° in front.

## Camera 1 facts (probed 2026-08-28, ONVIF at http://192.168.15.60:8080/)

- Firmware `V32.1.21.16.3-20240416`, model string `C6F0SgZ3N0PmL2`, "IPCAM"
  (HiSilicon/hi3510-style CGI, `/tmpfs/auto.jpg` snapshot). PTZ service present.
- Main stream **1920×1080 H.264 @ 20 fps**: `rtsp://192.168.15.60:554/11`
  (works **without credentials**); second stream `/12`. Audio G.711.
- ONVIF imaging exposes only brightness / "manual exposure"; IR-cut, IR LED
  and exposure/gain are in the CGI API (`/cgi-bin/hi3510/param.cgi?cmd=…`,
  e.g. `getinfrared`, `setinfrared&-infraredstat=open|close|auto`,
  `getimageattr`), which needs the web login (HTTP 401 otherwise). Camera
  clock is set to China Standard Time — irrelevant, the beacon supplies time.
- Consequence for the beacon code: at 20 fps a 200 ms symbol is 4 frames — fine.

### Camera control (verified 2026-08-28, `recorder/camera_ctl.py`)
- CGI writes need `-image_type=0` (`cmd=setimageattr&-image_type=0&-targety=15`); without it every set fails. Admin account required.
- **`targety` (AE target luminance) is the effective exposure lever**: 60 → 15 drops the frame mean from ~90 to ~32 while retroreflective/saturated regions stay at 255. `shutter` (1–10000) and `gc` ceilings had no visible effect in daylight (AE stays within limits); `aemode=1` sets `ae=64`.
- IR LED: `setinfrared&-infraredstat=open|close|auto` works; night mode (`night=on`, B/W) is already active under daylight on this unit.
- Snapshot `/tmpfs/auto.jpg` needs basic auth; RTSP `/11` (1080p20) and `/12` need none.
- Security: this firmware returns all account passwords in clear text to any authenticated user (`getuserattr`) and RTSP is unauthenticated — LAN only.
- Presets: `python -m slimevr_camera.recorder.camera_ctl marker [targety]` / `normal`.
