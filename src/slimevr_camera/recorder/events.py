"""Mark session events (resets, pose labels) with wall-clock time.

Interactive: run in a terminal during the session; press a key + Enter.
  r  full reset (standing)      y  yaw reset       m  mounting reset
  s  entering seated idle       t  entering standing idle
  a  activity start             e  end of hold / activity
  n <text>  free note           q  quit
Writes events.csv (wall_s, code, label, note) in the run folder.
Usage: uv run python -m slimevr_camera.recorder.events RUN_DIR
"""
from __future__ import annotations

import csv, sys, time
from pathlib import Path

CODES = {"r": "full_reset", "y": "yaw_reset", "m": "mounting_reset", "s": "seated_idle", "t": "standing_idle", "a": "activity", "e": "end", "n": "note"}


def main():
    run = Path(sys.argv[1]); run.mkdir(parents=True, exist_ok=True)
    path = run / "events.csv"; new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["wall_s", "code", "label", "note"])
        print(__doc__, file=sys.stderr)
        while True:
            try: line = input("> ").strip()
            except EOFError: break
            if not line: continue
            if line == "q": break
            code, _, note = line.partition(" ")
            if code not in CODES: print("unknown code", file=sys.stderr); continue
            w.writerow([f"{time.time():.3f}", code, CODES[code], note]); f.flush()
            print(f"  {CODES[code]} @ {time.strftime('%H:%M:%S')} {note}", file=sys.stderr)


if __name__ == "__main__":
    main()
