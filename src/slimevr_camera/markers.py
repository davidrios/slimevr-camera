"""Retroreflective-marker blobs: detection in IR/night-mode frames and
2-view triangulation (for the tape-on-tracker idea, notes/retroreflective-tape-idea.md).

detect_blobs(gray) -> (N,2) sub-pixel centroids + radius + peak, using a
saturation threshold, connected components, and intensity-weighted centroids.
Association across views is by epipolar distance; identification to trackers
is left to the caller (skeleton prediction / pattern geometry).
"""
from __future__ import annotations

import numpy as np
import cv2

from .geometry import Camera, triangulate


def detect_blobs(gray: np.ndarray, thresh: int = 200, min_area: int = 3, max_area: int = 2000):
    """Return array (N, 4): x, y (intensity-weighted sub-pixel centroid), equivalent radius, peak value."""
    _, bw = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    out = []
    g = gray.astype(np.float64)
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_area or area > max_area: continue
        x0, y0, w, h = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        sub = g[y0:y0 + h, x0:x0 + w]; m = (labels[y0:y0 + h, x0:x0 + w] == i)
        wts = np.where(m, sub, 0.0); tot = wts.sum()
        ys, xs = np.mgrid[y0:y0 + h, x0:x0 + w]
        out.append([(wts * xs).sum() / tot, (wts * ys).sum() / tot, np.sqrt(area / np.pi), sub[m].max()])
    return np.array(out).reshape(-1, 4)


def epipolar_pairs(cams: list[Camera], b1: np.ndarray, b2: np.ndarray, max_px: float = 3.0):
    """Match blobs between two views by symmetric epipolar distance. Returns list of (i, j, dist)."""
    P1, P2 = cams[0].P, cams[1].P
    # fundamental matrix from projection matrices
    C1 = -cams[0].R.T @ cams[0].t; e2 = P2 @ np.append(C1, 1.0)
    ex = np.array([[0, -e2[2], e2[1]], [e2[2], 0, -e2[0]], [-e2[1], e2[0], 0]])
    F = ex @ P2 @ np.linalg.pinv(P1)
    pairs = []
    for i, (x1, y1, *_) in enumerate(b1):
        p1 = np.array([x1, y1, 1.0]); l2 = F @ p1
        for j, (x2, y2, *_) in enumerate(b2):
            p2 = np.array([x2, y2, 1.0]); l1 = F.T @ p2
            d = 0.5 * (abs(p2 @ l2) / np.hypot(l2[0], l2[1]) + abs(p1 @ l1) / np.hypot(l1[0], l1[1]))
            if d < max_px: pairs.append((i, j, float(d)))
    pairs.sort(key=lambda t: t[2])
    used1, used2, out = set(), set(), []
    for i, j, d in pairs:
        if i in used1 or j in used2: continue
        used1.add(i); used2.add(j); out.append((i, j, d))
    return out


def triangulate_blobs(cams: list[Camera], b1: np.ndarray, b2: np.ndarray, max_px: float = 3.0):
    """-> (M,3) world points and the (i,j) pairs used."""
    pairs = epipolar_pairs(cams, b1, b2, max_px)
    if not pairs: return np.zeros((0, 3)), []
    uv = np.stack([np.array([b1[i, :2] for i, _, _ in pairs]), np.array([b2[j, :2] for _, j, _ in pairs])])
    X, ok = triangulate(cams, uv, np.ones((2, len(pairs)), bool))
    return X, pairs


# ---------------------------------------------------------------- v2 markers: bars and rings

def blob_shapes(gray: np.ndarray, thresh: int = 200, min_area: int = 6, max_area: int = 5000):
    """Connected saturated regions with second-moment shape: returns list of dicts
    {cx, cy, area, len_px (major axis length), width_px, angle (rad, image x-axis), elong}.
    Bars (elong >> 1) carry an in-image direction; dots (elong ~ 1) don't."""
    _, bw = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    out = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_area or area > max_area: continue
        ys, xs = np.nonzero(labels == i)
        cx, cy = xs.mean(), ys.mean(); C = np.cov(np.stack([xs - cx, ys - cy]))
        w, V = np.linalg.eigh(C); w = np.clip(w, 1e-6, None)
        major = V[:, 1]; L, W = 4 * np.sqrt(w[1]), 4 * np.sqrt(w[0])         # ~full lengths for a uniform bar
        out.append(dict(cx=float(cx), cy=float(cy), area=int(area), len_px=float(L), width_px=float(W),
                        angle=float(np.arctan2(major[1], major[0])), elong=float(L / W)))
    return out


def bar_line_3d(cams: list[Camera], b1: dict, b2: dict):
    """A bar seen in two views -> (3D centre, unit direction up to sign).
    Triangulates the two bar endpoints (centre +- half-length along the image
    axis); endpoint correspondence is fixed by orienting both image axes to
    +x first. The sign of the direction is resolved by the marker dot."""
    def ends(b):
        a = b["angle"]; ca, sa = np.cos(a), np.sin(a)
        if ca < 0: ca, sa = -ca, -sa                                  # consistent orientation across views
        h = b["len_px"] / 2
        return np.array([[b["cx"] - h * ca, b["cy"] - h * sa], [b["cx"] + h * ca, b["cy"] + h * sa]])
    E, ok = triangulate(cams, np.stack([ends(b1), ends(b2)]), np.ones((2, 2), bool))
    d = E[1] - E[0]; d /= np.linalg.norm(d)
    return E.mean(0), d


def ring_axis(gray: np.ndarray, thresh: int = 200, min_area: int = 20):
    """Reflective band around a limb -> fit an ellipse to each saturated region;
    returns list of (cx, cy, major_px, minor_px, angle_rad). The ellipse's MINOR axis
    in the image is the limb direction projected (a ring seen obliquely is
    squashed along the limb axis)."""
    _, bw = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    cnts, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cnts:
        if cv2.contourArea(c) < min_area or len(c) < 5: continue
        (cx, cy), (a, b), ang = cv2.fitEllipse(c)
        out.append((float(cx), float(cy), float(max(a, b)), float(min(a, b)), float(np.deg2rad(ang))))
    return out
