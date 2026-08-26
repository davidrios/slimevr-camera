"""Per-tracker heading observations from 3D keypoints.

Key facts:
- A near-vertical bone's yaw is NOT observable from its own two endpoints (a
  standing shin projects to a point on the floor). Yaw must come from a
  lateral feature: hip width, shoulder width, heel->toe, or the knee / elbow
  flexion plane.
- Yaw drift is a rotation about world-up, which rotates the floor projection
  of *every* axis of the bone frame by the same angle. So we never need a
  "forward" convention: observe some axis of the bone frame with the camera,
  compute the same axis from the IMU orientation, and compare their floor
  headings. Each estimator therefore returns (axis_world (T,3), axis_local
  (3,), quality (T,)), quality in [0,1] = observability x horizontality.
"""
from __future__ import annotations

import numpy as np

from .skeleton import BONES, BONE_INDEX, KP_INDEX

KP = KP_INDEX
X = np.array([1.0, 0.0, 0.0])


def _unit(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n == 0, np.nan, n)


def _horiz(v):
    """fraction of a unit vector lying in the floor plane."""
    return np.sqrt(np.clip(v[..., 0] ** 2 + v[..., 2] ** 2, 0, 1))


def _lateral(P, left, right):
    ax = _unit(P[:, KP[right]] - P[:, KP[left]])
    return ax, X, _horiz(ax)


def _plane_normal(P, a, b, c, local_axis):
    """Flexion-plane normal of joints a-b-c = the middle bone's flexion axis.
    quality = sin(bend angle) x horizontality."""
    u = _unit(P[:, KP[b]] - P[:, KP[a]])
    v = _unit(P[:, KP[c]] - P[:, KP[b]])
    n = np.cross(u, v)
    s = np.linalg.norm(n, axis=-1)
    ax = n / np.where(s == 0, np.nan, s)[:, None]
    return ax, local_axis, s * _horiz(ax)


def _segment(P, a, b, bone):
    ax = _unit(P[:, KP[b]] - P[:, KP[a]])
    loc = np.asarray(BONES[BONE_INDEX[bone]].vec); loc = loc / np.linalg.norm(loc)
    return ax, loc, _horiz(ax)


def estimate_all(P: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """P: (T, K, 3) triangulated keypoints (NaN where missing)."""
    out = {}
    out["hip"] = _lateral(P, "hipL", "hipR")
    out["chest"] = _lateral(P, "shoulderL", "shoulderR")
    ah, _, qh = out["hip"]; ac, _, qc = out["chest"]
    out["waist"] = (_unit(ah + ac), X, np.minimum(qh, qc))       # no keypoints of its own
    for s in "LR":
        out[f"foot{s}"] = _segment(P, f"ankle{s}", f"toe{s}", f"foot{s}")
        # knee flexes about the thigh/shin local +X: thigh tilts forward, shin backward -> normal = +X
        out[f"thigh{s}"] = _plane_normal(P, f"hip{s}", f"knee{s}", f"ankle{s}", X)
        out[f"shin{s}"] = out[f"thigh{s}"]
        # elbow flexion (forearm forward) about local -X -> normal = -X
        out[f"upperArm{s}"] = _plane_normal(P, f"shoulder{s}", f"elbow{s}", f"wrist{s}", -X)
    return out
