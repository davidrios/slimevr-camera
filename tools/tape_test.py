#!/usr/bin/env python3
"""Retroreflective-tape test: grab frames from the RTSP cameras and report blob contrast.

  uv run python tools/tape_test.py grab  [--cams rtsp://192.168.15.60:554/11 ...] [--n 3]
  uv run python tools/tape_test.py analyze FRAME.jpg [--roi x0 y0 x1 y1] [--thresh 230]

`grab` saves frames to /mnt/data2/david/work/slimevr-camera-data/tape-test/<stamp>_camN.jpg.
`analyze` lists blobs (sub-pixel centroid, radius, peak) and, for a ROI around the tracker,
the peak-vs-background contrast that decides whether patches are usable markers.
"""
from __future__ import annotations
import argparse, subprocess, sys, time
from pathlib import Path
import cv2, numpy as np
from slimevr_camera.markers import detect_blobs

OUT = Path("/mnt/data2/david/work/slimevr-camera-data/tape-test")
DEFAULT_CAMS = ["rtsp://192.168.15.60:554/11"]


def grab(cams, n):
    OUT.mkdir(parents=True, exist_ok=True); stamp = time.strftime("%Y%m%d_%H%M%S")
    for i, url in enumerate(cams, 1):
        for k in range(n):
            f = OUT / f"{stamp}_cam{i}_{k}.jpg"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-rtsp_transport", "tcp", "-i", url, "-frames:v", "1", "-y", str(f)], timeout=30)
            print("saved", f); time.sleep(0.5)


def analyze(path, roi, thresh):
    g = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    print(f"{path.name}: {g.shape[1]}x{g.shape[0]}  mean {g.mean():.0f}  p50 {np.percentile(g,50):.0f}  p99 {np.percentile(g,99):.0f}  saturated px {(g>=250).sum()}")
    if roi:
        x0, y0, x1, y1 = roi; sub = g[y0:y1, x0:x1]
        b = detect_blobs(sub, thresh=thresh, min_area=2, max_area=3000)
        bg = np.percentile(sub, 50)
        print(f"ROI {roi}: background p50 {bg:.0f}; {len(b)} blobs >= {thresh}:")
        for x, y, r, p in b: print(f"   ({x0+x:7.1f},{y0+y:7.1f}) r={r:4.1f}px peak={p:3.0f} contrast={p/max(bg,1):.1f}x")
        if len(b) >= 2:
            d = np.linalg.norm(b[:, None, :2] - b[None, :, :2], axis=-1); print("   pairwise blob distances (px):", np.round(d[np.triu_indices(len(b), 1)], 1)[:10])
    else:
        b = detect_blobs(g, thresh=thresh, min_area=2, max_area=3000)
        print(f"{len(b)} blobs >= {thresh} (whole frame; give --roi to focus on the tracker):", [(int(x), int(y), round(float(r),1), int(p)) for x, y, r, p in b[:12]])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grab"); g.add_argument("--cams", nargs="+", default=DEFAULT_CAMS); g.add_argument("--n", type=int, default=3)
    a = sub.add_parser("analyze"); a.add_argument("frame", type=Path); a.add_argument("--roi", type=int, nargs=4); a.add_argument("--thresh", type=int, default=230)
    args = ap.parse_args()
    grab(args.cams, args.n) if args.cmd == "grab" else analyze(args.frame, args.roi, args.thresh)
