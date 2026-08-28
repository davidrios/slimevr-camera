"""Control of the hi3510-family IP cameras (IPCAM firmware V32.x) used in David's room.

Credentials: entries `url,user,password`, whitespace- or newline-separated
(one per camera), in /mnt/data2/david/work/slimevr-camera-data/cameras/.access
(never logged).
Writes to image attributes REQUIRE `-image_type=<profile>` (found by reading
the camera's own display.html): 1 = day profile, 0 = night profile, and the
write only succeeds for the profile currently ACTIVE (night="off" -> 1,
night="on" -> 0). `set_image` picks it automatically and falls back. Known parameters
(getimageattr): brightness, saturation, sharpness, contrast, hue, wdr,
wdrvalue, night (on/off), shutter (1..10000), flash_shutter, flip, mirror,
gc (gain ceiling?), ae, targety (AE target luminance 0..100), noise, gamma,
aemode, imgmode.  IR LED: setinfrared&-infraredstat=open|close|auto.
Snapshot: /tmpfs/auto.jpg (HTTP basic auth). RTSP: rtsp://<host>:554/11 (no auth).
"""
from __future__ import annotations

import re
from pathlib import Path

import requests

ACCESS = Path("/mnt/data2/david/work/slimevr-camera-data/cameras/.access")


class Hi3510Camera:
    def __init__(self, host: str, user: str, password: str, timeout: float = 6.0):
        self.base = f"http://{host}"; self.auth = (user, password); self.timeout = timeout

    @classmethod
    def from_access(cls, host: str | None = None, path: Path = ACCESS) -> "Hi3510Camera":
        entries = [e.split(",") for e in path.read_text().split() if e.count(",") >= 2]
        hosts = {re.sub(r"^https?://", "", e[0]).split("/")[0].split(":")[0]: e for e in entries}
        if host is None: host = next(iter(hosts))
        e = hosts.get(host) or entries[0]                 # same credentials on all cameras -> fall back to the first
        return cls(host, e[1], ",".join(e[2:]))

    def _get(self, query: str) -> str:
        r = requests.get(f"{self.base}/cgi-bin/hi3510/param.cgi?{query}", auth=self.auth, timeout=self.timeout); r.raise_for_status(); return r.text

    def attrs(self) -> dict[str, str]:
        return dict(re.findall(r'var (\w+)="([^"]*)"', self._get("cmd=getimageattr")))

    def infrared(self) -> str:
        return re.search(r'infraredstat="(\w+)"', self._get("cmd=getinfrared")).group(1)

    def set_infrared(self, state: str) -> bool:      # open | close | auto
        return "Succeed" in self._get(f"cmd=setinfrared&-infraredstat={state}")

    def set_image(self, **kw) -> bool:
        q = "&".join(f"-{k}={v}" for k, v in kw.items())
        first = 0 if self.attrs().get("night") == "on" else 1
        for it in (first, 1 - first):
            if "Succeed" in self._get(f"cmd=setimageattr&-image_type={it}&{q}"):
                return True
        return False

    def snapshot(self, out: Path) -> Path:
        r = requests.get(f"{self.base}/tmpfs/auto.jpg", auth=self.auth, timeout=self.timeout); r.raise_for_status(); out.write_bytes(r.content); return out

    # presets
    def marker_mode(self, targety: int = 15) -> bool:
        """Night mode + IR LED on + dark AE target: retroreflective patches stay saturated, room goes dim."""
        ok = self.set_infrared("open")
        ok &= self.set_image(night="on")          # switches the active profile to night (image_type 0)
        return ok and self.set_image(targety=targety)

    def normal_mode(self) -> bool:
        return self.set_image(targety=60)


if __name__ == "__main__":
    import sys, json
    cam = Hi3510Camera.from_access()
    if len(sys.argv) > 1 and sys.argv[1] == "marker": print("marker mode:", cam.marker_mode(int(sys.argv[2]) if len(sys.argv) > 2 else 15))
    elif len(sys.argv) > 1 and sys.argv[1] == "normal": print("normal mode:", cam.normal_mode())
    print(json.dumps({k: cam.attrs().get(k) for k in ("night", "shutter", "gc", "ae", "targety", "aemode")}), "infrared:", cam.infrared())
