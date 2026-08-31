#!/usr/bin/env python3
"""Exp 07 — familiar-pose gate + in-pose measurement on MoVi (markerless main line).

Per subject: the FIRST still-ish segment of a chosen 'idle-like' motion is the
trusted window (template learned from detector-triangulated joints, and the
per-bone camera bias in that window is calibrated against the segment-frame
truth). Every LATER frame that matches the template and is still gets an
in-pose measurement; its error vs truth — with and without the calibrated
per-pose bias — is what an automatic full reset would apply.

Usage: uv run python experiments/07-familiar-pose/evaluate.py --subjects 1 2 3 4 5 --model wholebody-performance
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2, numpy as np, pandas as pd
from scipy.spatial.transform import Rotation as Rot

from slimevr_camera.data.movi import ROOT, SEGMENTS, load_camera, load_subject
from slimevr_camera.familiar import learn_template, match_frames, in_pose_measurement, descriptor
from slimevr_camera.geometry import triangulate
from slimevr_camera.skeleton import KEYPOINTS, wrap

COCO17 = ["nose", "eyeL", "eyeR", "earL", "earR", "shoulderL", "shoulderR", "elbowL", "elbowR", "wristL", "wristR", "hipL", "hipR", "kneeL", "kneeR", "ankleL", "ankleR"]
WB_TOE = {"toeL": 17, "toeR": 20}
Z2Y = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)
SEG_LOCAL_AXIS = {"hip": [1, 0, 0], "chest": [1, 0, 0], "thighL": [-1, 0, 0], "thighR": [-1, 0, 0], "shinL": [-1, 0, 0], "shinR": [-1, 0, 0]}
SEG_CODE = {v: k for k, v in SEGMENTS.items() if v}
IDLE = ["sitting_down", "cross_legged_sitting", "phone_talking", "checking_watch", "taking_photo", "scratching_head", "crossarms"]


def triangulated_joints(subj, model):
    cams = {c: load_camera(c) for c in ("PG1", "PG2")}
    kp = {c: np.load(ROOT / "keypoints" / f"F_{c}_Subject_{subj}_{model}.npz") for c in cams}
    K = kp["PG1"]["kp"].shape[1]
    o2m = {k: (COCO17.index(k) if k in COCO17 else COCO17.index("nose") if k == "head" else None) for k in KEYPOINTS}
    if K >= 23: o2m.update(WB_TOE)
    T = min(len(kp[c]["kp"]) for c in cams)
    X = np.full((T, len(KEYPOINTS), 3), np.nan)
    for f in range(T):
        uvs, valid = [], []
        for c, cam in cams.items():
            u = kp[c]["kp"][f]; sc = kp[c]["score"][f]
            uv = np.full((len(KEYPOINTS), 2), np.nan); ok = np.zeros(len(KEYPOINTS), bool)
            for i, k in enumerate(KEYPOINTS):
                j = o2m[k]
                if j is not None and sc[j] > 0.3:
                    kk = np.array([cam.dist[0], cam.dist[1], 0, 0], float)
                    uv[i] = cv2.undistortPoints(u[j].reshape(1, 1, 2).astype(np.float64), cam.K, kk, P=cam.K).ravel(); ok[i] = True
            uvs.append(uv); valid.append(ok)
        x, ok3 = triangulate(list(cams.values()), np.stack(uvs), np.stack(valid))
        X[f] = np.where(ok3[:, None], x, np.nan)
    return X @ Z2Y.T   # Y-up mm


def truth_heading(s, mi, name):
    W = s.world_affine(mi)
    if name not in W: return None
    R = Z2Y @ W[name][:3, :3]; v = R @ np.asarray(SEG_LOCAL_AXIS[name], float)
    return float(np.arctan2(v[0], v[2]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    ap.add_argument("--model", default="wholebody-performance")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results"); a = ap.parse_args(); a.out.mkdir(exist_ok=True)
    rows = []
    for subj in a.subjects:
        s = load_subject(subj, "F"); X = triangulated_joints(subj, a.model)
        for motion in IDLE:
            if motion not in s.motions: continue
            a30, b30 = s.flags30[s.motions.index(motion)]
            b30 = min(b30, len(X) - 1)
            seg = X[a30:b30 + 1]
            if len(seg) < 90: continue
            n_tr = max(30, len(seg) // 3)                     # trusted window = first third (>=1 s)
            tpl = learn_template(motion, seg[:n_tr])
            if tpl is None: continue
            # per-pose bias calibrated in the trusted window
            bias = {}
            meas_tr = in_pose_measurement(seg[:n_tr])
            for name in SEG_LOCAL_AXIS:
                if name not in meas_tr: continue
                hs = [truth_heading(s, s.mocap_index_for_video_frame(f), name) for f in range(a30, a30 + n_tr, 5)]
                hs = [h for h in hs if h is not None]
                if hs: bias[name] = wrap(meas_tr[name] - np.arctan2(np.mean(np.sin(hs)), np.mean(np.cos(hs))))
            # later frames matching the template
            idx, dist = match_frames(seg[n_tr:], [tpl])
            match = np.flatnonzero(idx == 0) + n_tr
            if len(match) < 15: 
                rows.append(dict(subject=subj, motion=motion, matched=0)); continue
            # windows of >=15 consecutive-ish matched frames
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
                    rows.append(dict(subject=subj, motion=motion, matched=1, bone=name, win_s=round((w1 - w0) / 30, 1), err_raw=raw, err_cal=cal))
    df = pd.DataFrame(rows); df.to_csv(a.out / f"exp07_{a.model}.csv", index=False)
    d = df[df.matched == 1]
    print(f"{a.model}: {len(d)} bone-windows from {d.subject.nunique() if len(d) else 0} subjects; motions with no re-match: {int((df.matched == 0).sum())}")
    st = lambda x: pd.Series(dict(n=len(x), bias=x.mean(), sd=x.std(), mae=x.abs().mean(), p95=x.abs().quantile(.95)))
    if len(d):
        print("\nRAW in-pose heading error (deg):"); print(d.groupby("bone").err_raw.apply(st).unstack().round(2).to_string())
        print("\nAfter the per-pose bias from the trusted window (what the auto-reset would apply):")
        print(d.groupby("bone").err_cal.apply(st).unstack().round(2).to_string())
        print("\nper motion, err_cal MAE:"); print(d.groupby("motion").err_cal.apply(lambda x: x.abs().mean()).round(2).to_string())


if __name__ == "__main__":
    main()
