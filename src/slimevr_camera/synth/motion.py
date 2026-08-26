"""Procedural body motion with alternating active / still phases.

Not realistic motion — just enough variety (hip/knee/elbow flexion, torso
twist, root yaw wander) to exercise heading observability and motion-
dependent drift. Replace with AMASS / rendered data later (agenda §H).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation as Rot

from ..skeleton import BONES


@dataclass
class MotionConfig:
    duration_s: float = 600.0
    fps: float = 60.0
    active_s: tuple[float, float] = (15.0, 40.0)   # active phase length range
    still_s: tuple[float, float] = (3.0, 8.0)      # still phase length range
    tremor_deg: float = 0.3                        # joint jitter while "still"
    turns_per_min: float = 2.0                     # in-place turns (VR users turn around); each +-90..360 deg
    seed: int = 0


def activity_schedule(cfg: MotionConfig, rng) -> np.ndarray:
    """Per-frame activity level a(t) in {0,1} with smooth 0.5 s ramps."""
    T = int(cfg.duration_s * cfg.fps)
    a = np.zeros(T)
    t = 0
    active = True
    while t < T:
        lo, hi = cfg.active_s if active else cfg.still_s
        n = int(rng.uniform(lo, hi) * cfg.fps)
        a[t:t + n] = 1.0 if active else 0.0
        t += n
        active = not active
    ramp = int(0.5 * cfg.fps)
    k = np.ones(ramp) / ramp
    return np.convolve(a, k, mode="same")


def _osc(tau, rng, n=3, fmax=1.5):
    """Sum of n random sinusoids of a warped time, normalised to [-1,1]."""
    out = np.zeros_like(tau)
    for _ in range(n):
        f = rng.uniform(0.1, fmax)
        out += rng.uniform(0.3, 1.0) * np.sin(2 * np.pi * f * tau + rng.uniform(0, 2 * np.pi))
    return out / n


def generate(cfg: MotionConfig):
    """Returns dict(t, activity, local: name->Rotation(T), root_pos (T,3))."""
    rng = np.random.default_rng(cfg.seed)
    T = int(cfg.duration_s * cfg.fps)
    t = np.arange(T) / cfg.fps
    a = activity_schedule(cfg, rng)
    tau = np.cumsum(a) / cfg.fps          # warped time: advances only when active
    d2r = np.deg2rad
    def trem():   # slow wobble in real time (not warped): ~1 Hz, tremor_deg amplitude
        return d2r(cfg.tremor_deg) * np.stack([_osc(t, rng, n=2, fmax=1.5) for _ in range(3)], -1)

    def euler(x_deg, y_deg, z_deg):
        e = np.stack([d2r(x_deg), d2r(y_deg), d2r(z_deg)], -1) + trem()
        return Rot.from_euler("xyz", e)

    flex = lambda amp: amp * (1 + _osc(tau, rng)) / 2            # [0, amp]
    sym = lambda amp: amp * _osc(tau, rng)                        # [-amp, amp]
    zero = np.zeros(T)

    root_yaw = np.cumsum(sym(3.0) * a) / cfg.fps * 10             # slow wander (deg)
    # discrete in-place turns: smooth ramps of +-(90..360) deg, ~2 s each, only while active
    n_turns = int(cfg.turns_per_min * cfg.duration_s / 60)
    turn_rate = np.zeros(T)
    for _ in range(n_turns):
        t0 = int(rng.uniform(0, T - 2 * cfg.fps)); amp = rng.choice([-1, 1]) * rng.uniform(90, 360)
        n = int(2 * cfg.fps); win = np.hanning(n); turn_rate[t0:t0 + n] += amp * win / win.sum()
    root_yaw = root_yaw + np.cumsum(turn_rate * a)
    local = {}
    local["hip"] = Rot.from_euler("xyz", np.stack([d2r(sym(10)), d2r(root_yaw), d2r(sym(5))], -1))
    local["waist"] = euler(sym(8), sym(10), sym(4))
    local["chest"] = euler(sym(10), sym(20), sym(5))
    local["head"] = euler(sym(20), sym(40), sym(10))
    for side in "LR":
        s = 1 if side == "R" else -1
        # hip flexion lifts the knee forward: rotation about -X
        local[f"thigh{side}"] = euler(-flex(60), sym(15), s * sym(10))
        # knee flexion swings the shin backward: rotation about +X
        local[f"shin{side}"] = euler(flex(70), zero, zero)
        local[f"foot{side}"] = euler(sym(15), sym(10), zero)
        # shoulder: raise arm forward (about -X) and out; upper-arm twist about Y
        local[f"upperArm{side}"] = euler(-flex(70), sym(40), -s * flex(40))
        # elbow flexion brings the forearm forward: about -X
        local[f"forearm{side}"] = euler(-flex(90), zero, zero)

    root_pos = np.stack([np.cumsum(sym(0.3) * a) / cfg.fps, 0.95 + 0.02 * sym(1), np.cumsum(sym(0.3) * a) / cfg.fps], -1)
    return dict(t=t, activity=a, local=local, root_pos=root_pos, fps=cfg.fps)
