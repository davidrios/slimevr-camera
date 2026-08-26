#!/usr/bin/env python3
"""Heading error of a real 2D detector on MoVi, per bone — v2.

Reference = the verified Visual3D segment frame (world rotation via FK), i.e.
exactly what a perfectly-mounted IMU on that segment would report.  For each
tracker we compare the floor heading of the camera-observed axis (from
`slimevr_camera.heading`) with the floor heading of the corresponding
*fixed local axis* of the segment frame (SEG_LOCAL_AXIS, identified
empirically from marker joint centres).

Three numbers per bone:
  raw     — error vs the segment axis as-is (includes a constant per-user
            offset between the observed feature and the segment's axis,
            e.g. knee-flexion axis vs Visual3D thigh X).
  reset   — error after subtracting the per-subject median (what a full
            reset absorbs).  This is the quantity that matters for us.
  window  — 'reset' error averaged over still windows of >= 1 s, i.e. what
            one correction would be based on.

Usage: uv run python experiments/04-movi-detector-bias/evaluate.py --subjects 1 2 3 4 5 --model body-balanced
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2, numpy as np, pandas as pd
from scipy.spatial.transform import Rotation as Rot

from slimevr_camera.data.movi import ROOT, SEGMENTS, load_camera, load_subject
from slimevr_camera.geometry import triangulate
from slimevr_camera.heading import estimate_all
from slimevr_camera.skeleton import KEYPOINTS, wrap

COCO17 = ["nose", "eyeL", "eyeR", "earL", "earR", "shoulderL", "shoulderR", "elbowL", "elbowR", "wristL", "wristR", "hipL", "hipR", "kneeL", "kneeR", "ankleL", "ankleR"]
# COCO-WholeBody: 17 body + feet at 17..22 (L big toe, L small toe, L heel, R big toe, R small toe, R heel)
WB_TOE = {"toeL": 17, "toeR": 20}


def our2model(K):
    m = {k: (COCO17.index(k) if k in COCO17 else COCO17.index("nose") if k == "head" else None) for k in KEYPOINTS}
    if K >= 23:
        m.update(WB_TOE)
    return m


# MoVi world is Z-up (mm); our heading code is Y-up.  (x,y,z) -> (x, z, -y)
Z2Y = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)

# Fixed local axis of each Visual3D segment that our estimator observes
# (identified 2026-08-26 from marker joint centres, subject 1).
SEG_LOCAL_AXIS = {   # fitted on subjects 1-3 from marker joint centres (see README)
    "hip": [1, 0, 0], "chest": [1, 0, 0],
    "thighL": [-1, 0.04, 0.01], "thighR": [-1, 0.04, 0], "shinL": [-1, 0.02, 0], "shinR": [-1, 0.10, 0],
    "footL": [0.11, 0.03, -0.99], "footR": [-0.11, 0.04, -0.99],
    # upper arms excluded: Visual3D's upper-arm frame has no stable twist (elbow-plane normal sd 0.6 in local coords)
}
SEG_CODE = {v: k for k, v in SEGMENTS.items() if v}


def undistort(uv, cam):
    k = np.array([cam.dist[0], cam.dist[1], 0, 0], float)
    return cv2.undistortPoints(uv.reshape(-1, 1, 2).astype(np.float64), cam.K, k, P=cam.K).reshape(uv.shape)


def heading(v):
    return np.arctan2(v[..., 0], v[..., 2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", type=int, nargs="+", default=[1])
    ap.add_argument("--model", default="body-balanced")
    ap.add_argument("--round", default="F")
    ap.add_argument("--keypoint-dir", type=Path, default=ROOT / "keypoints")
    ap.add_argument("--min-score", type=float, default=0.3)
    ap.add_argument("--still-deg-s", type=float, default=15.0)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    a = ap.parse_args(); a.out.mkdir(exist_ok=True)
    cams = {c: load_camera(c) for c in ("PG1", "PG2")}
    rows = []
    for subj in a.subjects:
        s = load_subject(subj, a.round)
        kp = {c: np.load(a.keypoint_dir / f"{a.round}_{c}_Subject_{subj}_{a.model}.npz") for c in cams}
        K = kp["PG1"]["kp"].shape[1]; o2m = our2model(K)
        T = min(len(kp[c]["kp"]) for c in cams)
        for f in range(T):
            mi = s.mocap_index_for_video_frame(f)
            if mi is None or mi + 4 >= len(s.affine): continue
            W1, W2 = s.world_affine(mi), s.world_affine(mi + 4)
            if "hip" not in W1: continue
            uvs, valid = [], []
            for c, cam in cams.items():
                u = kp[c]["kp"][f]; sc = kp[c]["score"][f]
                uv = np.full((len(KEYPOINTS), 2), np.nan); ok = np.zeros(len(KEYPOINTS), bool)
                for i, k in enumerate(KEYPOINTS):
                    j = o2m[k]
                    if j is not None and sc[j] > a.min_score:
                        uv[i] = u[j]; ok[i] = True
                if ok.any(): uv[ok] = undistort(uv[ok], cam)
                uvs.append(uv); valid.append(ok)
            X, ok3 = triangulate(list(cams.values()), np.stack(uvs), np.stack(valid))
            X = np.where(ok3[:, None], X, np.nan) @ Z2Y.T
            est = estimate_all(X[None])
            hip_yaw = np.rad2deg(heading(Z2Y @ W1["hip"][:3, :3] @ np.array([1.0, 0, 0])))
            motion = next((m for (x, y), m in zip(s.flags30, s.motions) if x <= f <= y), None)
            for name, ax_local in SEG_LOCAL_AXIS.items():
                if name not in est or name not in W1 or name not in W2: continue
                ax_d, _, q = est[name]
                if np.isnan(ax_d[0]).any() or q[0] < 0.3: continue
                Rw = Z2Y @ W1[name][:3, :3]
                ref = Rw @ (np.asarray(ax_local, float) / np.linalg.norm(ax_local))
                dR = Rot.from_matrix(W2[name][:3, :3] @ W1[name][:3, :3].T)
                speed = np.rad2deg(np.linalg.norm(dR.as_rotvec())) * 30
                rows.append(dict(subject=subj, frame=f, motion=motion, bone=name, err=float(np.rad2deg(wrap(heading(ax_d[0]) - heading(ref)))),
                                 quality=float(q[0]), body_yaw=float(hip_yaw), speed=float(speed), still=bool(speed < a.still_deg_s)))
    df = pd.DataFrame(rows)
    # reset-referenced error: subtract per-subject, per-bone median (constant offset a full reset absorbs)
    df["err_reset"] = df.err - df.groupby(["subject", "bone"]).err.transform("median")
    # still windows: runs of consecutive still frames per (subject, bone), >= 30 frames; error of the window-mean axis ~ mean of errors
    df = df.sort_values(["subject", "bone", "frame"])
    df["run"] = ((~df.still) | (df.frame.diff() != 1) | (df.bone != df.bone.shift()) | (df.subject != df.subject.shift())).cumsum()
    win = df[df.still].groupby(["subject", "bone", "run"]).agg(n=("err_reset", "size"), err_win=("err_reset", "mean"), yaw=("body_yaw", "mean"), motion=("motion", "first")).reset_index()
    win = win[win.n >= 30]
    df.to_csv(a.out / f"errors_{a.model}.csv", index=False); win.to_csv(a.out / f"windows_{a.model}.csv", index=False)
    pd.set_option("display.width", 220)
    print(f"model={a.model} subjects={a.subjects}: {len(df)} bone-frames, {len(win)} still windows (>=1 s)\n")
    def stats(x): return pd.Series(dict(n=len(x), bias=x.mean(), sd=x.std(), mae=x.abs().mean(), p95=x.abs().quantile(.95)))
    print("RAW error vs segment axis (per frame):"); print(df.groupby("bone").err.apply(stats).unstack().round(2).to_string())
    print("\nRESET-referenced error, per frame, still vs moving:"); print(df.groupby(["bone", "still"]).err_reset.apply(stats).unstack().round(2).to_string())
    # stillness-independent: 1 s rolling mean of the reset-referenced error over consecutive frames
    roll = df.set_index(["subject", "bone", "frame"]).err_reset.groupby(level=["subject", "bone"]).transform(lambda x: x.rolling(30, min_periods=25).mean()).dropna()
    print("\n1-second ROLLING-MEAN reset-referenced error (all frames, moving included) — noise left after averaging 30 frames:")
    print(roll.groupby(level="bone").apply(stats).unstack().round(2).to_string())
    print("\nWINDOW-level reset-referenced error (mean over still windows >= 1 s) — the number that matters:")
    print(win.groupby("bone").err_win.apply(stats).unstack().round(2).to_string())
    wb = win.copy(); wb["yaw_bin"] = (wb.yaw // 45 * 45).astype(int)
    print("\nwindow error by body yaw bin (mean):"); print(wb.pivot_table(index="bone", columns="yaw_bin", values="err_win", aggfunc="mean").round(1).to_string())
    print("\nwindow |error| by motion (mean over bones):"); print(win.groupby("motion").err_win.apply(lambda x: x.abs().mean()).round(2).sort_values().to_string())


if __name__ == "__main__":
    main()
