"""Stillness gate, per-window heading measurement, correction, evaluation."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.spatial.transform import Rotation as Rot

from .geometry import Camera, triangulate
from .heading import estimate_all
from .skeleton import UP, heading_of, heading_of_vec, wrap, yaw_rate  # noqa: F401


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


@dataclass
class ScaleLearner:
    """Recursive least squares for a per-tracker yaw scale error k:
    the change in required correction between two windows should equal
    -k x (signed yaw rotation travelled between them)."""
    prior_var: float = (0.02) ** 2      # k ~ +-2 % a priori (drift-lab: 0.2-0.4 %)
    meas_var_deg: float = 1.0            # camera heading noise per window (deg)
    min_travel_deg: float = 45.0         # ignore windows with too little net rotation in between
    k: float = 0.0
    var: float = None

    def __post_init__(self):
        self.var = self.prior_var

    def update(self, delta_corr: float, travel: float):
        if abs(travel) < np.deg2rad(self.min_travel_deg):
            return
        # model: delta_corr = -k * travel + noise
        h = -travel
        r = np.deg2rad(self.meas_var_deg) ** 2
        g = self.var * h / (h * self.var * h + r)
        self.k += g * (delta_corr - h * self.k)
        self.var *= (1 - g * h)


def apply_corrections(meas: dict[str, Rot], ms: list[Measurement], fps: float = 30.0,
                      learn_scale: bool = False) -> tuple[dict[str, Rot], dict[str, np.ndarray], dict[str, float]]:
    """Per-tracker yaw correction updated at each window end.
    Without scale learning: piecewise constant.  With it: between windows the
    correction is extrapolated as c + k_hat * (signed yaw rotation travelled
    since the window), and k_hat is refined from each new window."""
    corrected, corr, khat = {}, {}, {}
    for name, R in meas.items():
        T = len(R)
        travel = np.cumsum(yaw_rate(R, fps)) / fps      # signed yaw rotation travelled (rad)
        c = np.zeros(T)
        cur, t_last, learner = 0.0, None, ScaleLearner()
        for m in ms:
            if name not in m.heading_cam:
                continue
            d = wrap(m.heading_cam[name] - m.heading_imu[name])   # total correction needed now
            if learn_scale:
                t_end = min(m.window.end, T - 1)
                if t_last is not None:
                    learner.update(wrap(d - cur), travel[t_end] - travel[t_last])
                cur, t_last = d, t_end
                c[t_last:] = cur - learner.k * (travel[t_last:] - travel[t_last])
            else:
                cur = d
                c[m.window.end:] = cur
        corr[name] = c
        khat[name] = learner.k
        corrected[name] = Rot.from_rotvec(np.outer(c, UP)) * R
    return corrected, corr, khat


def heading_errors(truth: dict[str, Rot], est: dict[str, Rot]) -> dict[str, np.ndarray]:
    return {n: np.rad2deg(wrap(heading_of(est[n]) - heading_of(truth[n]))) for n in est}


def summarize(err: dict[str, np.ndarray]) -> dict[str, dict[str, float]]:
    return {n: dict(rms=float(np.sqrt(np.mean(e ** 2))), p95=float(np.percentile(np.abs(e), 95)), max=float(np.abs(e).max())) for n, e in err.items()}
