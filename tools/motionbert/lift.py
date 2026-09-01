#!/usr/bin/env python3
"""Lift prepared H36M-17 2D keypoint clips to 3D with MotionBERT.

Input npz: any number of arrays, each (T,17,3) [x, y, conf] normalized per the
MotionBERT wild convention (see slimevr_camera.mono.coco_to_h36m_input).
Output npz: same keys, each (T,17,3) pixel-aligned camera-frame 3D (same x/y
scale as the input, z = relative depth).

Usage: uv run python lift.py IN.npz OUT.npz --checkpoint CKPT.bin [--config CFG.yaml]
Mirrors the inference logic of MotionBERT/infer_wild.py (flip TTA per config).
"""
from __future__ import annotations

import argparse, sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "MotionBERT"))

from lib.utils.tools import get_config          # noqa: E402
from lib.utils.learning import load_backbone    # noqa: E402
from lib.utils.utils_data import flip_data      # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("inp", type=Path)
ap.add_argument("out", type=Path)
ap.add_argument("--checkpoint", type=Path, required=True)
ap.add_argument("--config", type=Path, default=HERE / "MotionBERT/configs/pose3d/MB_ft_h36m_global_lite.yaml")
a = ap.parse_args()

args = get_config(str(a.config))
model = load_backbone(args)
ckpt = torch.load(a.checkpoint, map_location="cpu", weights_only=True)
model.load_state_dict({k.removeprefix("module."): v for k, v in ckpt["model_pos"].items()}, strict=True)
model.eval()
torch.set_num_threads(max(1, torch.get_num_threads()))

data = np.load(a.inp)
out = {}
with torch.no_grad():
    for key in data.files:
        clip = data[key].astype(np.float32)          # (T,17,3)
        preds = []
        for st in range(0, len(clip), args.clip_len):
            x = torch.from_numpy(clip[st:st + args.clip_len][None])
            if args.no_conf:
                x = x[..., :2]
            if args.flip:
                y = (model(x) + flip_data(model(flip_data(x)))) / 2.0
            else:
                y = model(x)
            if args.rootrel:
                y[:, :, 0, :] = 0
            preds.append(y[0].numpy())
        out[key] = np.concatenate(preds)
        print(f"{key}: {len(out[key])} frames", flush=True)
np.savez_compressed(a.out, **out)
print("wrote", a.out)
