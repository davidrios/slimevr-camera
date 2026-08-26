# Synthetic-to-real domain gap for 2D/3D human pose (BEDLAM, PeopleSansPeople, SURREAL, RePoGen, SynthPose, Wood 2021, SynthMoCap, EgoBody)

- **Authors / venue / year:** survey note. BEDLAM (Black, CVPR 2023, 2306.16940); BEDLAM 2.0 (NeurIPS 2025, 2511.14394); PeopleSansPeople (Unity, 2112.09290); SURREAL (Varol, CVPR 2017, 1701.01370); RePoGen (FG 2024, 2307.06737); SynthPose/OpenCapBench (2406.09788); Wood et al. "Fake It Till You Make It" (ICCV 2021, 2109.15102); SynthMoCap "Look Ma, no markers" (SIGGRAPH Asia 2024, 2410.11520); trampoline synthetic (2604.01322); EgoBody (ECCV 2022, 2112.07642); Ego-Exo4D (2311.18259).
- **Link:** per paper above.
- **Code:** SynthPose weights https://huggingface.co/stanfordmimi/synthpose-vitpose-huge-hf ; SynthMoCap data https://github.com/microsoft/SynthMoCap
- **Read depth:** skimmed (result tables via ar5iv/arXiv HTML; not all tables extracted, see "unverified")
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Agenda §H sub-question: does BEDLAM-style synthetic training help or hurt an RTMPose/ViTPose-class 2D detector on real cheap-camera footage, and which sim-to-real tricks are evidence-backed. Also whether anyone has measured detectors on people wearing HMDs.

## What they do / Key numbers (with table/figure reference)

**3D (SMPL) regressors, synthetic-only vs real**
- BEDLAM Table 1 (3DPW PA-MPJPE/MPJPE/PVE): BEDLAM-CLIFF synthetic-only 46.6/72.0/85.0 ≈ CLIFF real 46.4/73.9/87.6; + 3DPW fine-tune 43.0/66.9/78.5. Table 3: 5 % → 100 % of BEDLAM gives PA-MPJPE 54.0 → 50.5 (CLIFF-style setup), monotonic. BEDLAM 2.0 Table 1: CameraHMR synthetic-only 3DPW 43.2 → 41.1, EMDB 50.0 → 46.5, RICH 42.1 → 36.8 (B1 → B2), attributed to camera/focal diversity; no real fine-tuning at all.

**2D keypoint detectors**
- PeopleSansPeople (Keypoint R-CNN, COCO AP): few-shot real: synthetic-pretrain + FT 44.4 vs real-only 6.4; full COCO 63.5 vs 62.0 (+1.5). (Table numbers from paper text; exact table id unverified.)
- SURREAL Table 3/4 (Human3.6M seg IoU / depth RMSE): synth-only 42.9 / 111.6 < real 46.3 / 96.3 < synth-pretrain+real-FT 54.3 / 90.0. Pattern: **synthetic-only < real-only < synthetic-pretrain + real fine-tune**.
- RePoGen Table 2 (ViTPose, AP on unusual-viewpoint test set): ViTPose-S COCO 35.1 → COCO+RePoGen 53.9; ViTPose-H 69.2 → 81.1, "without harming performance on common views". Table 3: gain saturates at ~3k synthetic images and *more synthetic hurt* (5k: 58.8 vs 3k: 61.8). Table 5: random textures give no notable gain.
- Trampoline (2026) Table 3 (ViTPose-S AP/AR on real test): COCO 50.5/55.6; synthetic-only 3.6k 59.3/64.0; real 10k 64.1/70.2; real+synthetic 68.4/74.5; 5k COCO images mixed into FT to prevent forgetting.
- SynthPose: ViTPose-B/H + HRNet fine-tuned on BEDLAM + VisionFit + 3DPW + COCO (equal per-batch cycling), 35 projected SMPL-vertex markers; PCK@0.05 on RICH 0.903 vs 0.707; joint-angle RMSE halved. **Direct evidence that projected-BEDLAM 2D labels fine-tune ViTPose without collapse.**
- Wood 2021 Table 3 (faces, 300W NME common/challenging): synthetic-only + label adaptation 3.09/4.86 vs real 3.37/5.77; no augmentation 4.25/7.87; no label adaptation 5.61/8.43.
- SynthMoCap: landmark detectors synthetic-only; randomisation recipe 914 HDRIs, 47 indoor scenes, 384 clothing, 479 hairstyles; augs: rotation/scale, motion blur, brightness/contrast/hue, **JPEG compression, ISO noise**, random occluders; cameras sampled so ≥75 % of joints visible. No standalone 2D metric (unverified).
- "Real-calibrated synthetic-first data engine" (2605.09699): abstract says synthetic-only "remains substantially below real-only" (snippet numbers 0.449 vs 0.746 mAP — unverified).
- Sapiens: 308 keypoints are from 11M **manually annotated** real images; synthetic only for depth/normals.

**HMD wearers**
- EgoBody Table 3: off-the-shelf PARE MPJPE 123.0 on EgoBody vs ~77 % higher error than on 3DPW; authors *manually fixed 2D detections* due to occlusion. No numeric evaluation of 2D detectors on the HoloLens wearer from the Kinect (third-person) views.
- Ego-Exo4D: exo-view GT built from off-the-shelf 2D detector + triangulation on Aria-glasses wearers; no reported detector degradation metric.
- **No paper found that measures 2D keypoint accuracy on a person wearing a VR headset from a third-person camera.** Occlusion benchmark 2504.10350: nose/head among most vulnerable keypoints.

## What we can reuse / what to be careful about

- Evidence-backed recipe: (1) pretrain/fine-tune on synthetic, (2) always mix real (COCO subset, equal per-batch cycling) to prevent forgetting, (3) heavy photometric augmentation incl. JPEG/ISO noise/blur — mimics RTSP cameras, (4) small real "label adaptation" set to fix label-convention mismatch (projected SMPL-X joints ≠ COCO annotator convention; Wood 5.61 → 3.09), (5) diverse cameras/focals (BEDLAM 2.0 gain), (6) stop early — a few thousand targeted synthetic images already saturate (RePoGen).
- Synthetic-only for a 2D detector is consistently below real-only; the value is in covering our *specific* gap (HMD, controllers, arm-up dance poses, low camera) — like RePoGen for viewpoints.
- The HMD question is unmeasured: we must build a small real labelled VR test set (David + friends, headset on) before any synthetic work can be evaluated.

## Open questions this raises

- How badly does RTMPose/ViTPose degrade on HMD wearers today? (Experiment: run off-the-shelf on our footage, annotate ~200 frames.)
- Does an HMD mesh in renders fix it, or does a simple copy-paste headset augmentation on COCO images do as well (far cheaper)?
- Label convention: projected SMPL-X joints vs COCO — use SynthPose's marker approach or a learned adaptation layer?
