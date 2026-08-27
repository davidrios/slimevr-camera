#!/usr/bin/env python3
"""Figures for experiment 04 from results/errors_*.csv and windows_*.csv."""
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd, cv2
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

R = Path(__file__).parent / "results"; R.mkdir(exist_ok=True)
ORDER = ["footL", "footR", "chest", "shinL", "shinR", "hip", "thighL", "thighR"]
NAMES = dict(footL="foot L", footR="foot R", chest="chest", shinL="shin L", shinR="shin R", hip="hip", thighL="thigh L", thighR="thigh R")


def rolling(df, n=30):
    return df.sort_values(["subject", "bone", "frame"]).set_index(["subject", "bone", "frame"]).err_reset.groupby(level=[0, 1]).transform(lambda x: x.rolling(n, min_periods=25).mean()).dropna().reset_index()


def fig_bones(model, title):
    df = pd.read_csv(R / f"errors_{model}.csv"); r = rolling(df)
    bones = [b for b in ORDER if b in set(r.bone)]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    data = [r[r.bone == b].err_reset.values for b in bones]
    ax.axhspan(-5, 5, color="tab:green", alpha=0.12, label="±5° budget")
    vp = ax.violinplot(data, showmedians=True, widths=0.85)
    ax.set_xticks(range(1, len(bones) + 1), [NAMES[b] for b in bones]); ax.set_ylim(-40, 40)
    ax.set_ylabel("heading error after 1-s averaging (°)"); ax.set_title(title); ax.legend(loc="upper left")
    for i, d in enumerate(data, 1): ax.text(i, 36, f"sd {np.std(d):.1f}°", ha="center", fontsize=8)
    fig.tight_layout(); fig.savefig(R / f"fig_bones_{model}.png", dpi=120); plt.close(fig)


def fig_timeline(model, subj=1):
    df = pd.read_csv(R / f"errors_{model}.csv"); r = rolling(df); r = r[r.subject == subj]
    fig, ax = plt.subplots(figsize=(12, 4.2))
    for b, c in zip(["chest", "hip", "thighL", "shinL", "footL"], ["tab:blue", "tab:orange", "tab:red", "tab:green", "tab:purple"]):
        d = r[r.bone == b]
        if len(d): ax.plot(d.frame / 30, d.err_reset, lw=0.9, label=NAMES[b], color=c)
    ax.axhspan(-5, 5, color="tab:green", alpha=0.12)
    # motion labels
    from slimevr_camera.data.movi import load_subject
    s = load_subject(subj)
    for (a, b_), m in zip(s.flags30, s.motions):
        ax.axvline(a / 30, color="k", alpha=0.15, lw=0.6); ax.text((a + b_) / 60, 33, m.replace("_", "\n"), fontsize=6, ha="center", va="top", rotation=0)
    ax.set_ylim(-35, 35); ax.set_xlabel("s"); ax.set_ylabel("1-s mean heading error (°)"); ax.set_title(f"MoVi subject {subj}, {model}: error is slowly varying and pose-dependent, not white noise"); ax.legend(loc="lower left", ncol=5, fontsize=8)
    fig.tight_layout(); fig.savefig(R / f"fig_timeline_{model}_s{subj}.png", dpi=120); plt.close(fig)


def fig_yaw(model):
    df = pd.read_csv(R / f"errors_{model}.csv"); r = rolling(df)
    yaw = df.groupby(["subject", "bone", "frame"]).body_yaw.first().reset_index()
    r = r.merge(yaw, on=["subject", "bone", "frame"])
    bones = [b for b in ["chest", "hip", "thighL", "shinL", "footL"] if b in set(r.bone)]
    fig, axes = plt.subplots(1, len(bones), figsize=(3.2 * len(bones), 3.4), sharey=True)
    for ax, b in zip(np.atleast_1d(axes), bones):
        d = r[r.bone == b]; ax.scatter(d.body_yaw, d.err_reset, s=2, alpha=0.15)
        bins = np.arange(-180, 181, 30); idx = np.digitize(d.body_yaw, bins)
        med = [d.err_reset[idx == i].median() if (idx == i).sum() > 30 else np.nan for i in range(1, len(bins))]
        ax.plot(bins[:-1] + 15, med, "r-o", ms=3, label="median per 30°"); ax.axhspan(-5, 5, color="tab:green", alpha=0.12)
        ax.set_title(NAMES[b]); ax.set_xlabel("body yaw vs cameras (°)"); ax.set_ylim(-30, 30)
    np.atleast_1d(axes)[0].set_ylabel("1-s mean heading error (°)"); np.atleast_1d(axes)[0].legend(fontsize=7)
    fig.suptitle("Heading error depends on viewing direction (pose-dependent bias)"); fig.tight_layout(); fig.savefig(R / f"fig_yaw_{model}.png", dpi=120); plt.close(fig)


def fig_models(models, subjects):
    fig, ax = plt.subplots(figsize=(8, 3.8)); w = 0.8 / len(models)
    bones = ["chest", "hip", "shinL", "shinR", "thighL", "thighR"]
    for i, m in enumerate(models):
        df = pd.read_csv(R / f"errors_{m}.csv"); df = df[df.subject.isin(subjects)]; r = rolling(df)
        sds = [r[r.bone == b].err_reset.std() for b in bones]
        ax.bar(np.arange(len(bones)) + i * w, sds, w, label=m)
    ax.axhline(5, color="tab:green", ls="--", label="5° budget"); ax.set_xticks(np.arange(len(bones)) + w * (len(models) - 1) / 2, [NAMES[b] for b in bones])
    ax.set_ylabel("sd of 1-s mean error (°)"); ax.set_title(f"Detector size barely matters (subjects {subjects})"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(R / "fig_models.png", dpi=120); plt.close(fig)


def fig_overlay(subj=1, frame=1000, model="wholebody-performance"):
    from slimevr_camera.data.movi import ROOT, load_camera, load_subject
    s = load_subject(subj); mi = s.mocap_index_for_video_frame(frame)
    M = {n: s.markers[mi, i] for i, n in enumerate(s.marker_names)}
    J = np.array([M[k] for k in ("HEAD", "LSJC", "RSJC", "LEJC", "REJC", "LWJC", "RWJC", "LHIP", "RHIP", "LKJC", "RKJC", "LAJC", "RAJC", "LTOE", "RTOE")])
    imgs = []
    for c in ("PG1", "PG2"):
        cam = load_camera(c); cap = cv2.VideoCapture(str(s.video_path(c))); cap.set(cv2.CAP_PROP_POS_FRAMES, frame); _, img = cap.read(); cap.release()
        Xc = J @ cam.R.T + cam.t; p = (Xc @ cam.K.T)[:, :2] / Xc[:, 2:3]
        for u, v in p: cv2.circle(img, (int(u), int(v)), 5, (0, 255, 0), 1)
        kp = np.load(ROOT / "keypoints" / f"F_{c}_Subject_{subj}_{model}.npz"); k = kp["kp"][frame]; sc = kp["score"][frame]
        for j in list(range(17)) + [17, 20]:
            if sc[j] > 0.3: cv2.circle(img, (int(k[j, 0]), int(k[j, 1])), 3, (0, 0, 255), -1)
        cv2.putText(img, f"{c}: green = marker joint centres (reprojected), red = {model}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        imgs.append(img)
    cv2.imwrite(str(R / "fig_overlay.png"), np.hstack(imgs))


if __name__ == "__main__":
    fig_bones("body-balanced", "MoVi, 5 subjects, RTMPose-m (body-balanced), 2 cameras 800×600 @ 4.5 m")
    fig_timeline("body-balanced", 1)
    fig_yaw("body-balanced")
    fig_models(["body-balanced", "wholebody-performance"], [1, 2])
    try: fig_bones("wholebody-performance", "MoVi, RTMPose-x wholebody (feet available)")
    except Exception as e: print("wholebody fig skipped:", e)
    fig_overlay()
    print("wrote", sorted(p.name for p in R.glob("fig_*.png")))
