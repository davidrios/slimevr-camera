"""slimevr-camera: camera-assisted yaw-drift correction for SlimeVR IMU trackers."""


def enable_cuda():
    """On machines with pip-provided CUDA libs (vulcanus), onnxruntime must
    preload them before a CUDA session is created. Safe no-op elsewhere."""
    try:
        import onnxruntime as ort
        ort.preload_dlls()
    except Exception:
        pass
