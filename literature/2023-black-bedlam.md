# BEDLAM: A Synthetic Dataset of Bodies Exhibiting Detailed Lifelike Animated Motion (+ BEDLAM 2.0)

- **Authors / venue / year:** Black, Patel, Tesch, Yang — CVPR 2023. BEDLAM 2.0: Patel et al., NeurIPS 2025 (D&B, oral).
- **Link:** https://arxiv.org/abs/2306.16940 ; project https://bedlam.is.tue.mpg.de/ ; BEDLAM 2.0 https://arxiv.org/abs/2511.14394 , https://bedlam2.is.tuebingen.mpg.de/
- **Code:** render tools https://github.com/PerceivingSystems/bedlam_render (UE 5.0.3 **Windows**, Blender 3.2.2), https://github.com/PerceivingSystems/bedlam2_render (UE 5.3.2 Windows, Blender 4.0.2), https://github.com/PerceivingSystems/bedlam2_retargeting ; training code https://github.com/pixelite1201/BEDLAM. LICENSE.md in render repos = MPI non-commercial (not MIT). Rendering needs a Windows UE box (128 GB RAM, RTX 3090+ recommended); GT/training code is plain Python/CUDA.
- **Read depth:** skimmed (paper tables via ar5iv, project/licence pages, render-repo READMEs; no data downloaded)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

The reference "mocap → SMPL-X body → game-engine render with GT" pipeline (agenda §H). Tells us what a re-render with our own fixed cameras + HMD mesh would cost, and that the licence is non-commercial for data, code *and* derived weights.

## What they do

- 2,311 AMASS motions (BEDLAM 2.0: 4,643 incl. MOYO, BEAT2) retargeted to SMPL-X bodies with CLO3D-simulated clothing, Meshcapade skin textures, Reallusion hair, rendered in Unreal 5 in 8 indoor scenes / 95 Poly Haven HDRIs, 1–10 people per frame, cinematic 16:9 camera (HFOV 52–65°, static random extrinsics + orbit shots).
- Released: 10,450 sequences at 1280×720, 30 fps (~380K frames, 1M boxes), PNG + MP4, 32-bit EXR depth, segmentation masks, CSV GT (SMPL-X params, camera intrinsics/extrinsics in Unreal coordinates). Also the source assets: body textures, clothing meshes/textures, SMPL-X animation files, HDRIs, scenes. **Not** released: 27 commercial hair grooms.
- Render pipeline: Blender script bakes SMPL-X animation (with pose correctives) to Alembic; Unreal Python editor scripts import clothing/textures/HDRIs, build sequences from `be_seq.csv` (bodies, placement, camera), render via Movie Render Queue; cryptomatte → depth/seg. No `.uproject` shipped; you create the project and enable plugins.
- **BEDLAM 2.0**: 8.0M frames / 27,480 seq / 74.5 h, same 1280×720@30; ~26 TB total (PNG 11 TB, MP4 160 GB, GT 4 GB, depth 15 TB for 44 % of frames). Adds moving cameras (pan/dolly/orbit/zoom, handheld + Apple Vision Pro egocentric trajectories, 14 %), focal 14–400 mm, 187 outfits, 40 hair grooms (released), 182 GSO shoes, 15 scenes, 16 shape coefficients. Hugging Face mirror gated ("bedlam2-non-commercial").

## Key numbers (with table/figure reference)

- Table 1 (3DPW PA-MPJPE / MPJPE / PVE): CLIFF real-only 46.4/73.9/87.6; BEDLAM-CLIFF **synthetic-only** 46.6/72.0/85.0; + 3DPW fine-tune 43.0/66.9/78.5. HMR real 76.7/130/– vs BEDLAM-HMR 47.6/79.0/93.1. RICH: CLIFF real 55.7/90.0/102.0 vs BEDLAM-CLIFF 51.2/84.5/96.6.
- Table 3: monotonic gain with more synthetic data; 5 % of BEDLAM (38K crops) beats 85K AGORA crops.
- BEDLAM 2.0 paper: CameraHMR 3DPW 43.2/68.0/80.7 (B1) → 41.1/64.8/76.3 (B2); GVHMR RICH WA-MPJPE 87.3 → 75.5.
- **No 2D keypoint detector evaluation** in either paper; no 2D keypoint files — 2D joints must be projected from SMPL-X + camera CSV.

## What we can reuse / what to be careful about

- Licence (https://bedlam.is.tue.mpg.de/license.html, identical for 2.0): "sole purpose of performing non-commercial scientific research, non-commercial education, or non-commercial artistic projects"; "prohibits the use of the Data & Software to train methods/algorithms/neural networks/etc. for commercial, pornographic, military, surveillance, or defamatory use"; no redistribution ("one copy for archive purposes only"). Commercial via smpl@max-planck-innovation.de. Registration + per-file download from the site.
- **Consequence for us**: weights trained on BEDLAM renders inherit the non-commercial restriction. Fine for a non-commercial open-source release, but blocks any commercial SlimeVR use and means we cannot redistribute the renders themselves.
- Re-rendering with our cameras + an HMD: technically feasible (bodies are Alembic caches in a normal UE level; cameras are CSV-driven) but there is no documented hook for attached props; Windows-only UE; heavy asset download. Cheaper for us: reuse only the *idea* and the free asset subset (Poly Haven HDRIs are CC0; clothing/textures are MPI-licensed) in a Blender pipeline we control.
- Body textures are Meshcapade CC BY-NC 4.0 (per BEDLAM 2.0 paper) — another non-commercial component.
- Camera model is a DSLR-style cinematic camera; our cheap wide-angle RTSP cameras (distortion, rolling shutter, compression) are out of its distribution — needs our own augmentation.

## Open questions this raises

- Total BEDLAM 1 download size unverified (login-gated). Segmentation masks in 2.0 unverified.
- Does training a 2D detector (RTMPose-class) on projected BEDLAM keypoints help on real footage? Not in the papers — see `synthetic-to-real-domain-gap.md`.
- Is there an already-existing Linux/Blender re-implementation of the BEDLAM sequence generator (see `synthetic-human-data-generators.md`)?
