# IR beacon for sync (and more) — David's idea, 2026-08-26

**Idea.** Cheap RTSP surveillance cameras have IR sensitivity (night mode
removes the IR-cut filter; some see 850 nm faintly even in day mode). Put a
cheap custom IR emitter in the room, blinking a known code. The camera sees
the blinks in-frame, so frame timestamps come from the *image content*, not
from the RTSP stream's unreliable clock.

**Why this is better than software sync.** Sync-from-motion (CasCalib, Lee
2025, §D) gives ~1-frame accuracy but needs motion and fails during exactly
the still windows we care about. A beacon gives a timestamp on every frame,
regardless of what the user does, and survives RTSP latency jitter, dropped
frames, and camera reboots.

**Extensions it unlocks**
1. **Common clock.** Drive the emitter from an ESP32 on the same network as
   the trackers (it can literally be a SlimeVR-firmware node with an LED),
   report blink times to the server → camera frames land on the server clock.
   A code pattern (e.g. a 16–32-bit counter or PRBS, one bit per few frames)
   makes every frame *absolutely* identifiable, not just relatively.
2. **Fixed fiducial.** A beacon is a bright point at a fixed world position;
   two or three at known spacing give scale and a static landmark for
   extrinsics and for detecting camera bumps. Cheaper than any calibration.
3. **Sub-frame timing.** Modulate duty cycle; the blob's brightness across the
   exposure encodes phase → better than one-frame resolution if ever needed.
4. **Free existing IR fiducials — to verify:** Quest 3 Touch Plus controllers
   are tracked by the headset via IR LED constellations. If the cameras see
   those LEDs in night mode, the *controllers* are moving IR fiducials with
   known 6-DoF pose from SteamVR — the LIV-style calibration (§D) with zero
   user action. Quest 3 headset itself may emit IR for hand/room tracking.

**Risks / to check**
- Day mode: IR-cut filter blocks 850 nm on most cams; 940 nm is invisible in
  day mode. Night mode is B/W and grainy → pose model accuracy drops. Options:
  cameras forced to night mode (usable indoors under room light? test);
  or bright 850 nm that leaks through the day filter; or use a visible LED
  instead (a tiny visible blink in a corner is not a product problem).
- Blooming / auto-exposure reacting to the LED.
- Rolling shutter: the blink is a point, so irrelevant.
- Must confirm the cameras' exact models: switchable IR-cut? RTSP timestamp
  behaviour? fps stability?

**Verdict.** Adopt as the planned sync mechanism for v1 experiments (visible
or IR LED on an ESP32, coded blink). Evaluate controller-LED detection as a
stretch goal for calibration.
