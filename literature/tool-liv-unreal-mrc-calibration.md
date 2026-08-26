# Mixed-reality-capture camera calibration tools (LIV, Unreal MRCalibration, Microsoft Spectator View)

- **Authors / venue / year:** LIV Inc. help-desk docs ("4. Calibrating Your Camera", tracked-camera setup); Epic Games "How to use the Mixed Reality Capture Calibration Tool" (UE 4.27 / 5.x docs); Microsoft MixedRealityCompanionKit LegacySpectatorView/Calibration (GitHub). Not papers; file named `tool-…` since there is no first author/year.
- **Link:** https://help.liv.tv/hc/en-us/articles/360016507779-4-Calibrating-Your-Camera ; https://dev.epicgames.com/documentation/en-us/unreal-engine/how-to-use-the-mixed-reality-capture-calibration-tool-in-unreal-engine ; https://github.com/microsoft/MixedRealityCompanionKit/tree/master/LegacySpectatorView/Calibration
- **Code:** LIV closed; Unreal tool closed binary (MRCalibration.exe), Windows + Vive/Rift; Microsoft kit open (MIT per repo LICENSE — unverified, not opened), OpenCV-based, HoloLens-specific.
- **Read depth:** skimmed (Epic docs full page; LIV via search summary only, help.liv.tv returned 403; Microsoft README summary)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Precedent for §D(c): consumer VR mixed-reality capture routinely solves an external camera's pose in SteamVR/Oculus space using a **tracked controller as a moving fiducial**. Nobody uses the HMD itself (it is on the user's face and its front is featureless); the controller is used because the user can place it exactly on a crosshair.

## What they do

- **LIV**: 3-click procedure. Click 1: hold controller against the camera lens (fixes camera position ≈ controller position). Clicks 2–3: from the far end of the play space, align the controller with on-screen crosshairs in two corners and pull the trigger. From these 3 (controller pose, image point) correspondences LIV solves FOV + rotation + position. Result check: virtual controllers overlaid on real ones "almost perfectly". Alternative: strap a Vive tracker to the camera (camera pose = tracker pose + fixed offset).
- **Unreal MRCalibration**: step 2 lens calibration with a printed checkerboard (reprojection error reported, <1 px = good); step 3 alignment: user aligns the tracked controller with on-screen controller models at up to 11 positions and pulls the trigger — i.e. PnP on controller poses vs. image positions; step 4: 5 more samples at the filming depth in 5 image regions. Outputs FOV, distortion, camera pose in tracking space.
- **Microsoft Spectator View**: checkerboard seen simultaneously by the HoloLens camera and the DSLR → OpenCV stereo calibration gives DSLR↔HoloLens transform; HoloLens' own tracking then places the DSLR in world.

## Key numbers (with table/figure reference)

None published. Community practice: ~10 controller samples give an overlay that is visually aligned (sub-cm at arm's length is the informal target); no degree figures anywhere.

## What we can reuse / what to be careful about

- Reuse: the procedure shape — a handful of (tracked-6DoF pose, image observation) pairs solved by PnP is enough for MR capture, which needs *visually* exact alignment, i.e. well under 1° effective error. For us, the HMD position from SteamVR/OpenXR + the head keypoint (or the HMD's rectangular front detected in the image) over a normal play session gives hundreds of such pairs with zero user effort, at the cost of a less precise image point than a crosshair-aligned controller.
- Careful: these tools assume intrinsics from a checkerboard or a manually tuned FOV; all Windows-only; none runs on Quest-standalone without a PC link (Quest MRC uses the same controller-as-fiducial idea in its Mixed Reality Capture Tool, not verified here).

## Open questions this raises

- Detecting the HMD in RGB robustly (it's dark, glossy, and often side-on): a head keypoint from the pose model is a proxy but is offset from the HMD origin by an unknown, user-dependent vector — could be solved as an extra 3 unknowns in the same least squares.
