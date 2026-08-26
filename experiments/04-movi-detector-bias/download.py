#!/usr/bin/env python3
"""Download a MoVi pilot subset from Borealis Dataverse (doi:10.5683/SP2/JRHDRN).

MoVi licence: non-commercial scientific research only; no redistribution;
no training of commercial algorithms. Data stays in data/movi/ (gitignored).

Usage: uv run python experiments/04-movi-detector-bias/download.py [--subjects 1 2 3 4 5] [--round F]
"""
from __future__ import annotations

import argparse, json, sys, urllib.request
from pathlib import Path

API = "https://borealisdata.ca/api/access/datafile/{id}"
HERE = Path(__file__).parent
DEST = HERE.parent.parent / "data" / "movi"


def inventory():
    d = json.load(open(HERE / "movi_dataverse.json"))
    return {f["dataFile"]["filename"]: (f["dataFile"]["id"], f["dataFile"]["filesize"]) for f in d["data"]["latestVersion"]["files"]}


def fetch(name, fid, size, dest: Path):
    out = dest / name
    if out.exists() and out.stat().st_size == size:
        print(f"  have {name}"); return
    print(f"  {name} ({size / 1e6:.0f} MB)")
    req = urllib.request.Request(API.format(id=fid), headers={"User-Agent": "slimevr-camera/0.1"})
    with urllib.request.urlopen(req) as r, open(out, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    ap.add_argument("--round", default="F", choices=["F", "S1", "S2"])
    ap.add_argument("--gt-only", action="store_true")
    a = ap.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    inv = inventory()
    want = ["README.pdf", "Camera Parameters.tar"]
    gt = {"F": ["F_Subjects_1_45.tar", "F_Subjects_46_90.tar"], "S1": ["S_V3D.tar"], "S2": ["S_V3D.tar"]}[a.round]
    want += [g for g in gt if any((int(x) <= 45) == ("1_45" in g) for x in a.subjects)] if a.round == "F" else gt
    if not a.gt_only:
        for s in a.subjects:
            for cam in ("PG1", "PG2"):
                want.append(f"{a.round}_{cam}_Subject_{s}_L.avi")
    missing = [w for w in want if w not in inv]
    if missing:
        print("not in inventory:", missing); sys.exit(1)
    print(f"downloading {len(want)} files, {sum(inv[w][1] for w in want) / 1e9:.2f} GB -> {DEST}")
    for w in want:
        fetch(w, *inv[w], DEST)
