"""Run-folder conventions for own-room sessions (docs/06-recorder-beacon.md).

data/runs/<stamp>_<label>/
  cam1.mkv cam2.mkv (+ .start.json)   capture.py
  beacon.csv                           beacon.py
  cam1.times.csv cam2.times.csv        decode.py  (frame -> wall_s)
  driftlog.csv (+ .meta.json)          server DriftLogger (copy in)
  *.bvh                                server BVH recorder (optional)
  events.csv                           events.py
  meta.json                            trackers, cameras, placement, notes
`load_run()` returns aligned handles; everything is on the wall clock.
"""
from __future__ import annotations

import csv, json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

RUNS = Path(__file__).resolve().parents[3] / "data" / "runs"


@dataclass
class Run:
    path: Path
    meta: dict
    events: pd.DataFrame
    frame_times: dict[str, np.ndarray]          # cam -> wall_s per frame
    driftlog: pd.DataFrame | None = None        # raw tracker quaternions (+ HMD positions)

    def video(self, cam: str) -> Path: return self.path / f"{cam}.mkv"

    def frame_at(self, cam: str, wall_s: float) -> int:
        t = self.frame_times[cam]; return int(np.clip(np.searchsorted(t, wall_s), 0, len(t) - 1))

    def trusted_windows(self, seconds_after_reset: float = 120.0) -> list[tuple[float, float]]:
        """Wall-time intervals after each full reset during which the IMU body model is trusted."""
        r = self.events[self.events.code == "r"].wall_s.to_numpy(float)
        return [(t, t + seconds_after_reset) for t in r]

    def holds(self) -> list[tuple[str, float, float]]:
        """(label, start, end) for seated_idle / standing_idle holds closed by an 'e' event."""
        ev = self.events.sort_values("wall_s"); out = []; open_ = None
        for _, e in ev.iterrows():
            if e.code in ("s", "t"): open_ = (e.label, float(e.wall_s))
            elif e.code == "e" and open_: out.append((open_[0], open_[1], float(e.wall_s))); open_ = None
        return out


def load_run(name: str) -> Run:
    p = RUNS / name
    meta = json.loads((p / "meta.json").read_text()) if (p / "meta.json").exists() else {}
    events = pd.read_csv(p / "events.csv") if (p / "events.csv").exists() else pd.DataFrame(columns=["wall_s", "code", "label", "note"])
    ft = {}
    for f in p.glob("*.times.csv"):
        ft[f.name.split(".")[0]] = pd.read_csv(f).wall_s.to_numpy(float)
    dl = pd.read_csv(p / "driftlog.csv") if (p / "driftlog.csv").exists() else None
    if dl is not None: dl["wall_s"] = dl.wall_ms / 1000.0
    return Run(p, meta, events, ft, dl)
