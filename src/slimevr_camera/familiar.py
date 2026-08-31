"""Familiar-pose detection and in-pose measurement (D33).

A pose template is learned from camera keypoints during a trusted window
(after a manual full reset, or a labelled idle hold). Later frames match a
template when the heading-invariant pose descriptor is close and the body is
still; in a matched window the observable headings (pelvis, chest, feet +
knee planes when bent) are measured and can be applied like a full reset.

Descriptor: 3D joints, centred on the hip midpoint, rotated so the hip
lateral axis points +x (heading-invariant), scaled by the subject's hip
width; concatenated joint offsets of a fixed subset.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .heading import estimate_all
from .skeleton import KEYPOINTS, KP_INDEX, wrap

DESC_JOINTS = ["shoulderL", "shoulderR", "elbowL", "elbowR", "hipL", "hipR", "kneeL", "kneeR", "ankleL", "ankleR"]


def descriptor(P: np.ndarray) -> np.ndarray:
    """P (K,3) joints, Y-up, any units -> heading/position/scale-invariant descriptor, or None."""
    hl, hr = P[KP_INDEX["hipL"]], P[KP_INDEX["hipR"]]
    if np.isnan(hl).any() or np.isnan(hr).any(): return None
    c = (hl + hr) / 2; lat = hr - hl; lat[1] = 0
    n = np.linalg.norm(lat)
    if n < 1e-6: return None
    ca, sa = lat[0] / n, lat[2] / n
    R = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])          # rotates lat -> +x
    out = []
    for j in DESC_JOINTS:
        v = P[KP_INDEX[j]]
        if np.isnan(v).any(): return None
        out.append(R @ (v - c) / n)
    return np.concatenate(out)


@dataclass
class Template:
    name: str
    desc: np.ndarray            # (M, D) descriptors sampled over the trusted window
    def distance(self, d: np.ndarray) -> float:
        return float(np.min(np.linalg.norm(self.desc - d, axis=1)))


def learn_template(name: str, P_seq: np.ndarray, stride: int = 3) -> Template | None:
    ds = [descriptor(P) for P in P_seq[::stride]]
    ds = [d for d in ds if d is not None]
    return Template(name, np.stack(ds)) if ds else None


def match_frames(P_seq: np.ndarray, templates: list[Template], max_dist: float = 0.9):
    """-> (T,) template index or -1, and (T,) distance to the best template."""
    idx = np.full(len(P_seq), -1); dist = np.full(len(P_seq), np.inf)
    for t, P in enumerate(P_seq):
        d = descriptor(P)
        if d is None: continue
        for k, tpl in enumerate(templates):
            dd = tpl.distance(d)
            if dd < dist[t]: dist[t], idx[t] = dd, k
    idx[dist > max_dist] = -1
    return idx, dist


def in_pose_measurement(P_win: np.ndarray, min_quality: float = 0.3) -> dict[str, float]:
    """Measured headings (rad) over a matched window, per tracker, quality-gated."""
    est = estimate_all(P_win)
    out = {}
    for name, (ax, loc, q) in est.items():
        good = ~np.isnan(ax).any(1) & (q > min_quality)
        if good.mean() < 0.5: continue
        m = ax[good].mean(0)
        out[name] = float(np.arctan2(m[0], m[2]))
    return out
