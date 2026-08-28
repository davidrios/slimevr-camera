#!/usr/bin/env python3
"""Analyse a tape-test recording: per-frame saturated blobs (excluding static ones),
contrast, radius; write annotated frames for the best moments.
Usage: uv run python tools/tape_analyze_video.py VIDEO.mkv [--thresh 235] [--out DIR]"""
from __future__ import annotations
import argparse
from pathlib import Path
import cv2, numpy as np
from slimevr_camera.markers import detect_blobs

ap = argparse.ArgumentParser(); ap.add_argument("video", type=Path); ap.add_argument("--thresh", type=int, default=235); ap.add_argument("--out", type=Path)
a = ap.parse_args(); out = a.out or a.video.with_suffix(""); out.mkdir(exist_ok=True)
cap = cv2.VideoCapture(str(a.video)); fps = cap.get(cv2.CAP_PROP_FPS); frames = []; i = 0
while True:
    ok, img = cap.read()
    if not ok: break
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    b = detect_blobs(g, thresh=a.thresh, min_area=2, max_area=1500)
    frames.append((i, g, b)); i += 1
cap.release()
# static blobs = present (within 3 px) in > 80 % of frames -> window/lights; drop them
allb = np.concatenate([b[:, :2] for _, _, b in frames if len(b)]) if any(len(b) for _, _, b in frames) else np.zeros((0, 2))
static = []
if len(allb):
    from collections import Counter
    key = Counter(map(tuple, np.round(allb / 4).astype(int)))
    static = [np.array(k) * 4 for k, c in key.items() if c > 0.8 * len(frames)]
def is_static(xy): return any(np.hypot(*(xy - s)) < 6 for s in static)
print(f"{a.video.name}: {len(frames)} frames @ {fps:.0f} fps, {len(static)} static bright spots ignored")
rows = []
for i, g, b in frames:
    dyn = [bb for bb in b if not is_static(bb[:2])]
    bg = float(np.percentile(g, 50))
    rows.append((i, len(dyn), dyn, bg))
counts = np.array([r[1] for r in rows]); print("frames with >=1 moving blob:", int((counts >= 1).sum()), " >=2:", int((counts >= 2).sum()), " >=3:", int((counts >= 3).sum()))
best = sorted(rows, key=lambda r: -r[1])[:6]
for i, n, dyn, bg in best:
    g = frames[i][1]; img = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    for x, y, r, p in dyn: cv2.circle(img, (int(x), int(y)), int(max(r * 3, 8)), (0, 0, 255), 2)
    cv2.imwrite(str(out / f"frame{i:05d}_{n}blobs.jpg"), img)
    print(f"  frame {i} (t={i/fps:5.1f}s): {n} blobs, bg {bg:.0f}:", [(int(x), int(y), f"r{r:.1f}", f"peak{p:.0f}", f"{p/max(bg,1):.0f}x") for x, y, r, p in dyn[:6]])
# time profile
seg = [(int(r[0] / fps), r[1]) for r in rows]; prof = {}
for t, n in seg: prof[t] = max(prof.get(t, 0), n)
print("max blobs per second:", " ".join(f"{t}:{n}" for t, n in sorted(prof.items())))
