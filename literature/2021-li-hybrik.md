# HybrIK: A Hybrid Analytical-Neural Inverse Kinematics Solution for 3D Human Pose and Shape Estimation (+ HybrIK-X)

- **Authors / venue / year:** Jiefeng Li, Chao Xu, Zhicun Chen, Siyuan Bian, Lixin Yang, Cewu Lu — CVPR 2021. HybrIK-X (SMPL-X whole body): Li, Bian, Xu, Chen, Yang, Lu — arXiv 2304.05690, TPAMI 2025.
- **Link:** https://arxiv.org/abs/2011.14672 ; https://arxiv.org/abs/2304.05690
- **Code:** https://github.com/Jeff-sjtu/HybrIK — MIT. PyTorch. Backbones ResNet-34 and HRNet-W48; HybrIK-X checkpoints in same repo. Video demo (frame-by-frame). GPU recommended; the network is small enough (ResNet-34) that CPU inference is plausible (unverified).
- **Read depth:** HybrIK: skimmed PDF text (method, Tables 1–2). HybrIK-X: abstract only.
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

The one model family that treats **twist about the bone axis as an explicit, separately estimated 1-DoF quantity**, and the only paper here with an ablation isolating the effect of twist error. Exactly the decomposition we care about: swing (bone direction, incl. heading) comes analytically from 3D joints; twist is a learned scalar per joint.

## What they do

Predict 3D joint positions (heatmaps) + shape β + a twist angle φ_k per joint, then run a differentiable analytical IK ("twist-and-swing decomposition", Baerlocher) that converts joints to SMPL relative rotations. Swing is fully determined by the child-joint direction; twist comes from the network. "Adaptive" variant re-solves each joint from the reconstructed parent to limit error accumulation. Output: SMPL θ, β in camera frame; root depth from RootNet. Per-frame, no temporal model. HybrIK-X extends this to SMPL-X (hands/face).

## Key numbers (with table/figure reference)

- Table 2 (3DPW): PA-MPJPE 45.0 / MPJPE 74.1 / PVE 86.5 mm (Adaptive HybrIK w/ 3DPW); Human3.6M PA-MPJPE 33.6. Repo lists HRNet-W48 variant at 41.8 PA-MPJPE.
- **Table 1 (twist ablation, GT joints, 3DPW):** vertex error with *estimated* twist 10.0 mm, *zero* twist 12.1 mm, *random* twist 67.3 mm. 24-joint error is 0.1 mm in all cases — twist does not move SMPL joints, only the mesh.
- Fig. 5: distribution of GT twist angles on 3DPW test — only neck, elbow and wrist have a wide range; all other joints < 30°. Authors use this to argue twist "can be reliably estimated"; it also means a zero-twist prior is nearly as good for most joints.
- EMDB Table 3 (third party, HRNet version): **MPJAE 24.5° / MPJAE-PA 23.1°**, best of the 2023 field on MPJPE-PA but not on angle (CLIFF 23.1°/21.6°).

## What we can reuse / what to be careful about

- Reuse: the swing/twist split gives us a natural place to *read heading from swing only and ignore twist*, or to replace predicted twist with the IMU's. The IK is a stand-alone differentiable module we could apply to any 3D-keypoint model.
- Careful: the twist ablation only shows the *mesh* effect; no twist-angle error in degrees is reported. Elbow/wrist twist (forearm pronation — the joints SlimeVR has trackers on) is precisely where the range is wide and estimation hardest. Per-frame, small backbone ⇒ jittery.

## Open questions this raises

- Measure HybrIK's twist-angle error in degrees on 3DPW/EMDB per joint (elbow, wrist, hip, knee) — nobody reports it.
- Is swing (bone direction) error alone, projected to the floor plane, within ±5° for thigh/shank/upper-arm during still moments?
