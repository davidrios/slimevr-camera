"""Stillness gate, per-window heading measurement, correction, evaluation."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.spatial.transform import Rotation as Rot

from .geometry import Camera, triangulate
from .heading import estimate_all
from .skeleton import UP, heading_of, heading_of_vec, wrap


@dataclass
class GateConfig:
    speed_thresh_deg_s: float = 8.0     # max tracker angular speed to count as still
    min_still_s: float = 2.0
    min_quality: float = 0.3            # observability threshold per tracker
    max_axis_spread: float = 0.15       # 1 - |mean unit axis| inside the window (stability; 0.02 rejected everything at >6 px noise)
    min_valid_frac: float = 0.7


@dataclass
class Window:
    start: int
    end: int


def still_windows(gyro_speed: np.ndarray, fps: float, cfg: GateConfig) -> list[Window]:
    still = gyro_speed.max(1) < np.deg2rad(cfg.speed_thresh_deg_s)
    out, i, T = [], 0, len(still)
    while i < T:
        if still[i]:
            j = i
            while j < T and still[j]:
                j += 1
            if (j - i) >= cfg.min_still_s * fps:
                out.append(Window(i, j))
            i = j
        else:
            i += 1
    return out


def triangulate_sequence(cams: list[Camera], uvs: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """uvs (C,T,K,2) -> (T,K,3) with NaN for untriangulated."""
    C, T, K, _ = uvs.shape
    X = np.full((T, K, 3), np.nan)
    for t in range(T):
        x, ok = triangulate(cams, uvs[:, t], valid[:, t])
        X[t] = x
    return X


@dataclass
class Measurement:
    window: Window
    heading_cam: dict[str, float] = field(default_factory=dict)   # rad
    heading_imu: dict[str, float] = field(default_factory=dict)
    quality: dict[str, float] = field(default_factory=dict)


def measure_windows(P: np.ndarray, meas: dict[str, Rot], windows: list[Window], cfg: GateConfig) -> list[Measurement]:
    est = estimate_all(P)
    out = []
    for w in windows:
        m = Measurement(w)
        for name, (ax, loc, q) in est.items():
            if name not in meas:
                continue
            f = ax[w.start:w.end]; qq = q[w.start:w.end]
            good = ~np.isnan(f).any(1) & (qq > cfg.min_quality)
            if good.mean() < cfg.min_valid_frac:
                continue
            fmean = f[good].mean(0)
            if np.linalg.norm(fmean) < 1 - cfg.max_axis_spread:   # axis wandered inside the window
                continue
            m.heading_cam[name] = float(heading_of_vec(fmean))
            # the same physical axis according to the (drifted) IMU
            ai = meas[name][w.start:w.end].apply(np.tile(loc, (w.end - w.start, 1)))
            m.heading_imu[name] = float(heading_of_vec(ai.mean(0)))
            m.quality[name] = float(qq[good].mean())
        out.append(m)
    return out


def apply_corrections(meas: dict[str, Rot], ms: list[Measurement], alpha: float = 1.0) -> tuple[dict[str, Rot], dict[str, np.ndarray]]:
    """Piecewise-constant per-tracker yaw correction updated at each window end.
    alpha=1: replace with the latest measurement; <1: exponential blend."""
    corrected, corr = {}, {}
    for name, R in meas.items():
        T = len(R)
        c = np.zeros(T)
        cur = 0.0
        for m in ms:
            if name in m.heading_cam:
                d = wrap(m.heading_cam[name] - m.heading_imu[name])
                cur = wrap(cur + alpha * wrap(d - cur)) if alpha < 1 else d
                c[m.window.end:] = cur
        corr[name] = c
        corrected[name] = Rot.from_rotvec(np.outer(c, UP)) * R
    return corrected, corr


def heading_errors(truth: dict[str, Rot], est: dict[str, Rot]) -> dict[str, np.ndarray]:
    return {n: np.rad2deg(wrap(heading_of(est[n]) - heading_of(truth[n]))) for n in est}


def summarize(err: dict[str, np.ndarray]) -> dict[str, dict[str, float]]:
    return {n: dict(rms=float(np.sqrt(np.mean(e ** 2))), p95=float(np.percentile(np.abs(e), 95)), max=float(np.abs(e).max())) for n, e in err.items()}
