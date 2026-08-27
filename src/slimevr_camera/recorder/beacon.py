"""Host-side beacon driver and the shared symbol code.

Code: symbol period SYM_S (200 ms). Each word = SYNC (1,1,1,0) + 16-bit
counter, Manchester-encoded (bit 1 -> [1,0], bit 0 -> [0,1]) = 36 symbols =
7.2 s. Manchester guarantees a transition every <= 2 symbols (the decoder can
track fps drift) and the counter makes any 7.2 s window unique for ~5.5 days.
The host logs (wall_time, level) for every transition it commands.
"""
from __future__ import annotations

import csv, sys, time
from pathlib import Path

SYM_S = 0.2
SYNC = [1, 1, 1, 0]


def word_symbols(counter: int) -> list[int]:
    bits = [(counter >> (15 - i)) & 1 for i in range(16)]
    return SYNC + [s for b in bits for s in ((1, 0) if b else (0, 1))]


def level_at(t_from_start: float, counter0: int = 0) -> int:
    """Host-side reference: LED level at time t (s) since the run started."""
    n = int(t_from_start // SYM_S); w, k = divmod(n, len(SYNC) + 32)
    return word_symbols((counter0 + w) & 0xFFFF)[k]


def run(port: str, log_path: Path, duration_s: float | None = None):
    import serial  # pyserial
    ser = serial.Serial(port, 115200, timeout=0.05)
    time.sleep(2.0)                       # board reset after open
    ser.reset_input_buffer()
    with open(log_path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["wall_s", "mono_s", "level", "counter", "symbol_idx"])
        t0 = time.monotonic(); n = 0; last = None
        print(f"beacon on {port}, logging to {log_path}", file=sys.stderr)
        while duration_s is None or time.monotonic() - t0 < duration_s:
            target = t0 + n * SYM_S
            while time.monotonic() < target:
                time.sleep(0.001)
            wrd, k = divmod(n, len(SYNC) + 32); lvl = word_symbols(wrd & 0xFFFF)[k]
            if lvl != last:
                ser.write(b"1" if lvl else b"0"); ser.flush()
                w.writerow([f"{time.time():.6f}", f"{time.monotonic():.6f}", lvl, wrd & 0xFFFF, k]); f.flush()
                last = lvl
            n += 1


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("port"); ap.add_argument("log", type=Path); ap.add_argument("--duration", type=float)
    a = ap.parse_args(); run(a.port, a.log, a.duration)
