"""MoVi (BMLmovi) loader — Ghorbani et al. 2021, doi:10.5683/SP2/JRHDRN.

Licence: non-commercial scientific research only; no redistribution.
Files live in data/movi/ (gitignored); see experiments/04-movi-detector-bias/download.py.

Ground truth: Visual3D segment frames (4x4 affine, 120 Hz, mm, Z-up) for 15
segments.  Videos: two hardware-synced FLIR "PG1"/"PG2" cameras, 800x600,
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

    def segment_frames(self, mocap_idx: int) -> dict[str, np.ndarray]:
        """tracker name -> 4x4 affine (mm) for our tracker set; skips gaps."""
        out = {}
        for i, code in enumerate(self.segment_names):
            name = SEGMENTS.get(code)
            A = self.affine[mocap_idx, i]
            if name and not np.any(A[:3, 3] <= MISSING / 10):
                out[name] = A
        return out


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
    )
