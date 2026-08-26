import numpy as np
from scipy.spatial.transform import Rotation as Rot

from slimevr_camera.geometry import Camera, triangulate
from slimevr_camera.heading import estimate_all
from slimevr_camera.skeleton import BONES, TRACKER_BONES, forward_kinematics, heading_of, keypoint_array, wrap
from slimevr_camera.synth.camera import default_rig
from slimevr_camera.synth.motion import MotionConfig, generate


def test_triangulate_exact():
    cams = default_rig()
    X = np.random.default_rng(0).uniform([-1, 0, -1], [1, 2, 1], (20, 3))
    uvs = np.stack([c.project(X)[0] for c in cams])
    Xh, ok = triangulate(cams, uvs, np.ones((2, 20), bool))
    assert ok.all() and np.allclose(Xh, X, atol=1e-6)


def test_heading_estimators_match_truth_when_observable():
    m = generate(MotionConfig(duration_s=20, fps=30, tremor_deg=0.0, seed=3))
    world, joints = forward_kinematics(m["local"], m["root_pos"])
    P = keypoint_array(joints)
    est = estimate_all(P)
    for name in TRACKER_BONES:
        ax, loc, q = est[name]
        truth_ax = world[name].apply(np.tile(loc, (len(ax), 1)))
        got = np.arctan2(ax[:, 0], ax[:, 2]); truth = np.arctan2(truth_ax[:, 0], truth_ax[:, 2])
        good = q > 0.5
        assert good.mean() > 0.2, name
        err = np.rad2deg(np.abs(wrap(got[good] - truth[good])))
        tol = 3.0 if name == "waist" else 0.5   # waist is a blend, not a real axis
        assert np.median(err) < tol, (name, np.median(err))
