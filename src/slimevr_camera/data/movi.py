"""MoVi (BMLmovi) loader — Ghorbani et al. 2021, doi:10.5683/SP2/JRHDRN.

Licence: non-commercial scientific research only; no redistribution.
Files live in data/movi/ (gitignored); see experiments/04-movi-detector-bias/download.py.

Ground truth: Visual3D segment frames (4x4 affine, 120 Hz, mm, Z-up) for 15
segments.  NOTE: `jointsAffine_v3d` is PARENT-RELATIVE (root = pelvis is
world) and stored in ROW-VECTOR convention (rotation blocks are transposed
relative to the usual column convention).  Verified 2026-08-26 against marker
joint centres (1–5 mm at still frames): R_w(child) = R_l @ R_w(parent);
t_w(child) = t_w(parent) + R_w(parent)^T @ t_l.  `world_affine()` returns COLUMN-convention world frames
(R = R_w^T), i.e. `A[:3,:3] @ v_local + A[:3,3]` maps segment -> world.  Virtual markers LHJC/RHJC are
unfilled (zeros); hip joint centres are LHIP/RHIP.  Videos: two hardware-synced FLIR "PG1"/"PG2" cameras, 800x600,
30 Hz, one continuous file per round; `flags30` gives the video frame range
of each motion and `flags120` the matching mocap range.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy.io as sio

from ..geometry import Camera

ROOT = Path(__file__).resolve().parents[3] / "data" / "movi"
EXTRACTED = ROOT / "extracted"

# Visual3D segment codes -> our tracker names (None = no SlimeVR tracker there)
SEGMENTS = {
    "RPV": "hip", "RTA": "chest", "RHE": "head",
    "LTH": "thighL", "RTH": "thighR", "LSK": "shinL", "RSK": "shinR", "LFT": "footL", "RFT": "footR",
    "LAR": "upperArmL", "RAR": "upperArmR", "LFA": "forearmL", "RFA": "forearmR", "LHA": None, "RHA": None,
}
MISSING = -9.99999e8


def load_camera(cam: str) -> Camera:
    """cam in {"PG1","PG2"}. MoVi stores the MATLAB-convention (transposed)
    intrinsic matrix and R,t with x_cam = R^T (x_world - ...)? — verified
    empirically by reprojecting markers (see tests); here we return a Camera
    whose P projects world mm -> pixels."""
    c = np.load(EXTRACTED / "Calib" / f"cameraParams_{cam}.npz", allow_pickle=True)
    e = np.load(EXTRACTED / "Calib" / f"Extrinsics_{cam}.npz", allow_pickle=True)
    K = np.asarray(c["IntrinsicMatrix"], float).T          # MATLAB stores K^T
    R = np.asarray(e["rotationMatrix"], float)
    t = np.asarray(e["translationVector"], float)
    # MATLAB cameraParameters convention: [x y z]_cam = [X Y Z]_world * R + t  (row vectors)
    # => column form: x_cam = R^T X + t
    cam_obj = Camera(K=K, R=R.T, t=t, width=800, height=600)
    cam_obj.dist = np.asarray(c["RadialDistortion"], float)   # k1, k2 (MATLAB convention)
    return cam_obj


@dataclass
class MoviSubject:
    subject: int
    round: str                       # "F", "S1", "S2"
    segment_names: list[str]
    affine: np.ndarray               # (T120, 15, 4, 4) mm, Z-up; MISSING where gaps
    marker_names: list[str]
    markers: np.ndarray              # (T120, 87, 3)
    motions: list[str]
    flags30: np.ndarray              # (n_motions, 2) inclusive video frame ranges
    flags120: np.ndarray             # (n_motions, 2) inclusive mocap frame ranges
    meta: dict
    parent: np.ndarray = None    # (15,) 1-based parent segment index, 0 = root

    def video_path(self, cam: str) -> Path:
        return ROOT / f"{self.round}_{cam}_Subject_{self.subject}_L.avi"

    def mocap_index_for_video_frame(self, frame: int) -> int | None:
        """Map a 30 fps video frame to the nearest 120 Hz mocap sample using
        the per-motion flag pairs (linear inside each motion)."""
        for (a30, b30), (a120, b120) in zip(self.flags30, self.flags120):
            if a30 <= frame <= b30:
                u = (frame - a30) / max(b30 - a30, 1)
                return int(round(a120 + u * (b120 - a120)))
        return None

    def world_affine(self, mocap_idx: int) -> dict[str, np.ndarray]:
        """tracker name -> 4x4 WORLD affine (mm, Z-up) via forward kinematics
        over `segmentParent` (1-based; 0 = root). Segments with gaps are skipped."""
        W = [None] * len(self.segment_names)
        for i in range(len(self.segment_names)):
            self._fk(i, mocap_idx, W)
        return {SEGMENTS[c]: self._to_affine(W[i]) for i, c in enumerate(self.segment_names) if SEGMENTS.get(c) and W[i] is not None}

    def _fk(self, i, mocap_idx, W):
        """W[i] = (R_row (3x3, row convention), t_world (3,)) or None."""
        if W[i] is not None:
            return W[i]
        A = self.affine[mocap_idx, i]
        if np.any(A[:3, 3] <= MISSING / 10):
            return None
        p = int(self.parent[i]) - 1
        if p < 0:
            W[i] = (A[:3, :3], A[:3, 3])
        else:
            Wp = self._fk(p, mocap_idx, W)
            if Wp is None:
                return None
            Rw = A[:3, :3] @ Wp[0]
            W[i] = (Rw, Wp[1] + Wp[0].T @ A[:3, 3])
        return W[i]

    @staticmethod
    def _to_affine(Rt):
        M = np.eye(4); M[:3, :3] = Rt[0].T; M[:3, 3] = Rt[1]; return M

    def segment_frames(self, mocap_idx: int) -> dict[str, np.ndarray]:
        return self.world_affine(mocap_idx)


def load_subject(subject: int, round: str = "F") -> MoviSubject:
    tar_dir = "F_Subjects_1_45" if subject <= 45 else "F_Subjects_46_90"
    path = EXTRACTED / tar_dir / f"{round}_v3d_Subject_{subject}.mat" if round == "F" else EXTRACTED / "S_V3D" / f"{round}_v3d_Subject_{subject}.mat"
    m = sio.loadmat(path, squeeze_me=True, struct_as_record=False)
    s = m[f"Subject_{subject}_{round}"]
    mv = s.move
    meta = {k: getattr(s.subject, k) for k in s.subject._fieldnames}
    return MoviSubject(
        subject=subject, round=round,
        segment_names=[str(x) for x in mv.segmentName],
        affine=np.asarray(mv.jointsAffine_v3d, float),
        marker_names=[str(x) for x in mv.markerName],
        markers=np.asarray(mv.markerLocation, float),
        motions=[str(x) for x in mv.motions_list],
        flags30=np.asarray(mv.flags30, int), flags120=np.asarray(mv.flags120, int), meta=meta,
        parent=np.asarray(mv.segmentParent, int),
    )
