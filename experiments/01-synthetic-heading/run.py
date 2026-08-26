"""Experiment 01: can 2 noisy cameras recover per-tracker heading during still
windows well enough to cancel injected yaw drift?  Synthetic keypoint level."""
from __future__ import annotations

import argparse, json
from pathlib import Path

import numpy as np

from slimevr_camera.pipeline import GateConfig, apply_corrections, heading_errors, measure_windows, still_windows, summarize, triangulate_sequence
from slimevr_camera.skeleton import TRACKER_BONES, forward_kinematics, heading_of, keypoint_array, wrap
from slimevr_camera.synth.camera import ObsConfig, default_rig, observe
from slimevr_camera.synth.imu import ImuConfig, simulate
from slimevr_camera.synth.motion import MotionConfig, generate


def run(pixel_noise: float, duration: float, seed: int, fps: float = 30.0, plot: Path | None = None):
    m = generate(MotionConfig(duration_s=duration, fps=fps, seed=seed))
    world, joints = forward_kinematics(m["local"], m["root_pos"])
    imu = simulate(world, fps, ImuConfig(seed=seed + 1), TRACKER_BONES)
    cams = default_rig()
    uvs, valid = observe(cams, keypoint_array(joints), ObsConfig(pixel_noise=pixel_noise, seed=seed + 2))
    P = triangulate_sequence(cams, uvs, valid)
    gate = GateConfig()
    wins = still_windows(imu["gyro_speed"], fps, gate)
    ms = measure_windows(P, imu["meas"], wins, gate)
    corrected, corr = apply_corrections(imu["meas"], ms)
    before = summarize(heading_errors(world, imu["meas"]))
    after = summarize(heading_errors(world, corrected))
    # camera-only measurement error inside windows (the number the literature lacks)
    cam_err = {n: [] for n in TRACKER_BONES}
    from slimevr_camera.heading import estimate_all
    from slimevr_camera.skeleton import heading_of_vec
    locs = {n: v[1] for n, v in estimate_all(P).items()}
    for mm in ms:
        for n, h in mm.heading_cam.items():
            ax = world[n][mm.window.start:mm.window.end].apply(np.tile(locs[n], (mm.window.end - mm.window.start, 1)))
            cam_err[n].append(np.rad2deg(wrap(h - heading_of_vec(ax.mean(0)))))
    cam_stats = {n: (dict(rms=float(np.sqrt(np.mean(np.square(e)))), n=len(e)) if e else dict(rms=float("nan"), n=0)) for n, e in cam_err.items()}
    if plot:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        eb, ea = heading_errors(world, imu["meas"]), heading_errors(world, corrected)
        fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
        for n in ["hip", "chest", "thighL", "shinL", "footL", "upperArmL"]:
            axes[0].plot(m["t"], eb[n], label=n); axes[1].plot(m["t"], ea[n], label=n)
        for w in wins:
            for ax in axes: ax.axvspan(w.start / fps, w.end / fps, color="k", alpha=0.08)
        axes[0].set_ylabel("heading err, uncorrected (°)"); axes[1].set_ylabel("corrected (°)"); axes[1].set_xlabel("s")
        axes[0].legend(ncol=6, fontsize=8); fig.tight_layout(); fig.savefig(plot, dpi=110)
    return dict(pixel_noise=pixel_noise, seed=seed, n_windows=len(wins), before=before, after=after, camera_window_error=cam_stats)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--noise", type=float, nargs="+", default=[1, 3, 6, 10])
    ap.add_argument("--duration", type=float, default=600)
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    a = ap.parse_args()
    a.out.mkdir(exist_ok=True)
    rows = []
    for noise in a.noise:
        for seed in range(a.seeds):
            r = run(noise, a.duration, seed, plot=a.out / f"noise{noise:g}_seed{seed}.png" if seed == 0 else None)
            rows.append(r)
            print(f"noise={noise:g}px seed={seed} windows={r['n_windows']}")
            for n in TRACKER_BONES:
                print(f"  {n:11s} before rms={r['before'][n]['rms']:6.2f}  after rms={r['after'][n]['rms']:6.2f} p95={r['after'][n]['p95']:6.2f}  cam-window rms={r['camera_window_error'][n]['rms']:6.2f} (n={r['camera_window_error'][n]['n']})")
    (a.out / "results.json").write_text(json.dumps(rows, indent=1))
