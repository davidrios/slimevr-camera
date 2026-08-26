#!/usr/bin/env python3
"""Run a 2D pose detector (rtmlib) on MoVi FLIR videos; cache keypoints.

Output: data/movi/keypoints/<round>_<cam>_Subject_<n>_<model>.npz with
kp (T,K,2) pixels, score (T,K), model name. K=17 COCO (body) or 133 (wholebody).
Usage: uv run python experiments/04-movi-detector-bias/detect.py --subjects 1 --cams PG1 PG2 [--model body|wholebody] [--max-frames N] [--device cpu|cuda]
"""
from __future__ import annotations

import argparse, time
from pathlib import Path

import cv2, numpy as np

from slimevr_camera import enable_cuda
from slimevr_camera.data.movi import ROOT

OUT = ROOT / "keypoints"


def run(video: Path, out: Path, model: str, device: str, max_frames: int | None, mode: str):
    enable_cuda()
    from rtmlib import Body, Wholebody
    cls = Body if model == "body" else Wholebody
    det = cls(mode=mode, backend="onnxruntime", device=device)
    cap = cv2.VideoCapture(str(video)); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if max_frames: n = min(n, max_frames)
    kps, scs = [], []
    t0 = time.time()
    for i in range(n):
        ret, img = cap.read()
        if not ret: break
        k, s = det(img)                            # (P,K,2), (P,K)
        if len(k) == 0:
            kps.append(np.full((det_k(model), 2), np.nan)); scs.append(np.zeros(det_k(model)))
        else:
            p = int(np.argmax(s.mean(1)))          # single person: take the best-scoring detection
            kps.append(k[p]); scs.append(s[p])
        if i % 200 == 0: print(f"  {video.name}: {i}/{n} frames, {(i + 1) / (time.time() - t0):.1f} fps", flush=True)
    cap.release()
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, kp=np.stack(kps), score=np.stack(scs), model=f"rtmlib-{model}-{mode}")
    print(f"  wrote {out} ({len(kps)} frames, {(time.time() - t0):.0f} s)")


def det_k(model): return 17 if model == "body" else 133


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", type=int, nargs="+", default=[1])
    ap.add_argument("--cams", nargs="+", default=["PG1", "PG2"])
    ap.add_argument("--round", default="F")
    ap.add_argument("--model", default="body", choices=["body", "wholebody"])
    ap.add_argument("--mode", default="balanced", choices=["lightweight", "balanced", "performance"])
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--max-frames", type=int)
    a = ap.parse_args()
    for s in a.subjects:
        for cam in a.cams:
            v = ROOT / f"{a.round}_{cam}_Subject_{s}_L.avi"
            o = OUT / f"{a.round}_{cam}_Subject_{s}_{a.model}-{a.mode}.npz"
            if o.exists(): print("have", o.name); continue
            run(v, o, a.model, a.device, a.max_frames, a.mode)
