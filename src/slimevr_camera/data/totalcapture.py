"""TotalCapture loader (Trumble et al., BMVC 2017; CVSSP, Univ. of Surrey).

Licence: research use only, no commercial use, no redistribution (D34:
validation only). Files under data/totalcapture/ (gitignored; credentials in
.access, never read into logs).

Layout (raw/ -> extracted/):
  calibration.cal                     8 cameras, "Surrey" format (see calibrationreadme)
  s{N}/s{N}_{seq}_Xsens.sensors       13 IMUs @ 60 Hz: name, quat (w x y z), accel (x y z)
  s{N}/{seq}_Xsens_AuxFields.sensors  same + gyro (x y z) + mag (x y z)
  s{N}/s{N}_{seq}_calib_imu_bone.txt  R_ib per sensor (quat x y z w)
  s{N}/s{N}_{seq}_calib_imu_ref.txt   R_ig per sensor (quat x y z w)
  S{N}/{seq}/gt_skel_gbl_ori.txt      Vicon: 21 joints, global orientation quats (order verified below)
  S{N}/{seq}/gt_skel_gbl_pos.txt      Vicon: 21 joints, global positions
  video/s{N}/s{N}_{seq}.tar.gz        8 cameras, 1080p60
Global bone orientation from IMU:  R_g_b = R_ig * R_i * R_ib^-1   (README).

Conventions VERIFIED 2026-08-28 on s1/walking1 (no video needed):
  - gt_skel_gbl_ori quaternions are x y z w (IMU-derived bone orientation
    agrees with Vicon to 2–8° median per bone; w-first gives ~130°).
  - gt_skel_gbl_pos is Y-up, in INCHES (head–foot joint distance ≈ 55 in).
    calibration.cal translations are in METRES -> convert positions * 0.0254
    before projecting. Reprojection check pending video.
  - 60 Hz throughout; IMU, Vicon and video frame counts match (3671).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation as Rot

from ..geometry import Camera

ROOT = Path(__file__).resolve().parents[3] / "data" / "totalcapture"
EX = ROOT / "extracted"

IMU_TO_BONE = {"Head": "Head", "Sternum": "Spine3", "Pelvis": "Hips", "L_UpArm": "LeftArm", "R_UpArm": "RightArm",
               "L_LowArm": "LeftForeArm", "R_LowArm": "RightForeArm", "L_UpLeg": "LeftUpLeg", "R_UpLeg": "RightUpLeg",
               "L_LowLeg": "LeftLeg", "R_LowLeg": "RightLeg", "L_Foot": "LeftFoot", "R_Foot": "RightFoot"}
# our tracker names
BONE_TO_TRACKER = {"Hips": "hip", "Spine3": "chest", "LeftUpLeg": "thighL", "RightUpLeg": "thighR", "LeftLeg": "shinL",
                   "RightLeg": "shinR", "LeftFoot": "footL", "RightFoot": "footR", "LeftArm": "upperArmL", "RightArm": "upperArmR",
                   "LeftForeArm": "forearmL", "RightForeArm": "forearmR", "Head": "head"}


def load_cameras(path: Path = EX / "calibration.cal") -> list[Camera]:
    tok = path.read_text().split()
    n, dist_order = int(tok[0]), int(tok[1]); i = 2; cams = []
    for _ in range(n):
        rmin, rmax, cmin, cmax = map(int, tok[i:i + 4]); i += 4
        fx, fy, cx, cy = map(float, tok[i:i + 4]); i += 4
        dist = [float(x) for x in tok[i:i + dist_order]]; i += dist_order
        R = np.array([float(x) for x in tok[i:i + 9]]).reshape(3, 3); i += 9
        t = np.array([float(x) for x in tok[i:i + 3]]); i += 3
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1.0]])
        c = Camera(K=K, R=R, t=t, width=cmax + 1, height=rmax + 1); c.dist = np.array(dist); cams.append(c)
    return cams


def _read_sensors(path: Path, aux: bool):
    """-> names (13,), quat wxyz (T,13,4), accel (T,13,3) [, gyro (T,13,3), mag (T,13,3)]"""
    lines = path.read_text().splitlines()
    n, T = map(int, lines[0].split()); names = None
    q = np.zeros((T, n, 4)); a = np.zeros((T, n, 3)); g = np.zeros((T, n, 3)); m = np.zeros((T, n, 3))
    li = 1
    for f in range(T):
        li += 1                                   # frame number line
        rows = [lines[li + k].split() for k in range(n)]; li += n
        if names is None: names = [r[0] for r in rows]
        v = np.array([[float(x) for x in r[1:]] for r in rows])
        q[f] = v[:, 0:4]; a[f] = v[:, 4:7]
        if aux: g[f] = v[:, 7:10]; m[f] = v[:, 10:13]
    return names, q, a, (g, m) if aux else None


def _read_calib(path: Path) -> dict[str, Rot]:
    lines = path.read_text().splitlines()[1:]
    out = {}
    for l in lines:
        p = l.split()
        if len(p) == 5: out[p[0]] = Rot.from_quat([float(x) for x in p[1:]])   # x y z w (scipy order)
    return out


def _read_gt(path: Path, ncol: int):
    lines = path.read_text().splitlines()
    joints = lines[0].split()
    data = np.array([[float(x) for x in l.split()] for l in lines[1:] if l.strip()])
    return joints, data.reshape(len(data), len(joints), ncol)


@dataclass
class TCSequence:
    subject: int; seq: str
    imu_names: list[str]; imu_quat: np.ndarray; imu_acc: np.ndarray       # quat (T,13,4) w x y z
    calib_bone: dict[str, Rot]; calib_ref: dict[str, Rot]
    joints: list[str]; gt_ori: np.ndarray; gt_pos: np.ndarray             # (T,21,4), (T,21,3)
    fps: float = 60.0

    def imu_bone_world(self, sensor: str) -> Rot:
        """Global bone orientation from the IMU per README: R_ig * R_i * R_ib^-1."""
        i = self.imu_names.index(sensor)
        Ri = Rot.from_quat(self.imu_quat[:, i][:, [1, 2, 3, 0]])       # wxyz -> xyzw
        return self.calib_ref[sensor] * Ri * self.calib_bone[sensor].inv()

    INCH = 0.0254

    def gt_pos_m(self) -> np.ndarray:
        return self.gt_pos * self.INCH

    def gt_bone_world(self, bone: str, order: str = "xyzw") -> Rot:
        j = self.joints.index(bone); q = self.gt_ori[:, j]
        return Rot.from_quat(q if order == "xyzw" else q[:, [1, 2, 3, 0]])


def load_sequence(subject: int, seq: str) -> TCSequence:
    s = f"s{subject}"; S = f"S{subject}"
    names, q, a, _ = _read_sensors(EX / s / f"{s}_{seq}_Xsens.sensors", aux=False)
    cb = _read_calib(EX / s / f"{s}_{seq}_calib_imu_bone.txt"); cr = _read_calib(EX / s / f"{s}_{seq}_calib_imu_ref.txt")
    joints, ori = _read_gt(EX / S / seq / "gt_skel_gbl_ori.txt", 4); _, pos = _read_gt(EX / S / seq / "gt_skel_gbl_pos.txt", 3)
    return TCSequence(subject, seq, names, q, a, cb, cr, joints, ori, pos)
