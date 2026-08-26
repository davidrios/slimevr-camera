"""Experiment 02: can the camera *calibrate* the gyro scale error, not just
reset heading?  Each window gives (correction change, yaw travelled) -> RLS
estimate of k per tracker -> feed-forward between windows.  Sweep the
still-window cadence to see how much cadence can be relaxed."""
from __future__ import annotations

import argparse, json
from pathlib import Path

import numpy as np

from slimevr_camera.pipeline import GateConfig, apply_corrections, heading_errors, measure_windows, still_windows, summarize, triangulate_sequence
from slimevr_camera.skeleton import TRACKER_BONES, forward_kinematics, keypoint_array
from slimevr_camera.synth.camera import ObsConfig, default_rig, observe
from slimevr_camera.synth.imu import ImuConfig, simulate
from slimevr_camera.synth.motion import MotionConfig, generate

LONG = ["hip", "chest", "thighL", "thighR", "shinL", "shinR"]


def run(active_s, seed, duration=1200.0, fps=30.0, noise=3.0, plot=None, motion_rw=0.05):
    m = generate(MotionConfig(duration_s=duration, fps=fps, active_s=active_s, seed=seed))
    world, joints = forward_kinematics(m["local"], m["root_pos"])
    imu_cfg = ImuConfig(seed=seed + 1, motion_rw_deg_per_sqrt_deg=motion_rw)
    imu = simulate(world, fps, imu_cfg, TRACKER_BONES)
    rng = np.random.default_rng(imu_cfg.seed)      # replay the k draws for truth
    k_true = {}
    for name in TRACKER_BONES:
        rng.uniform(*imu_cfg.bias_deg_per_min); k_true[name] = rng.uniform(*imu_cfg.scale_error)
        rng.standard_normal(len(world[name])); rng.standard_normal(len(world[name])); rng.standard_normal(len(world[name]))
    cams = default_rig()
    uvs, valid = observe(cams, keypoint_array(joints), ObsConfig(pixel_noise=noise, seed=seed + 2))
    P = triangulate_sequence(cams, uvs, valid)
    gate = GateConfig()
    wins = still_windows(imu["gyro_speed"], fps, gate)
    ms = measure_windows(P, imu["meas"], wins, gate)
    res = {}
    for label, learn in (("reset", False), ("reset+scale", True)):
        corrected, corr, khat = apply_corrections(imu["meas"], ms, fps, learn_scale=learn)
        err = heading_errors(world, corrected)
        res[label] = dict(summary=summarize(err), khat=khat, err=err)
    out = dict(active_s=active_s, seed=seed, n_windows=len(wins), interval_s=duration / max(len(wins), 1),
               k_true=k_true, k_hat=res["reset+scale"]["khat"],
               reset={n: res["reset"]["summary"][n]["rms"] for n in TRACKER_BONES},
               scale={n: res["reset+scale"]["summary"][n]["rms"] for n in TRACKER_BONES})
    if plot:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
        for ax, label in zip(axes, ("reset", "reset+scale")):
            for n in ["hip", "chest", "thighL", "shinL", "footL", "upperArmL"]:
                ax.plot(m["t"], res[label]["err"][n], label=n, lw=0.8)
            for w in wins: ax.axvspan(w.start / fps, w.end / fps, color="k", alpha=0.08)
            ax.set_ylabel(f"heading err, {label} (°)")
        axes[0].legend(ncol=6, fontsize=8); axes[1].set_xlabel("s"); fig.tight_layout(); fig.savefig(plot, dpi=110)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--motion-rw", type=float, default=0.05, help="yaw std per sqrt(deg gross rotation); 0 = turntable-only model")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    a = ap.parse_args(); a.out.mkdir(exist_ok=True)
    cadences = {"~35s": (15.0, 40.0), "~2min": (90.0, 150.0), "~5min": (240.0, 360.0)}
    rows = []
    for label, act in cadences.items():
        for seed in range(a.seeds):
            r = run(act, seed, plot=a.out / f"mrw{a.motion_rw:g}_cadence{label}_seed{seed}.png" if seed == 0 else None, motion_rw=a.motion_rw)
            r["cadence"] = label; rows.append(r)
            print(f"{label} seed={seed} windows={r['n_windows']} (every {r['interval_s']:.0f} s)")
    (a.out / f"results_mrw{a.motion_rw:g}.json").write_text(json.dumps(rows, indent=1))
    print("\nheading RMS (deg), long bones mean / upper arms mean, over 20 min; k_hat error (%, long bones)")
    print(f"{'cadence':8s} {'reset':>8s} {'+scale':>8s} | {'reset':>8s} {'+scale':>8s} | k_err")
    for label in cadences:
        rs = [r for r in rows if r["cadence"] == label]
        f = lambda key, names: np.mean([r[key][n] for r in rs for n in names])
        kerr = np.mean([abs(r["k_hat"][n] - r["k_true"][n]) * 100 for r in rs for n in LONG])
        print(f"{label:8s} {f('reset', LONG):8.2f} {f('scale', LONG):8.2f} | {f('reset', ['upperArmL','upperArmR']):8.2f} {f('scale', ['upperArmL','upperArmR']):8.2f} | {kerr:.3f}")
