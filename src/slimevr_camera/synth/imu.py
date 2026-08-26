"""Synthetic IMU trackers: true bone orientation + yaw drift.

Drift model (VIP-style, D14): measured = R_y(delta_psi(t)) * true, one angle
about world-up per tracker. delta_psi grows by
  - random walk        sigma_rw * sqrt(dt)
  - constant bias      bias * dt
  - scale-factor error k * |yaw rate| * dt   (dominant per drift-lab/FINDINGS.md)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation as Rot

from ..skeleton import UP, heading_of, wrap


@dataclass
class ImuConfig:
    rw_deg_per_sqrt_s: float = 0.02
    bias_deg_per_min: tuple[float, float] = (-3.0, 3.0)   # drift-lab run A: BNO085 static 0.2–4.4 deg/min per unit    # per tracker, uniform
    scale_error: tuple[float, float] = (-0.004, 0.004)        # per tracker, fraction of yaw rotation
    gyro_noise_deg_s: float = 0.3
    seed: int = 1


def simulate(world: dict[str, Rot], fps: float, cfg: ImuConfig, trackers: list[str]):
    """Returns dict(meas: name->Rotation, drift: name->(T,) rad, gyro_speed: (T, n) rad/s)."""
    rng = np.random.default_rng(cfg.seed)
    dt = 1.0 / fps
    meas, drift, speeds = {}, {}, []
    for name in trackers:
        R = world[name]
        T = len(R)
        psi = heading_of(R)
        yaw_rate = np.abs(wrap(np.diff(psi, prepend=psi[0]))) / dt
        bias = np.deg2rad(rng.uniform(*cfg.bias_deg_per_min)) / 60
        k = rng.uniform(*cfg.scale_error)
        rw = np.deg2rad(cfg.rw_deg_per_sqrt_s) * np.sqrt(dt) * rng.standard_normal(T)
        d = np.cumsum(rw + bias * dt + k * yaw_rate * dt)
        d -= d[0]   # perfect full reset at t=0
        drift[name] = d
        meas[name] = Rot.from_rotvec(np.outer(d, UP)) * R
        # angular speed as a gyro would see it (finite difference + noise)
        rel = R[1:] * R[:-1].inv()
        w = np.linalg.norm(rel.as_rotvec(), axis=1) / dt
        w = np.concatenate([[w[0]], w]) + np.deg2rad(cfg.gyro_noise_deg_s) * np.abs(rng.standard_normal(T))
        speeds.append(w)
    return dict(meas=meas, drift=drift, gyro_speed=np.stack(speeds, 1))
