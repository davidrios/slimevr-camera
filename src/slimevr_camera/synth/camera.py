"""Synthetic 2D keypoint observations from pinhole cameras."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..geometry import Camera


@dataclass
class ObsConfig:
    pixel_noise: float = 3.0       # sigma, px
    dropout: float = 0.02          # random per-keypoint miss probability
    seed: int = 2


def observe(cams: list[Camera], kp3d: np.ndarray, cfg: ObsConfig):
    """kp3d (T,K,3) -> uvs (C,T,K,2), valid (C,T,K)."""
    rng = np.random.default_rng(cfg.seed)
    uvs, valid = [], []
    for c in cams:
        uv, z = c.project(kp3d)
        ok = c.in_frame(uv, z) & (rng.uniform(size=z.shape) > cfg.dropout)
        uv = uv + cfg.pixel_noise * rng.standard_normal(uv.shape)
        uvs.append(uv); valid.append(ok)
    return np.stack(uvs), np.stack(valid)


def default_rig(distance=3.5, height=1.4, spread_deg=60.0, f_px=1000.0, width=1920, height_px=1080):
    """Two cameras in front-left and front-right of the play space, looking at
    a point ~1 m above the origin."""
    a = np.deg2rad(spread_deg / 2)
    target = (0, 1.0, 0)
    return [
        Camera.look_at((-distance * np.sin(a), height, distance * np.cos(a)), target, f_px, width, height_px),
        Camera.look_at((distance * np.sin(a), height, distance * np.cos(a)), target, f_px, width, height_px),
    ]
