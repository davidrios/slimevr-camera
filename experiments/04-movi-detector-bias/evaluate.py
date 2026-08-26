#!/usr/bin/env python3
"""Heading bias of a real 2D detector on MoVi, per bone.

For each video frame with cached keypoints in both views: undistort,
triangulate (DLT) the COCO joints, derive each tracker's observable axis
(slimevr_camera.heading.estimate_all, in a Y-up frame), and compare its floor
heading with the SAME axis taken from the Visual3D ground-truth segment
frame.  Reports mean (bias) / std (noise) per bone, still vs moving, and
bias vs the body's yaw relative to the cameras.

Usage: uv run python experiments/04-movi-detector-bias/evaluate.py --subjects 1 2 3 4 5 [--model body-balanced]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2, numpy as np, pandas as pd
from scipy.spatial.transform import Rotation as Rot

from slimevr_camera.data.movi import ROOT, load_camera, load_subject
from slimevr_camera.geometry import triangulate
from slimevr_camera.heading import estimate_all
from slimevr_camera.skeleton import KEYPOINTS, wrap

COCO = ["nose", "eyeL", "eyeR", "earL", "earR", "shoulderL", "shoulderR", "elbowL", "elbowR", "wristL", "wristR", "hipL", "hipR", "kneeL", "kneeR", "ankleL", "ankleR"]
# our keypoint order -> COCO index (toes absent in body-17 -> NaN)
OUR2COCO = {k: (COCO.index(k) if k in COCO else COCO.index("nose") if k == "head" else None) for k in KEYPOINTS}

# MoVi world is Z-up (mm). Our heading code assumes Y-up. Map (x,y,z)_movi -> (x, z, -y)_ours
Z2Y = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)

# Which local axis of the Visual3D segment frame corresponds to the axis our
# estimator observes.  Determined empirically in --calibrate-axes mode: the
# segment-frame axis whose floor heading best matches the estimator on GT
# joints (marker-derived) — then fixed here.
SEG_AXIS: dict[str, np.ndarray] = {}


def undistort(uv, cam):
    k = np.array([cam.dist[0], cam.dist[1], 0, 0], float)
    pts = uv.reshape(-1, 1, 2).astype(np.float64)
    out = cv2.undistortPoints(pts, cam.K, k, P=cam.K)
    return out.reshape(uv.shape)


def gt_joints_from_markers(s, mi):
    """Marker-derived pseudo-keypoints in our KEYPOINTS order (mm, Z-up) for
    checking the estimator itself, independent of any detector."""
    M = {n: s.markers[mi, i] for i, n in enumerate(s.marker_names)}
    def mid(*names): return np.mean([M[n] for n in names], 0)
    try:
        J = {
            "head": mid("LFHD", "RFHD", "LBHD", "RBHD"),
            "shoulderL": M["LSHO"], "shoulderR": M["RSHO"], "elbowL": M["LELB"], "elbowR": M["RELB"],
            "wristL": mid("LWRA", "LWRB"), "wristR": mid("RWRA", "RWRB"),
            "hipL": mid("LASI", "LPSI"), "hipR": mid("RASI", "RPSI"),
            "kneeL": M["LKNE"], "kneeR": M["RKNE"], "ankleL": M["LANK"], "ankleR": M["RANK"],
            "toeL": M["LTOE"], "toeR": M["RTOE"],
        }
    except KeyError as e:
        return None
    return np.stack([J[k] for k in KEYPOINTS])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", type=int, nargs="+", default=[1])
    ap.add_argument("--model", default="body-balanced")
    ap.add_argument("--round", default="F")
    ap.add_argument("--still-deg-s", type=float, default=15.0, help="GT segment angular speed threshold for 'still'")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    a = ap.parse_args(); a.out.mkdir(exist_ok=True)
    cams = {c: load_camera(c) for c in ("PG1", "PG2")}
    rows = []
    for subj in a.subjects:
        s = load_subject(subj, a.round)
        kp = {c: np.load(ROOT / "keypoints" / f"{a.round}_{c}_Subject_{subj}_{a.model}.npz") for c in cams}
        T = min(len(kp[c]["kp"]) for c in cams)
        # GT angular speed per segment (deg/s at 120 Hz) for the still/moving split
        for f in range(T):
            mi = s.mocap_index_for_video_frame(f)
            if mi is None or mi + 4 >= len(s.affine): continue
            seg = s.segment_frames(mi)
            if "hip" not in seg: continue
            # --- detector path: undistort, triangulate ---
            uvs, valid = [], []
            for c, cam in cams.items():
                u = kp[c]["kp"][f]; sc = kp[c]["score"][f]
                uv_our = np.full((len(KEYPOINTS), 2), np.nan); ok = np.zeros(len(KEYPOINTS), bool)
                for i, k in enumerate(KEYPOINTS):
                    j = OUR2COCO[k]
                    if j is not None and sc[j] > 0.3:
                        uv_our[i] = u[j]; ok[i] = True
                uv_our[ok] = undistort(uv_our[ok], cam)
                uvs.append(uv_our); valid.append(ok)
            X, ok3 = triangulate(list(cams.values()), np.stack(uvs), np.stack(valid))
            X = np.where(ok3[:, None], X, np.nan) @ Z2Y.T                      # -> Y-up, mm
            est = estimate_all(X[None])                                       # (1,3) axes
            # --- marker path (estimator sanity, no detector) ---
            Jm = gt_joints_from_markers(s, mi)
            estm = estimate_all((Jm @ Z2Y.T)[None]) if Jm is not None and not np.any(Jm < -1e8) else None
            motion = next((m for (x, y), m in zip(s.flags30, s.motions) if x <= f <= y), None)
            for name, A in seg.items():
                if name not in est: continue
                ax_d, loc, q_d = est[name]
                Rgt = Rot.from_matrix(Z2Y @ A[:3, :3])                          # segment frame in Y-up world
                # GT version of the same *physical* axis: take the estimator's
                # axis from marker joints as the reference (this is the axis
                # definition; the detector must reproduce it)
                if estm is None or name not in estm: continue
                ax_m, _, q_m = estm[name]
                h = lambda v: np.arctan2(v[..., 0], v[..., 2])
                if np.isnan(ax_d[0]).any() or np.isnan(ax_m[0]).any() or q_m[0] < 0.3: continue
                # body yaw relative to camera baseline: hip lateral axis heading (marker-based)
                hip_ax = estm["hip"][0][0]
                A1 = s.affine[mi, s.segment_names.index([k for k, v in __import__("slimevr_camera.data.movi", fromlist=["SEGMENTS"]).SEGMENTS.items() if v == name][0])]
                A2 = s.affine[mi + 4, s.segment_names.index([k for k, v in __import__("slimevr_camera.data.movi", fromlist=["SEGMENTS"]).SEGMENTS.items() if v == name][0])]
                if np.any(A2[:3, 3] <= -1e8): continue
                dR = Rot.from_matrix(A2[:3, :3] @ A1[:3, :3].T); speed = np.rad2deg(np.linalg.norm(dR.as_rotvec())) * 30   # deg/s (4 mocap frames = 1/30 s)
                rows.append(dict(subject=subj, frame=f, motion=motion, bone=name,
                                 err_deg=float(np.rad2deg(wrap(h(ax_d[0]) - h(ax_m[0])))),
                                 q_det=float(q_d[0]), q_mk=float(q_m[0]), body_yaw=float(np.rad2deg(h(hip_ax))),
                                 speed=float(speed), still=bool(speed < a.still_deg_s)))
    df = pd.DataFrame(rows)
    df.to_csv(a.out / f"errors_{a.model}.csv", index=False)
    pd.set_option("display.width", 200)
    print(f"{len(df)} bone-frames from subjects {a.subjects}, model {a.model}\n")
    g = df.groupby(["bone", "still"]).err_deg.agg(n="size", bias="mean", noise="std", mae=lambda x: x.abs().mean(), p95=lambda x: x.abs().quantile(.95)).round(2)
    print("heading error vs marker-derived reference, per bone (still = GT segment speed < %.0f deg/s):" % a.still_deg_s); print(g.to_string())
    # bias vs body yaw bins (still frames only)
    st = df[df.still].copy(); st["yaw_bin"] = (st.body_yaw // 45 * 45).astype(int)
    print("\nbias (mean err) by body yaw bin, still frames:"); print(st.pivot_table(index="bone", columns="yaw_bin", values="err_deg", aggfunc="mean").round(1).to_string())
    print("\nper-motion MAE (all bones):"); print(df.groupby("motion").err_deg.apply(lambda x: x.abs().mean()).round(2).sort_values().to_string())


if __name__ == "__main__":
    main()
