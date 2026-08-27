# 03 — Questions for David

Answered questions get a short answer here **and** the consequence recorded in
`STATE.md` decisions. Unanswered ones stay open.

## Framing
- **Q1.** Do you agree the drifting quantity is essentially per-tracker yaw,
  and that a camera-measured *heading* correction (applied like a yaw reset)
  is the right target? Or do you observe error that this framing misses
  (e.g. pitch/roll errors after fast motion, mounting slip, position error
  even with good yaw)?
  **A:** Yaw probably dominates. Go with yaw-only framing; revisit if residuals say otherwise.
- **Q2.** How much residual error would you call "solved"? E.g. feet within
  5 cm / limb heading within 3° for a whole session?
  **A:** Start with a moderate target, improve later. Confirmed target: **limb heading within 5°**.

## Your setup
- **Q3.** HMD and runtime: SteamVR on PC, standalone Quest (via
  SlimeVR + Virtual Desktop/OSC), or no HMD at all? This decides whether we
  have a 6-DoF anchor visible to the camera.
  **A:** SteamVR on PC with a Quest 3 (so HMD 6-DoF pose is available to the server as a camera-visible anchor).
- **Q4.** Which trackers/IMUs and how many (the 8 BNO + 1 BMI270 from
  drift-lab)? Which body assignments?
  **A:** 8+3 custom BNO085 trackers: ankles + feet extensions, thighs, hips + waist extension, chest, elbows.
- **Q5.** Do you have baseline drift numbers from `drift-lab` yet (°/min
  still, °/min while moving)? If not, is that the first thing we finish?
  **A:** Not a priority — drift varies per environment/unit; the system must be robust to unknown drift rather than tuned to a baseline.
- **Q6.** Cameras you'd realistically test with: USB webcam (which
  resolution/fps), a phone, a depth camera? Where would it sit relative to the
  play space?
  **A:** Two cheap RTSP surveillance cameras (model/res/fps still TBD). Implication: network latency, no shared clock → need software sync.

## Product constraints
- **Q7.** Is "the user does a normal full reset once in view of the camera"
  an acceptable amount of setup? That is my proposed way to get camera
  extrinsics for free.
  **A:** Yes. Multiple resets and adjustments in camera view are fine. Rule: simple user input OK, complex setup not.
- **Q8.** How do you feel about video privacy for community data donation —
  only derived keypoints leave the machine?
  **A:** Raw video donation is probably within reach — the HMD already largely anonymizes faces. Design for opt-in raw video, with derived-only as a fallback tier.
- **Q9.** Should the integration live inside SlimeVR-Server (Kotlin, JVM) with
  a Python sidecar for the model, or fully external talking over SolarXR/OSC?
  (Sidecar seems natural; want your read on what the maintainers would
  accept.)
  **A:** Maintainers will likely accept anything that works — this is a major community pain point. Architecture is our call.

## Research process
- **Q10.** Do you have institutional/paper access, or should I plan on arXiv
  + open-access only?
  **A:** No institutional access — open access / arXiv only.
- **Q11.** Any papers, repos or people you already know of that I should
  start from?

  **A:** None known, but probably exists — search SlimeVR Discord/GitHub issues/forks for camera-assist attempts.
## Round 3 (2026-08-26)
- **Q13** per-bone target → **A:** fine; feet can wait, least concern.
- **Q15** PR #1805 → **A:** unknown author, no context. Reference only, build clean.
- **Q6b** night mode → **A:** camera has night mode, maybe not switchable at will; buying/hacking a specific model is acceptable.

## Round 4 (2026-08-27)
- **Q19** licence → **A:** open source, not sold, but used with hardware SlimeVR sells → treated as commercial-adjacent (D34). MPI data not used for training; TotalCapture validation-only; waiting on their reply.
- **Q17** on-body drift run → optional (D26).
- Still open: **Q6b** RTSP camera model; **Q14** whether the cameras see the Touch Plus IR LEDs in night mode; **Q16** turning statistics (minor).
