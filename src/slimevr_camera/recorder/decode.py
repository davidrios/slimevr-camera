"""Recover per-frame wall-clock time for a recorded camera from the beacon.

1. brightness(frame) at the LED blob (given pixel, or auto: the pixel whose
   temporal brightness has the strongest ~SYM_S-scale square-wave energy);
2. binarize (adaptive threshold);
3. cross-correlate the binary sequence against the host log's level(t)
   over candidate offsets to find the absolute alignment;
4. least-squares fit  wall_s = a * frame_idx + b  on transition times
   (absorbs fps drift); report residual.
"""
from __future__ import annotations

import csv
from pathlib import Path

import cv2, numpy as np

from .beacon import SYM_S


def load_host_log(path: Path):
    rows = list(csv.DictReader(open(path)))
    t = np.array([float(r["wall_s"]) for r in rows]); lvl = np.array([int(r["level"]) for r in rows])
    return t, lvl


def host_level(t_query: np.ndarray, t_log: np.ndarray, lvl_log: np.ndarray) -> np.ndarray:
    idx = np.searchsorted(t_log, t_query, side="right") - 1
    out = np.where(idx >= 0, lvl_log[np.clip(idx, 0, len(lvl_log) - 1)], 0)
    return out


def blob_brightness(video: Path, xy: tuple[int, int] | None, radius: int = 4, max_frames: int | None = None):
    cap = cv2.VideoCapture(str(video)); vals = []; frames_for_auto = []
    n = 0
    while True:
        ok, img = cap.read()
        if not ok or (max_frames and n >= max_frames): break
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if xy is None:
            frames_for_auto.append(cv2.resize(g, (g.shape[1] // 4, g.shape[0] // 4)))
        else:
            x, y = xy; vals.append(float(g[max(0, y - radius):y + radius + 1, max(0, x - radius):x + radius + 1].mean()))
        n += 1
    cap.release()
    if xy is None:
        S = np.stack(frames_for_auto).astype(np.float32)          # (T, h, w) at 1/4 resolution
        # temporal variance after removing the per-pixel mean: a blinking LED dominates
        score = (S - S.mean(0)).var(0)
        y, x = np.unravel_index(int(np.argmax(score)), score.shape)
        xy = (int(x) * 4 + 2, int(y) * 4 + 2)
        vals, _ = blob_brightness(video, xy, radius, max_frames)
        return vals, xy
    return np.array(vals), xy


def binarize(v: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(v, 10), np.percentile(v, 90)
    return (v > (lo + hi) / 2).astype(int)


def align(b: np.ndarray, fps_nominal: float, start_wall_guess: float, t_log, lvl_log, search_s: float = 60.0, step_s: float = 0.01):
    """Return (a, b, corr) with wall_s = a*frame + b, found by correlation over start offsets."""
    frames = np.arange(len(b)); best = (None, -1)
    for off in np.arange(-search_s, search_s, step_s):
        t = start_wall_guess + off + frames / fps_nominal
        h = host_level(t, t_log, lvl_log)
        c = np.mean((2 * b - 1) * (2 * h - 1))
        if c > best[1]: best = (off, c)
    off = best[0]
    # refine: transitions in video vs host transitions (nearest within a symbol)
    tv = np.flatnonzero(np.diff(b) != 0) + 0.5                      # frame index of transition (between frames)
    t_guess = start_wall_guess + off + tv / fps_nominal
    th = t_log[np.abs(t_log[None, :] - t_guess[:, None]).argmin(1)]
    ok = np.abs(th - t_guess) < SYM_S / 2
    A = np.stack([tv[ok], np.ones(ok.sum())], 1)
    (a, b0), *_ = np.linalg.lstsq(A, th[ok], rcond=None)
    resid = th[ok] - A @ np.array([a, b0])
    return dict(a=float(a), b=float(b0), fps=1 / a, corr=float(best[1]), n_transitions=int(ok.sum()), resid_ms=float(np.std(resid) * 1000))


def frame_times(video: Path, host_log: Path, start_json: Path, xy=None, fps_nominal=None, out_csv: Path | None = None):
    import json
    st = json.loads(start_json.read_text())
    if fps_nominal is None:
        cap = cv2.VideoCapture(str(video)); fps_nominal = cap.get(cv2.CAP_PROP_FPS) or 25.0; cap.release()
    v, xy = blob_brightness(video, xy); b = binarize(v)
    t_log, lvl_log = load_host_log(host_log)
    fit = align(b, fps_nominal, st["wall_s"], t_log, lvl_log)
    fit["blob_xy"] = xy
    if out_csv:
        with open(out_csv, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["frame", "wall_s"])
            for i in range(len(v)): w.writerow([i, f"{fit['a'] * i + fit['b']:.4f}"])
    return fit


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser(); ap.add_argument("video", type=Path); ap.add_argument("host_log", type=Path); ap.add_argument("start_json", type=Path)
    ap.add_argument("--xy", type=int, nargs=2); ap.add_argument("--out", type=Path)
    a = ap.parse_args(); print(json.dumps(frame_times(a.video, a.host_log, a.start_json, tuple(a.xy) if a.xy else None, out_csv=a.out), indent=1))
