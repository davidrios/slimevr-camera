#!/usr/bin/env python3
"""On-body drift vs gross motion (experiment 03).

Input: a DriftLogger CSV (raw getRawRotation(), 100 Hz recommended).
Holds are detected automatically (all-axis angular speed below a threshold
for at least --min-hold seconds) or given with --holds "mm:ss,mm:ss,...".
The FIRST hold is the reset pose (t0).  Every later hold in the same pose
gives the accumulated yaw error per tracker directly.

Usage: uv run python experiments/03-onbody-drift/analyze.py LOG.csv [--holds ...] [--plot out.png]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as Rot

UP = np.array([0.0, 1.0, 0.0])


def load(path: Path) -> dict[str, tuple[np.ndarray, Rot]]:
    d = pd.read_csv(path, usecols=["mono_ms", "tracker_id", "name", "qw", "qx", "qy", "qz"])
    out = {}
    t_origin = d["mono_ms"].min() / 1000.0
    for tid, g in d.groupby("tracker_id"):
        g = g.sort_values("mono_ms")
        q = g[["qx", "qy", "qz", "qw"]].to_numpy(float)          # scipy order (x,y,z,w)
        # drop identity placeholders before the first real packet (drift-lab pitfall)
        real = ~np.isclose(np.abs(q[:, 3]), 1.0, atol=1e-6)
        first = np.argmax(real) if real.any() else 0
        t = g["mono_ms"].to_numpy(float)[first:] / 1000.0 - t_origin
        out[str(tid)] = (t, Rot.from_quat(q[first:]))
    return out


def angular_speed(t, R):
    rel = R[1:] * R[:-1].inv()
    w = np.rad2deg(np.linalg.norm(rel.as_rotvec(), axis=1)) / np.diff(t)
    return np.concatenate([[0.0], w])


def detect_holds(t, speed, thresh_deg_s, min_hold_s):
    still = speed < thresh_deg_s
    holds, i = [], 0
    while i < len(t):
        if still[i]:
            j = i
            while j < len(t) and still[j]:
                j += 1
            if t[j - 1] - t[i] >= min_hold_s:
                holds.append((i, j))
            i = j
        else:
            i += 1
    return holds


def mean_rot(R: Rot) -> Rot | None:
    if len(R) == 0:
        return None
    q = R.as_quat(); q = q * np.sign(q[:, 3:4] + 1e-12)
    m = q.mean(0); return Rot.from_quat(m / np.linalg.norm(m))


def heading_err_deg(R0: Rot, R1: Rot) -> float:
    """Yaw of R1 relative to R0: heading change of the tracker axis that was
    most horizontal at t0 (same-axis method, see slimevr_camera.heading)."""
    axes = R0.apply(np.eye(3))
    a = np.argmin(np.abs(axes[:, 1]))              # most horizontal local axis
    v0, v1 = axes[a], R1.apply(np.eye(3)[a])
    h = lambda v: np.arctan2(v[0], v[2])
    return float(np.rad2deg((h(v1) - h(v0) + np.pi) % (2 * np.pi) - np.pi))


def tilt_deg(R0: Rot, R1: Rot) -> float:
    up0, up1 = R0.inv().apply(UP), R1.inv().apply(UP)
    return float(np.rad2deg(np.arccos(np.clip(up0 @ up1, -1, 1))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--holds", help="comma-separated mm:ss (or seconds) hold *start* times; else auto-detect")
    ap.add_argument("--hold-len", type=float, default=15.0, help="seconds to average when --holds given")
    ap.add_argument("--speed", type=float, default=5.0, help="auto-detect: max deg/s to count as still")
    ap.add_argument("--min-hold", type=float, default=10.0)
    ap.add_argument("--plot", type=Path)
    a = ap.parse_args()

    data = load(a.csv)
    names = sorted(data)
    print(f"{a.csv.name}: {len(names)} trackers, {max(t[-1] for t, _ in data.values()) / 60:.1f} min")

    # holds on the common timeline: use the tracker with the most samples for detection
    ref = max(names, key=lambda n: len(data[n][0]))
    t_ref, R_ref = data[ref]
    if a.holds:
        starts = [sum(float(x) * 60 ** i for i, x in enumerate(reversed(s.split(":")))) for s in a.holds.split(",")]
        holds_t = [(s, s + a.hold_len) for s in starts]
    else:
        sp_all = np.zeros(len(t_ref))
        for n in names:                                   # still = ALL trackers still
            t, R = data[n]
            sp_all = np.maximum(sp_all, np.interp(t_ref, t, angular_speed(t, R)))
        holds_t = [(t_ref[i], t_ref[j - 1]) for i, j in detect_holds(t_ref, sp_all, a.speed, a.min_hold)]
    print(f"holds ({len(holds_t)}):", ", ".join(f"{s / 60:.1f}–{e / 60:.1f} min" for s, e in holds_t))
    if len(holds_t) < 2:
        print("need >= 2 holds (reset pose + at least one return)"); return

    rows = []
    for n in names:
        t, R = data[n]
        sp = angular_speed(t, R)
        Rh = [mean_rot(R[(t >= s) & (t <= e)]) for s, e in holds_t]
        gross = np.cumsum(sp * np.gradient(t))              # deg of rotation travelled, all axes
        g_at = [np.interp(s, t, gross) for s, _ in holds_t]
        for k in range(1, len(holds_t)):
            if Rh[0] is None or Rh[k] is None or Rh[k - 1] is None:
                continue
            rows.append(dict(tracker=n, hold=k, t_min=holds_t[k][0] / 60,
                             yaw_err=heading_err_deg(Rh[0], Rh[k]), yaw_inc=heading_err_deg(Rh[k - 1], Rh[k]),
                             tilt=tilt_deg(Rh[0], Rh[k]), gross_interval=g_at[k] - g_at[k - 1]))
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print("\nPer hold (yaw_err = vs reset pose, yaw_inc = vs previous hold, gross = deg rotated in the interval):")
    print(df.pivot(index="hold", columns="tracker", values="yaw_err").round(2).to_string())
    print("\nincrement per hold:"); print(df.pivot(index="hold", columns="tracker", values="yaw_inc").round(2).to_string())
    print("\ngross motion per interval (deg):"); print(df.pivot(index="hold", columns="tracker", values="gross_interval").round(0).to_string())
    print("\ntilt vs reset (deg):"); print(df.pivot(index="hold", columns="tracker", values="tilt").round(2).to_string())

    # sigma_m fit: E[inc^2] = sigma_m^2 * gross  (+ floor^2), per tracker, through origin with floor
    print("\nsigma_m per tracker (deg per sqrt(deg of gross rotation)), least squares on inc^2 = s^2*gross + f^2:")
    for n in names:
        d = df[df.tracker == n]
        if len(d) < 2:
            continue
        A = np.stack([d.gross_interval, np.ones(len(d))], 1)
        (s2, f2), *_ = np.linalg.lstsq(A, d.yaw_inc ** 2, rcond=None)
        print(f"  {n:6s} sigma_m={np.sqrt(max(s2, 0)):.4f}  floor={np.sqrt(max(f2, 0)):.2f} deg  n={len(d)}  mean|inc|={d.yaw_inc.abs().mean():.2f}  mean gross/interval={d.gross_interval.mean():.0f}")
    pooled = df.groupby("hold").agg(g=("gross_interval", "mean"), inc2=("yaw_inc", lambda x: (x ** 2).mean()))
    A = np.stack([pooled.g, np.ones(len(pooled))], 1)
    (s2, f2), *_ = np.linalg.lstsq(A, pooled.inc2, rcond=None)
    print(f"  POOLED sigma_m={np.sqrt(max(s2, 0)):.4f}  floor={np.sqrt(max(f2, 0)):.2f} deg")

    if a.plot:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
        for n in names:
            d = df[df.tracker == n]; ax[0].plot(d.t_min, d.yaw_err, "o-", label=n); ax[1].plot(d.gross_interval, d.yaw_inc.abs(), "o", label=n)
        ax[0].set_xlabel("min"); ax[0].set_ylabel("yaw error vs reset pose (°)"); ax[0].legend(fontsize=7)
        ax[1].set_xlabel("gross rotation in interval (°)"); ax[1].set_ylabel("|yaw increment| (°)")
        fig.tight_layout(); fig.savefig(a.plot, dpi=110)


if __name__ == "__main__":
    main()
