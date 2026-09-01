"""Monocular lifting glue (D36): COCO-17 2D keypoints <-> MotionBERT H36M-17.

The lifter itself (tools/motionbert/lift.py) runs in its own uv env and speaks
npz; this module prepares its input from cached rtmlib detections and converts
its output back into our KEYPOINTS layout in the world frame.

Conventions (verified in literature/2022-zhu-motionbert.md):
- lifter input  (T,17,3): H36M-17 order, [x, y, conf], pixels centred on the
  image and divided by min(w,h)/2 (the `--pixel` path of dataset_wild.py);
- lifter output (T,17,3): same x,y scale plus a relative depth z — a
  pixel-aligned camera frame (x right, y image-down, z away); directions map
  to world via Camera.R.T.
"""
from __future__ import annotations

import cv2
import numpy as np

from .geometry import Camera
from .skeleton import KEYPOINTS

# H36M-17 index -> constituent COCO-17 indices (averaged)
H36M_FROM_COCO = [
    [11, 12],       # 0  pelvis
    [12], [14], [16],   # 1-3  R hip/knee/ankle
    [11], [13], [15],   # 4-6  L hip/knee/ankle
    [5, 6, 11, 12], # 7  spine (pelvis+thorax midpoint)
    [5, 6],         # 8  thorax
    [0],            # 9  nose
    [3, 4],         # 10 head (ear midpoint)
    [5], [7], [9],  # 11-13 L shoulder/elbow/wrist
    [6], [8], [10], # 14-16 R shoulder/elbow/wrist
]

# our KEYPOINTS -> H36M-17 index (toes unavailable)
KP_FROM_H36M = {
    "head": 9, "shoulderL": 11, "shoulderR": 14, "elbowL": 12, "elbowR": 15,
    "wristL": 13, "wristR": 16, "hipL": 4, "hipR": 1, "kneeL": 5, "kneeR": 2,
    "ankleL": 6, "ankleR": 3,
}


def coco_to_h36m_input(kp: np.ndarray, score: np.ndarray, cam: Camera, min_score: float = 0.3) -> np.ndarray:
    """rtmlib COCO-body detections (T,K>=17,2)+(T,K) -> lifter input (T,17,3).

    Undistorts (k1,k2), then centres/scales per the MotionBERT wild convention.
    Missing constituents give conf 0 (the model consumes conf; coords fall back
    to the image centre rather than NaN, which would poison the network)."""
    T = len(kp)
    uv = kp[:, :17, :].astype(np.float64).copy()
    sc = score[:, :17].copy()
    ok = np.isfinite(uv).all(-1) & (sc > min_score)
    flat = uv.reshape(-1, 1, 2)
    good = np.isfinite(flat).all(-1).ravel()
    k = np.array([cam.dist[0], cam.dist[1], 0, 0], float)
    und = flat.copy()
    if good.any():
        und[good] = cv2.undistortPoints(flat[good].reshape(-1, 1, 2), cam.K, k, P=cam.K)
    uv = und.reshape(T, 17, 2)
    s = min(cam.width, cam.height) / 2.0
    uv = (uv - np.array([cam.width, cam.height]) / 2.0) / s
    out = np.zeros((T, 17, 3), np.float32)
    for j, srcs in enumerate(H36M_FROM_COCO):
        srcs = np.array(srcs)
        valid = ok[:, srcs].all(1)
        out[valid, j, :2] = uv[valid][:, srcs, :].mean(1)
        out[valid, j, 2] = sc[valid][:, srcs].min(1)
    return out


def lifted_to_keypoints(X: np.ndarray, inp: np.ndarray, cam: Camera, world_R: np.ndarray | None = None,
                        min_conf: float = 0.05) -> np.ndarray:
    """Lifter output (T,17,3) -> (T, len(KEYPOINTS), 3) world directions frame.

    Rotates the pixel-aligned camera-frame cloud to the world with cam.R.T
    (optionally then world_R, e.g. Z-up -> Y-up); joints whose lifter *input*
    conf was < min_conf become NaN; toes are always NaN. Scale is arbitrary
    (descriptor and headings are scale-invariant)."""
    Xw = X @ cam.R          # == (cam.R.T @ x)  per point
    if world_R is not None:
        Xw = Xw @ world_R.T
    out = np.full((len(X), len(KEYPOINTS), 3), np.nan)
    for i, name in enumerate(KEYPOINTS):
        j = KP_FROM_H36M.get(name)
        if j is None:
            continue
        v = Xw[:, j, :].copy()
        v[inp[:, j, 2] < min_conf] = np.nan
        out[:, i] = v
    return out
