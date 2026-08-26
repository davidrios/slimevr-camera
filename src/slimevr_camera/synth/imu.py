"""Synthetic IMU trackers: true bone orientation + yaw drift.

Drift model (VIP-style, D14): measured = R_y(delta_psi(t)) * true, one angle
about world-up per tracker. delta_psi grows by
  - static random walk   sigma_rw * sqrt(dt)                      (~0 per drift-lab run A)
  - constant bias        bias * dt                                (~0 per drift-lab run A)
  - yaw scale factor     k * yaw_rate * dt   (signed; turntable: +-0.4 %)
  - MOTION-DRIVEN RANDOM WALK  sigma_m * sqrt(gross_rotation_increment)
      Unpredictable yaw increments whose variance scales with the gross 3D
      angular motion (all axes). This stands in for per-axis scale +
      cross-axis misalignment + gravity-correction leakage, which do NOT
      cancel on back-and-forth motion (David's field observation: drift with
      modest movement and no turning). Its magnitude is NOT yet measured —
      sweep it. This term is the reason the project exists.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation as Rot

from ..skeleton import UP, yaw_rate


@dataclass
class ImuConfig:
    rw_deg_per_sqrt_s: float = 0.02
    bias_deg_per_min: tuple[float, float] = (-0.02, 0.02)   # drift-lab run A: static drift < 1 deg/hour
    scale_error: tuple[float, float] = (-0.0045, 0.0045)     # drift-lab turntable: +0.43 % / -0.23 % measured
    motion_rw_deg_per_sqrt_deg: float = 0.05   # yaw std per sqrt(degree of gross 3D rotation); UNMEASURED
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
        wy = yaw_rate(R, fps)
        bias = np.deg2rad(rng.uniform(*cfg.bias_deg_per_min)) / 60
        k = rng.uniform(*cfg.scale_error)
        rw = np.deg2rad(cfg.rw_deg_per_sqrt_s) * np.sqrt(dt) * rng.standard_normal(T)
        rel = R[1:] * R[:-1].inv()
        gross = np.concatenate([[0.0], np.rad2deg(np.linalg.norm(rel.as_rotvec(), axis=1))])   # deg per frame, all axes
        mrw = np.deg2rad(cfg.motion_rw_deg_per_sqrt_deg) * np.sqrt(gross) * rng.standard_normal(T)
        d = np.cumsum(rw + bias * dt + k * wy * dt + mrw)
        d -= d[0]   # perfect full reset at t=0
        drift[name] = d
        meas[name] = Rot.from_rotvec(np.outer(d, UP)) * R
        # angular speed as a gyro would see it (finite difference + noise)
        w = np.deg2rad(gross) / dt
        w[0] = w[1]
        w = w + np.deg2rad(cfg.gyro_noise_deg_s) * np.abs(rng.standard_normal(T))
        speeds.append(w)
    return dict(meas=meas, drift=drift, gyro_speed=np.stack(speeds, 1))
