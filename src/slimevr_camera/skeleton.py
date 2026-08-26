"""Kinematic skeleton matching a SlimeVR 11-tracker layout.

Conventions (world and rest frame): Y up, character faces +Z, subject's
right is +X. Every bone frame is identity at rest, so a bone's world
orientation R maps rest vectors into the world; its *forward* axis is
R @ (0,0,1) and its heading is atan2(forward.x, forward.z).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation as Rot

UP = np.array([0.0, 1.0, 0.0])
FORWARD = np.array([0.0, 0.0, 1.0])


@dataclass(frozen=True)
class Bone:
    name: str
    parent: str | None          # parent bone name (None for root)
    start: str                  # joint the bone starts at
    end: str                    # joint the bone ends at
    vec: tuple[float, float, float]  # rest-frame vector start->end (m)
    tracker: bool               # does a SlimeVR tracker sit on this bone?


# Joint offsets that are not bone ends (attached rigidly to a bone frame).
# joint -> (bone, rest offset from bone start)
ATTACHED = {
    "hipL": ("hip", (-0.09, 0.0, 0.0)),
    "hipR": ("hip", (0.09, 0.0, 0.0)),
    "shoulderL": ("chest", (-0.18, 0.22, 0.0)),
    "shoulderR": ("chest", (0.18, 0.22, 0.0)),
}

BONES: list[Bone] = [
    Bone("hip", None, "pelvis", "waist", (0.0, 0.10, 0.0), True),
    Bone("waist", "hip", "waist", "chestBase", (0.0, 0.15, 0.0), True),
    Bone("chest", "waist", "chestBase", "neck", (0.0, 0.25, 0.0), True),
    Bone("head", "chest", "neck", "head", (0.0, 0.18, 0.0), False),
    Bone("thighL", "hip", "hipL", "kneeL", (0.0, -0.45, 0.0), True),
    Bone("shinL", "thighL", "kneeL", "ankleL", (0.0, -0.43, 0.0), True),
    Bone("footL", "shinL", "ankleL", "toeL", (0.0, -0.06, 0.18), True),
    Bone("thighR", "hip", "hipR", "kneeR", (0.0, -0.45, 0.0), True),
    Bone("shinR", "thighR", "kneeR", "ankleR", (0.0, -0.43, 0.0), True),
    Bone("footR", "shinR", "ankleR", "toeR", (0.0, -0.06, 0.18), True),
    Bone("upperArmL", "chest", "shoulderL", "elbowL", (0.0, -0.28, 0.0), True),
    Bone("forearmL", "upperArmL", "elbowL", "wristL", (0.0, -0.26, 0.0), False),
    Bone("upperArmR", "chest", "shoulderR", "elbowR", (0.0, -0.28, 0.0), True),
    Bone("forearmR", "upperArmR", "elbowR", "wristR", (0.0, -0.26, 0.0), False),
]
BONE_INDEX = {b.name: i for i, b in enumerate(BONES)}
TRACKER_BONES = [b.name for b in BONES if b.tracker]

# Keypoints a 2D pose model would give us (COCO body + toes).
KEYPOINTS = [
    "head", "shoulderL", "shoulderR", "elbowL", "elbowR", "wristL", "wristR",
    "hipL", "hipR", "kneeL", "kneeR", "ankleL", "ankleR", "toeL", "toeR",
]
KP_INDEX = {k: i for i, k in enumerate(KEYPOINTS)}


def forward_kinematics(local: dict[str, Rot], root_pos: np.ndarray):
    """local: bone name -> Rotation (T,) relative to parent. Returns
    (world: name -> Rotation (T,), joints: name -> (T,3))."""
    T = len(root_pos)
    world: dict[str, Rot] = {}
    joints: dict[str, np.ndarray] = {"pelvis": np.asarray(root_pos, float)}
    for b in BONES:
        R = local[b.name] if b.parent is None else world[b.parent] * local[b.name]
        world[b.name] = R
        if b.start not in joints:  # attached joint (hipL, shoulderR, ...)
            pb, off = ATTACHED[b.start]
            joints[b.start] = joints[BONES[BONE_INDEX[pb]].start] + world[pb].apply(np.tile(off, (T, 1)))
        joints[b.end] = joints[b.start] + R.apply(np.tile(b.vec, (T, 1)))
    for j, (pb, off) in ATTACHED.items():
        if j not in joints:
            joints[j] = joints[BONES[BONE_INDEX[pb]].start] + world[pb].apply(np.tile(off, (T, 1)))
    return world, joints


def keypoint_array(joints: dict[str, np.ndarray]) -> np.ndarray:
    """(T, K, 3) in KEYPOINTS order."""
    return np.stack([joints[k] for k in KEYPOINTS], axis=1)


def heading_of(R: Rot) -> np.ndarray:
    """Heading angle (rad) of a bone frame's forward axis, projected on floor."""
    f = R.apply(np.tile(FORWARD, (len(R), 1)))
    return np.arctan2(f[:, 0], f[:, 2])


def heading_of_vec(v: np.ndarray) -> np.ndarray:
    return np.arctan2(v[..., 0], v[..., 2])


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi
