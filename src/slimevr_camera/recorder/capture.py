"""Record N RTSP streams without re-encoding, with a wall-clock start marker.

Each camera -> <out>/<name>.mkv (ffmpeg -c copy) + <name>.start.json.
ffmpeg's -use_wallclock_as_timestamps gives packet-arrival PTS as a fallback;
the beacon decoder provides the authoritative per-frame time.
"""
from __future__ import annotations

import json, signal, subprocess, sys, time
from pathlib import Path


def start(name: str, url: str, out: Path) -> subprocess.Popen:
    out.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-rtsp_transport", "tcp", "-use_wallclock_as_timestamps", "1",
           "-i", url, "-c", "copy", "-f", "matroska", "-y", str(out / f"{name}.mkv")]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    (out / f"{name}.start.json").write_text(json.dumps(dict(name=name, url=url, wall_s=time.time(), mono_s=time.monotonic(), cmd=cmd)))
    return p


def main():
    import argparse
    ap = argparse.ArgumentParser(description="e.g. --cam cam1=rtsp://user:pw@192.168.1.10:554/stream --cam cam2=rtsp://...")
    ap.add_argument("--cam", action="append", required=True, help="name=rtsp_url")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    procs = [start(*c.split("=", 1), a.out) for c in a.cam]
    print(f"recording {len(procs)} streams to {a.out}; Ctrl-C to stop", file=sys.stderr)
    try:
        while all(p.poll() is None for p in procs):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    for p in procs:
        try: p.stdin.write(b"q"); p.stdin.flush()
        except Exception: p.send_signal(signal.SIGINT)
    for p in procs: p.wait(timeout=10)


if __name__ == "__main__":
    main()
