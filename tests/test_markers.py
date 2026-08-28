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


def test_bar_direction_from_two_views():
    from slimevr_camera.markers import blob_shapes, bar_line_3d
    cams = default_rig(distance=4.0, f_px=1200.0)
    # a 4.5 cm bar at 1 m height, heading 80 deg (roughly broadside to both front cameras;
    # a bar aligned with a camera's line of sight foreshortens to a dot — expected, not a bug)
    d_true = np.array([np.sin(np.deg2rad(80)), 0.0, np.cos(np.deg2rad(80))]); c = np.array([0.1, 1.0, 0.0])
    P = np.stack([c + s * d_true for s in np.linspace(-0.0225, 0.0225, 40)])
    shapes = []
    for cam in cams:
        img = np.zeros((cam.height, cam.width), np.uint8)
        uv, _ = cam.project(P)
        for u, v in uv: cv2.circle(img, (int(round(u)), int(round(v))), 2, 255, -1)
        sh = blob_shapes(img); assert len(sh) == 1 and sh[0]["elong"] > 2.5, sh
        shapes.append(sh[0])
    X, d = bar_line_3d(cams, *shapes)
    assert np.linalg.norm(X - c) < 0.01
    heading_err = np.degrees(abs(np.arctan2(d[0], d[2]) - np.deg2rad(80))) % 180
    heading_err = min(heading_err, 180 - heading_err)
    assert heading_err < 5.0, heading_err   # ~3 deg here is the rasterisation limit of a 4.5 cm bar at 4 m in the synthetic render
