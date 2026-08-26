# EMDB: The Electromagnetic Database of Global 3D Human Pose and Shape in the Wild

- **Authors / venue / year:** Manuel Kaufmann, Jie Song, Chen Guo, Kaiyue Shen, Tianjian Jiang, Chengcheng Tang, Juan José Zárate, Otmar Hilliges — ICCV 2023
- **Link:** https://arxiv.org/abs/2308.16894
- **Code/data:** https://github.com/eth-ait/emdb (toolkit; dataset under ETH research licence — unverified)
- **Read depth:** skimmed PDF text (abstract, Table 3, metric definitions)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

The benchmark that actually reports **per-joint angular error (MPJAE, degrees)** for monocular SMPL regressors, with EM-sensor ground truth (2.3 cm / 10.6° accuracy vs. a multi-view system). It is also the standard test set for every world-grounded model above (WHAM, TRAM, GVHMR, PromptHMR).

## What they do

10 subjects, 81 sequences, 58 min; body-worn EM sensors (6-DoF) + hand-held iPhone (ARKit camera poses). SMPL fitted to sensors then refined with images. Evaluates monocular methods with MPJPE/MVE (± PA) and **MPJAE** (geodesic angle between predicted and GT joint rotations after Procrustes for the -PA variant), plus jitter.

## Key numbers (with table/figure reference)

- **Table 3 (EMDB 1, camera-relative):** MPJAE / MPJAE-PA in degrees — HybrIK (HRNet) 24.5 ± 11.3 / 23.1 ± 11.1; CLIFF 23.1 ± 9.9 / 21.6 ± 8.6; PARE 24.7 / 22.4; GLAMR 25.5 / 23.5; ROMP 26.6 / 24.0; PyMAF 28.5 / 25.7. MPJPE-PA for the same: HybrIK 65.6, CLIFF 68.8 mm.
- Authors note explicitly that a baseline "fails to capture the lower arm rotations" in a way MPJPE does not penalise — their motivation for reporting MPJAE.
- Dataset GT itself: 10.6° angular error against the volumetric reference (abstract), so the floor of measurable rotation accuracy on EMDB is ~10°.

## What we can reuse / what to be careful about

- Reuse: realistic expectation — 2023 per-frame SMPL regressors average **~22–25° per-joint rotation error** (all joints, all frames, moving subjects). Our regime (still, well-seen) should be better but this is the published bar. Evaluation code computes MPJAE for us.
- Careful: MPJAE mixes swing and twist and averages over hands/feet; no per-joint or per-axis breakdown; GT rotation accuracy is itself ~10°. None of the 2024–25 models (WHAM, TRAM, GVHMR, PromptHMR) published MPJAE on EMDB even though the toolkit supports it.

## Open questions this raises

- Run EMDB's evaluation on WHAM/GVHMR/PromptHMR outputs and split MPJAE into heading (yaw of bone direction) vs twist, per joint.
- Compare with the 3DPW-eval MPJAE (ECCV 2020 challenge) for older numbers.
