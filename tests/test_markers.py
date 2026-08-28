import numpy as np, cv2
from slimevr_camera.markers import detect_blobs, triangulate_blobs
from slimevr_camera.synth.camera import default_rig


def test_blob_triangulation_recovers_known_separation():
    cams = default_rig(distance=4.0, f_px=1200.0)
    # three patches on a "tracker" 5 cm apart, at 1 m height, slightly rotated
    P = np.array([[0.0, 1.0, 0.0], [0.05, 1.0, 0.01], [0.0, 1.05, 0.0]])
    rng = np.random.default_rng(1)
    blobs = []
    for cam in cams:
        img = (rng.normal(20, 5, (cam.height, cam.width))).clip(0, 255).astype(np.uint8)
        uv, z = cam.project(P)
        for u, v in uv:
            cv2.circle(img, (int(round(u)), int(round(v))), 3, 255, -1)          # saturated blob ~7 px
        # a distractor reflection that has no epipolar partner
        cv2.circle(img, (200, 300), 3, 255, -1)
        blobs.append(detect_blobs(img))
    assert all(len(b) == 4 for b in blobs)
    X, pairs = triangulate_blobs(cams, blobs[0], blobs[1])
    assert len(pairs) >= 3
    d = np.linalg.norm(X[:, None] - X[None], axis=-1)
    # the 5 cm separations must be recovered to a few mm
    seps = sorted(d[np.triu_indices(len(X), 1)])
    assert abs(seps[0] - 0.05) < 0.004 and abs(seps[1] - 0.05) < 0.004, seps
