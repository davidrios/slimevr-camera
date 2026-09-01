#!/usr/bin/env python3
"""Exp 09 — single-camera familiar-pose measurement on MoVi (D36).

Same protocol as exp 07, but 3D joints come from ONE view via MotionBERT
monocular lifting (slimevr_camera.mono) instead of 2-cam triangulation.
Each MoVi camera (PG1, PG2) is evaluated separately as "the user's one
camera"; results are comparable row-for-row with exp 07.

Usage: uv run python experiments/09-single-camera/evaluate.py \
          --subjects 1 2 3 4 5 --model wholebody-performance --ckpt lite
"""
from __future__ import annotations

import argparse, subprocess
from pathlib import Path

import numpy as np, pandas as pd

from slimevr_camera.data.movi import ROOT, load_camera, load_subject
from slimevr_camera.familiar import learn_template, match_frames, in_pose_measurement
from slimevr_camera.mono import coco_to_h36m_input, lifted_to_keypoints
from slimevr_camera.skeleton import wrap

REPO = Path(__file__).resolve().parents[2]
CKPTS = {
    "lite": ("/mnt/data2/david/work/slimevr-camera-data/models/motionbert/mb_ft_h36m_global_lite.bin",
             REPO / "tools/motionbert/MotionBERT/configs/pose3d/MB_ft_h36m_global_lite.yaml"),
    "full": ("/mnt/data2/david/work/slimevr-camera-data/models/motionbert/mb_ft_h36m.bin",
             REPO / "tools/motionbert/MotionBERT/configs/pose3d/MB_ft_h36m.yaml"),
}
Z2Y = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)
SEG_LOCAL_AXIS = {"hip": [1, 0, 0], "chest": [1, 0, 0], "thighL": [-1, 0, 0], "thighR": [-1, 0, 0], "shinL": [-1, 0, 0], "shinR": [-1, 0, 0]}
IDLE = ["sitting_down", "cross_legged_sitting", "phone_talking", "checking_watch", "taking_photo", "scratching_head", "crossarms"]


def lifted_segments(subj: int, cam_name: str, model: str, ckpt: str) -> dict[str, np.ndarray]:
    """motion -> (T, K, 3) Y-up world-frame joints for each idle segment."""
    cache = ROOT / "lift3d"; cache.mkdir(exist_ok=True)
    out_npz = cache / f"F_{cam_name}_Subject_{subj}_{model}_{ckpt}.npz"
    cam = load_camera(cam_name)
    s = load_subject(subj, "F")
    kp = np.load(ROOT / "keypoints" / f"F_{cam_name}_Subject_{subj}_{model}.npz")
    T_all = len(kp["kp"])
    segs = {}
    for motion in IDLE:
        if motion not in s.motions: continue
        a30, b30 = s.flags30[s.motions.index(motion)]
        b30 = min(b30, T_all - 1)
        if b30 - a30 + 1 < 90: continue
        segs[motion] = (a30, b30)
    if not out_npz.exists():
        in_npz = cache / (out_npz.stem + ".in.npz")
        np.savez_compressed(in_npz, **{m: coco_to_h36m_input(kp["kp"][a:b + 1], kp["score"][a:b + 1], cam)
                                       for m, (a, b) in segs.items()})
        ck, cfg = CKPTS[ckpt]
        subprocess.run(["uv", "run", "--project", str(REPO / "tools/motionbert"), "python",
                        str(REPO / "tools/motionbert/lift.py"), str(in_npz), str(out_npz),
                        "--checkpoint", ck, "--config", str(cfg)], check=True)
    lifted = np.load(out_npz)
    out = {}
    for m, (a, b) in segs.items():
        inp = coco_to_h36m_input(kp["kp"][a:b + 1], kp["score"][a:b + 1], cam)
        out[m] = (lifted_to_keypoints(lifted[m], inp, cam, world_R=Z2Y), a, b)
    return out


def truth_heading(s, mi, name):
    W = s.world_affine(mi)
    if name not in W: return None
    R = Z2Y @ W[name][:3, :3]; v = R @ np.asarray(SEG_LOCAL_AXIS[name], float)
    return float(np.arctan2(v[0], v[2]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    ap.add_argument("--model", default="wholebody-performance")
    ap.add_argument("--ckpt", default="lite", choices=list(CKPTS))
    ap.add_argument("--cams", nargs="+", default=["PG1", "PG2"])
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results"); a = ap.parse_args(); a.out.mkdir(exist_ok=True)
    rows = []
    for cam_name in a.cams:
        for subj in a.subjects:
            s = load_subject(subj, "F")
            for motion, (seg, a30, b30) in lifted_segments(subj, cam_name, a.model, a.ckpt).items():
                n_tr = max(30, len(seg) // 3)                     # trusted window = first third (>=1 s)
                tpl = learn_template(motion, seg[:n_tr])
                if tpl is None: continue
                bias = {}
                meas_tr = in_pose_measurement(seg[:n_tr])
                for name in SEG_LOCAL_AXIS:
                    if name not in meas_tr: continue
                    hs = [truth_heading(s, s.mocap_index_for_video_frame(f), name) for f in range(a30, a30 + n_tr, 5)]
                    hs = [h for h in hs if h is not None]
                    if hs: bias[name] = wrap(meas_tr[name] - np.arctan2(np.mean(np.sin(hs)), np.mean(np.cos(hs))))
                idx, dist = match_frames(seg[n_tr:], [tpl])
                match = np.flatnonzero(idx == 0) + n_tr
                if len(match) < 15:
                    rows.append(dict(cam=cam_name, subject=subj, motion=motion, matched=0)); continue
                wins = []; start = match[0]; prev = match[0]
                for f in match[1:]:
                    if f - prev > 5:
                        if prev - start >= 15: wins.append((start, prev))
                        start = f
                    prev = f
                if prev - start >= 15: wins.append((start, prev))
                for w0, w1 in wins:
                    meas = in_pose_measurement(seg[w0:w1])
                    for name in SEG_LOCAL_AXIS:
                        if name not in meas: continue
                        hs = [truth_heading(s, s.mocap_index_for_video_frame(f), name) for f in range(a30 + w0, a30 + w1, 5)]
                        hs = [h for h in hs if h is not None]
                        if not hs: continue
                        ht = np.arctan2(np.mean(np.sin(hs)), np.mean(np.cos(hs)))
                        raw = np.degrees(wrap(meas[name] - ht))
                        cal = np.degrees(wrap(meas[name] - bias.get(name, 0.0) - ht))
                        rows.append(dict(cam=cam_name, subject=subj, motion=motion, matched=1, bone=name,
                                         win_s=round((w1 - w0) / 30, 1), err_raw=raw, err_cal=cal))
    df = pd.DataFrame(rows); df.to_csv(a.out / f"exp09_{a.model}_{a.ckpt}.csv", index=False)
    st = lambda x: pd.Series(dict(n=len(x), bias=x.mean(), sd=x.std(), mae=x.abs().mean(), p95=x.abs().quantile(.95)))
    for cam_name in a.cams:
        d = df[(df.cam == cam_name) & (df.matched == 1)]
        print(f"\n===== {cam_name} ({a.ckpt}): {len(d)} bone-windows; motions with no re-match: {int(((df.cam == cam_name) & (df.matched == 0)).sum())}")
        if len(d):
            print("RAW in-pose heading error (deg):"); print(d.groupby("bone").err_raw.apply(st).unstack().round(2).to_string())
            print("\nAfter per-pose bias from the trusted window:")
            print(d.groupby("bone").err_cal.apply(st).unstack().round(2).to_string())
            print("\nper motion, err_cal MAE:"); print(d.groupby("motion").err_cal.apply(lambda x: x.abs().mean()).round(2).to_string())


if __name__ == "__main__":
    main()
