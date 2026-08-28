#!/usr/bin/env python3
"""Run an rtmlib 2D detector on any video; cache keypoints as .npz (kp (T,K,2), score (T,K)).
Usage: uv run python tools/detect_video.py VIDEO OUT.npz [--model body|wholebody] [--mode balanced|performance] [--device cpu|cuda] [--max-frames N]
"""
from __future__ import annotations
import argparse, time
from pathlib import Path
import cv2, numpy as np
from slimevr_camera import enable_cuda

ap = argparse.ArgumentParser(); ap.add_argument("video", type=Path); ap.add_argument("out", type=Path)
ap.add_argument("--model", default="body", choices=["body", "wholebody"]); ap.add_argument("--mode", default="balanced")
ap.add_argument("--device", default="cpu"); ap.add_argument("--max-frames", type=int)
a = ap.parse_args()
enable_cuda()
from rtmlib import Body, Wholebody
det = (Body if a.model == "body" else Wholebody)(mode=a.mode, backend="onnxruntime", device=a.device)
K = 17 if a.model == "body" else 133
cap = cv2.VideoCapture(str(a.video)); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); n = min(n, a.max_frames) if a.max_frames else n
kps, scs, t0 = [], [], time.time()
for i in range(n):
    ok, img = cap.read()
    if not ok: break
    k, s = det(img)
    if len(k) == 0: kps.append(np.full((K, 2), np.nan)); scs.append(np.zeros(K))
    else: p = int(np.argmax(s.mean(1))); kps.append(k[p]); scs.append(s[p])
    if i % 500 == 0: print(f"{a.video.name}: {i}/{n} {(i+1)/(time.time()-t0):.1f} fps", flush=True)
a.out.parent.mkdir(parents=True, exist_ok=True)
np.savez_compressed(a.out, kp=np.stack(kps), score=np.stack(scs), model=f"rtmlib-{a.model}-{a.mode}", video=str(a.video))
print("wrote", a.out, len(kps), "frames", f"{time.time()-t0:.0f} s")
