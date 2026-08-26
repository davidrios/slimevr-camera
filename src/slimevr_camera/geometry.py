"""Projective geometry: pinhole cameras and multi-view triangulation."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Camera:
    K: np.ndarray            # 3x3 intrinsics
    R: np.ndarray            # 3x3 world->camera rotation
    t: np.ndarray            # 3,   world->camera translation (x_c = R x_w + t)
    width: int = 1920
    height: int = 1080

    @property
    def P(self) -> np.ndarray:
        return self.K @ np.hstack([self.R, self.t[:, None]])

    @staticmethod
    def look_at(pos, target, f_px=1000.0, width=1920, height=1080, up=(0, 1, 0)) -> "Camera":
        pos, target, up = map(lambda v: np.asarray(v, float), (pos, target, up))
        z = target - pos; z /= np.linalg.norm(z)          # camera looks down +z
        x = np.cross(z, up); x /= np.linalg.norm(x)
        y = np.cross(z, x)                                # y down (image convention)
        R = np.stack([x, y, z])                           # rows = camera axes in world
        K = np.array([[f_px, 0, width / 2], [0, f_px, height / 2], [0, 0, 1.0]])
        return Camera(K, R, -R @ pos, width, height)

    def project(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """X (...,3) world -> pixels (...,2), depth (...)."""
        Xc = X @ self.R.T + self.t
        z = Xc[..., 2]
        uv = (Xc @ self.K.T)[..., :2] / z[..., None]
        return uv, z

    def in_frame(self, uv, z) -> np.ndarray:
        return (z > 0) & (uv[..., 0] >= 0) & (uv[..., 0] < self.width) & (uv[..., 1] >= 0) & (uv[..., 1] < self.height)


def triangulate(cams: list[Camera], uvs: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Linear (DLT) triangulation.
    uvs: (C, N, 2) pixel observations, valid: (C, N) bool.
    Returns X (N,3) and ok (N,) — ok is False where < 2 valid views."""
    C, N, _ = uvs.shape
    X = np.full((N, 3), np.nan)
    ok = valid.sum(0) >= 2
    Ps = [c.P for c in cams]
    for n in np.flatnonzero(ok):
        rows = []
        for c in range(C):
            if not valid[c, n]:
                continue
            u, v = uvs[c, n]
            P = Ps[c]
            rows.append(u * P[2] - P[0])
            rows.append(v * P[2] - P[1])
        A = np.stack(rows)
        _, _, Vt = np.linalg.svd(A)
        h = Vt[-1]
        X[n] = h[:3] / h[3]
    return X, ok
