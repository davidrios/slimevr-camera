#!/usr/bin/env python3
"""Experiment 06 — TotalCapture (validation only, D34).

Stage A: detector heading error per tracker vs Vicon bone frames, 2 cameras,
         same method as exp 04 (undistort -> DLT -> observable axis vs the
         bone's fixed local axis; reset-referenced; 1-s rolling mean).
Stage B: END-TO-END LOOP on real IMUs. Bone orientation from the Xsens IMUs
         (R_ig R_i R_ib^-1) + injected gyro-only yaw drift (motion-driven
         random walk + scale error, as in exp 02) -> still windows (from IMU
         angular speed) -> camera heading of the same axis -> yaw correction
         -> heading error vs Vicon over the sequence, reset-only baseline vs
         corrected.  Also: 3-DoF variant (tilt from bone direction) for D31.

Usage: uv run python experiments/06-totalcapture-loop/evaluate.py --seq walking1 --cams 1 8 --model wholebody-performance
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2, numpy as np, pandas as pd
from scipy.spatial.transform import Rotation as Rot

from slimevr_camera.data.totalcapture import ROOT, load_cameras, load_sequence, BONE_TO_TRACKER, IMU_TO_BONE
from slimevr_camera.geometry import triangulate
from slimevr_camera.heading import estimate_all
from slimevr_camera.skeleton import KEYPOINTS, UP, wrap

COCO17 = ["nose", "eyeL", "eyeR", "earL", "earR", "shoulderL", "shoulderR", "elbowL", "elbowR", "wristL", "wristR", "hipL", "hipR", "kneeL", "kneeR", "ankleL", "ankleR"]
WB_TOE = {"toeL": 17, "toeR": 20}
TRACKER_BONE = {v: k for k, v in BONE_TO_TRACKER.items()}
SEG_LOCAL_AXIS = {"hip": [1, 0, 0], "chest": [1, 0, 0], "thighL": [-1, 0, 0], "thighR": [-1, 0, 0], "shinL": [-1, 0, 0], "shinR": [-1, 0, 0],
                  "footL": None, "footR": None}   # exact from Vicon joints (s1/walking1); feet: no toe joint in TotalCapture -> axis fitted from data (see fit_foot_axes)
GATE_BONES = ["hip", "chest", "thighL", "thighR", "shinL", "shinR", "footL", "footR"]
IMU_OF = {v: k for k, v in IMU_TO_BONE.items()}                # bone -> sensor


def our2model(K):
    m = {k: (COCO17.index(k) if k in COCO17 else COCO17.index("nose") if k == "head" else None) for k in KEYPOINTS}
    if K >= 23: m.update(WB_TOE)
    return m


def undistort(uv, cam):
    k = np.array([cam.dist[0] if len(cam.dist) else 0.0, 0, 0, 0], float)
    return cv2.undistortPoints(uv.reshape(-1, 1, 2).astype(np.float64), cam.K, k, P=cam.K).reshape(uv.shape)


def heading(v): return np.arctan2(v[..., 0], v[..., 2])


def camera_axes(seq, cams, kps, min_score=0.3):
    """Per frame: triangulated joints -> observable axis per tracker (world, Y-up, metres)."""
    K = kps[0]["kp"].shape[1]; o2m = our2model(K); T = min(len(k["kp"]) for k in kps)
    out = {n: (np.full((T, 3), np.nan), np.zeros(T)) for n in SEG_LOCAL_AXIS}
    for f in range(T):
        uvs, valid = [], []
        for cam, kp in zip(cams, kps):
            u = kp["kp"][f]; sc = kp["score"][f]; uv = np.full((len(KEYPOINTS), 2), np.nan); ok = np.zeros(len(KEYPOINTS), bool)
            for i, k in enumerate(KEYPOINTS):
                j = o2m[k]
                if j is not None and sc[j] > min_score: uv[i] = u[j]; ok[i] = True
            if ok.any(): uv[ok] = undistort(uv[ok], cam)
            uvs.append(uv); valid.append(ok)
        X, ok3 = triangulate(cams, np.stack(uvs), np.stack(valid)); X = np.where(ok3[:, None], X, np.nan)
        est = estimate_all(X[None])
        for n in SEG_LOCAL_AXIS:
            if n in est: out[n][0][f] = est[n][0][0]; out[n][1][f] = est[n][2][0]
    return out


def fit_foot_axes(seq, axes, min_q=0.5):
    """The observed heel->toe direction expressed in the Vicon foot frame is a
    constant (the mounting offset a reset absorbs). Fit it as the mean of
    R^T @ observed_axis over confident frames; store into SEG_LOCAL_AXIS."""
    for n in ("footL", "footR"):
        R = seq.gt_bone_world(TRACKER_BONE[n]); ax, q = axes[n]; T = min(len(R), len(ax))
        good = (q[:T] > min_q) & ~np.isnan(ax[:T]).any(1)
        loc = np.einsum("tji,tj->ti", R[:T].as_matrix()[good], ax[:T][good]); m = np.median(loc, 0); m /= np.linalg.norm(m)
        SEG_LOCAL_AXIS[n] = m.tolist(); print(f"fitted {n} axis in foot frame: {m.round(2)} (spread sd {loc.std(0).round(2)}, n={good.sum()})")


def stage_a(seq, axes, out_dir, tag):
    rows = []
    for n, loc in SEG_LOCAL_AXIS.items():
        R = seq.gt_bone_world(TRACKER_BONE[n]); ref = R.apply(np.tile(np.asarray(loc, float), (len(R), 1)))
        ax, q = axes[n]; T = min(len(ax), len(ref))
        err = np.rad2deg(wrap(heading(ax[:T]) - heading(ref[:T]))); err[(q[:T] < 0.3)] = np.nan
        speed = np.rad2deg(np.linalg.norm((R[1:] * R[:-1].inv()).as_rotvec(), axis=1)) * seq.fps; speed = np.concatenate([[0], speed])[:T]
        for f in range(T): rows.append(dict(bone=n, frame=f, err=err[f], speed=speed[f]))
    df = pd.DataFrame(rows).dropna(subset=["err"])
    df["err_reset"] = df.err - df.groupby("bone").err.transform("median")
    df["still"] = df.speed < 15
    df = df.sort_values(["bone", "frame"]); df["roll"] = df.groupby("bone").err_reset.transform(lambda x: x.rolling(60, min_periods=50).mean())
    st = lambda x: pd.Series(dict(n=len(x), bias=x.mean(), sd=x.std(), mae=x.abs().mean(), p95=x.abs().quantile(.95)))
    print(f"\n=== Stage A ({tag}): detector heading error vs Vicon, per frame (reset-referenced)"); print(df.groupby(["bone", "still"]).err_reset.apply(st).unstack().round(2).to_string())
    print("\n1-s rolling mean:"); print(df.dropna(subset=["roll"]).groupby("bone").roll.apply(st).unstack().round(2).to_string())
    df.to_csv(out_dir / f"stageA_{tag}.csv", index=False)
    return df


def inject_drift(R: Rot, fps, rng, rw=0.02, scale=0.004, mrw=0.05):
    """Yaw drift about world-up: static rw (deg/sqrt s) + signed scale error + motion-driven random walk (deg/sqrt deg)."""
    T = len(R); dt = 1 / fps
    rel = R[1:] * R[:-1].inv(); rv = rel.as_rotvec(); gross = np.concatenate([[0], np.rad2deg(np.linalg.norm(rv, axis=1))]); wy = np.concatenate([[0], rv @ UP])
    k = rng.uniform(-scale, scale)
    d = np.cumsum(np.deg2rad(rw) * np.sqrt(dt) * rng.standard_normal(T) + k * wy + np.deg2rad(mrw) * np.sqrt(gross) * rng.standard_normal(T))
    d -= d[0]
    return Rot.from_rotvec(np.outer(d, UP)) * R, d, gross


def pose_descriptor(seq):
    """Per-frame pose descriptor from the *IMU-derived* bone orientations (what the
    server has): unit bone axes (local Y? -> use full rotation matrices rel. to hip yaw)
    of the tracker bones, expressed in a hip-yaw-aligned frame so the descriptor is
    heading-invariant."""
    Rh = seq.imu_bone_world(IMU_OF["Hips"]); T = len(Rh)
    yaw = heading(Rh.apply(np.tile([1.0, 0, 0], (T, 1)))); Ryaw = Rot.from_rotvec(np.outer(-yaw, UP))
    feats = []
    for b in GATE_BONES:
        Rb = seq.imu_bone_world(IMU_OF[TRACKER_BONE[b]])[:T]
        feats.append((Ryaw * Rb).as_matrix()[:, :, 1])              # bone local Y axis in hip-yaw frame
    return np.concatenate(feats, 1)                                 # (T, 3*len(GATE_BONES))


def familiar_windows(seq, trusted_s=3.0, still_deg_s=20.0, min_still_s=0.5, max_pose_dist=0.35):
    """Windows that are still AND whose pose is close to a pose seen in the trusted
    window (the first `trusted_s` seconds, standing in as 'after the manual reset')."""
    fps = seq.fps; D = pose_descriptor(seq); T = len(D)
    trusted = D[: int(trusted_s * fps)]
    dist = np.array([np.min(np.linalg.norm(trusted - d, axis=1)) for d in D])          # nearest trusted pose
    speeds = []
    for sensor in [IMU_OF[TRACKER_BONE[b]] for b in GATE_BONES]:
        Ri = seq.imu_bone_world(sensor)[:T]; speeds.append(np.concatenate([[0], np.rad2deg(np.linalg.norm((Ri[1:] * Ri[:-1].inv()).as_rotvec(), axis=1)) * fps]))
    ok = (np.max(speeds, 0) < still_deg_s) & (dist < max_pose_dist)
    wins, i = [], 0
    while i < T:
        if ok[i]:
            j = i
            while j < T and ok[j]: j += 1
            if j - i >= min_still_s * fps: wins.append((i, j))
            i = j
        else: i += 1
    return wins, dist


def stage_b(seq, axes, out_dir, tag, seed=0, still_deg_s=20.0, min_still_s=0.5, familiar=True):
    rng = np.random.default_rng(seed); fps = seq.fps
    # still windows from the IMU angular speeds (all sensors)
    speeds = []
    for sensor in [IMU_OF[TRACKER_BONE[b]] for b in GATE_BONES]:
        Ri = seq.imu_bone_world(sensor); speeds.append(np.concatenate([[0], np.rad2deg(np.linalg.norm((Ri[1:] * Ri[:-1].inv()).as_rotvec(), axis=1)) * fps]))
    sp = np.max(speeds, 0); still = sp < still_deg_s
    if familiar:
        wins, dist = familiar_windows(seq, still_deg_s=still_deg_s, min_still_s=min_still_s)
        print(f"\n=== Stage B ({tag}): end-to-end loop, {len(wins)} FAMILIAR still windows (pose within 0.35 of the first 3 s; >= {min_still_s} s; < {still_deg_s} deg/s)")
        print("    windows (s):", [(round(a / fps, 1), round(b / fps, 1)) for a, b in wins][:12])
    else:
        wins, i = [], 0
        while i < len(still):
            if still[i]:
                j = i
                while j < len(still) and still[j]: j += 1
                if j - i >= min_still_s * fps: wins.append((i, j))
                i = j
            else: i += 1
        print(f"\n=== Stage B ({tag}): end-to-end loop, {len(wins)} still windows (>= {min_still_s} s, all IMUs < {still_deg_s} deg/s)")
    rows = []
    for n, loc in SEG_LOCAL_AXIS.items():
        bone = TRACKER_BONE[n]; sensor = IMU_OF[bone]; loc = np.asarray(loc, float)
        Rv = seq.gt_bone_world(bone); Ri = seq.imu_bone_world(sensor); T = min(len(Rv), len(Ri), len(axes[n][0]))
        Rv, Ri = Rv[:T], Ri[:T]
        Rd, d, gross = inject_drift(Ri, fps, rng)
        ax_cam, q = axes[n]
        def yaw_err(R): return np.rad2deg(wrap(heading(R.apply(np.tile(loc, (T, 1)))) - heading(Rv.apply(np.tile(loc, (T, 1))))))
        e_imu, e_drift = yaw_err(Ri), yaw_err(Rd)
        # camera correction in still windows: replace yaw of the drifted IMU axis by the camera axis heading (window mean), applied from window end
        c = np.zeros(T); cur = 0.0
        for (a, b) in wins:
            b = min(b, T); f = ax_cam[a:b]; qq = q[a:b]; good = ~np.isnan(f).any(1) & (qq > 0.3)
            if good.mean() < 0.5: continue
            h_cam = heading(f[good].mean(0)); h_imu = heading(Rd[a:b].apply(np.tile(loc, (b - a, 1))).mean(0))
            cur = float(wrap(h_cam - h_imu)); c[b:] = cur
        Rc = Rot.from_rotvec(np.outer(c, UP)) * Rd; e_corr = yaw_err(Rc)
        st = lambda e: dict(rms=float(np.sqrt(np.nanmean(e ** 2))), p95=float(np.nanpercentile(np.abs(e), 95)))
        rows.append(dict(bone=n, imu_only=st(e_imu)["rms"], drifted=st(e_drift)["rms"], corrected=st(e_corr)["rms"], corrected_p95=st(e_corr)["p95"], n_corrections=int((np.diff(c) != 0).sum())))
    df = pd.DataFrame(rows); print(df.round(2).to_string(index=False)); df.to_csv(out_dir / f"stageB_{tag}.csv", index=False)
    print("imu_only = calibrated Xsens vs Vicon (the floor); drifted = + injected drift; corrected = camera yaw correction in still windows")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--subject", type=int, default=1); ap.add_argument("--seq", default="walking1")
    ap.add_argument("--cams", type=int, nargs="+", default=[1, 8]); ap.add_argument("--model", default="wholebody-performance"); ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    a = ap.parse_args(); a.out.mkdir(exist_ok=True)
    seq = load_sequence(a.subject, a.seq); cams_all = load_cameras(); cams = [cams_all[c - 1] for c in a.cams]
    kps = [np.load(ROOT / "keypoints" / f"s{a.subject}_{a.seq}_cam{c}_{a.model}.npz") for c in a.cams]
    tag = f"{a.seq}_cams{''.join(map(str, a.cams))}_{a.model}"
    axes = camera_axes(seq, cams, kps)
    fit_foot_axes(seq, axes)
    stage_a(seq, axes, a.out, tag); stage_b(seq, axes, a.out, tag)
