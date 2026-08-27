"""End-to-end beacon test on a synthetic video: blinking blob rendered at an
unknown offset and slightly wrong fps; decoder must recover per-frame time."""
import csv, json
import cv2, numpy as np
from slimevr_camera.recorder.beacon import SYM_S, level_at
from slimevr_camera.recorder.decode import frame_times


def test_decode_recovers_time(tmp_path):
    rng = np.random.default_rng(0)
    T0 = 1_700_000_000.0                     # host run start (wall)
    # host log: transitions of level_at
    log = tmp_path / "beacon.csv"; last = None
    with open(log, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["wall_s", "mono_s", "level", "counter", "symbol_idx"])
        for n in range(int(120 / SYM_S)):
            lvl = level_at(n * SYM_S)
            if lvl != last: w.writerow([f"{T0 + n * SYM_S:.6f}", 0, lvl, 0, 0]); last = lvl
    # video: true start T0+13.37 s, true fps 24.7 (nominal 25), 60 s, blob at (100,80), noise + drift
    true_start, true_fps, n_frames = T0 + 13.37, 24.7, 60 * 25
    vid = tmp_path / "cam.mkv"; wr = cv2.VideoWriter(str(vid), cv2.VideoWriter_fourcc(*"MJPG"), 25, (160, 120))
    for i in range(n_frames):
        t = true_start + i / true_fps
        img = (40 + 20 * rng.random((120, 160, 3))).astype(np.uint8)
        if level_at(t - T0): cv2.circle(img, (100, 80), 4, (255, 255, 255), -1)
        wr.write(img)
    wr.release()
    (tmp_path / "cam.start.json").write_text(json.dumps(dict(wall_s=true_start + 2.0)))   # start marker 2 s late (ffmpeg spin-up)
    fit = frame_times(vid, log, tmp_path / "cam.start.json", xy=None, fps_nominal=25.0)
    assert abs(fit["fps"] - true_fps) < 0.05, fit
    assert abs(fit["b"] - true_start) < 0.02, fit          # absolute time within 20 ms
    assert fit["resid_ms"] < 25, fit
    assert abs(fit["blob_xy"][0] - 100) <= 4 and abs(fit["blob_xy"][1] - 80) <= 4
