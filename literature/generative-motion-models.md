# Generative motion models as a synthetic-motion source (MDM, PriorMDM, MotionGPT, EDGE, AIST++ and 2024–2026 successors)

- **Authors / venue / year:** survey note; MDM Tevet et al. ICLR 2023 (arXiv 2209.14916); PriorMDM Shafir et al. ICLR 2024 (2303.01418); MotionGPT Jiang et al. NeurIPS 2023 (2306.14795), MotionGPT3 (2506.24086); MoMask Guo et al. CVPR 2024 (2312.00063); EDGE Tseng et al. CVPR 2023 (2211.10658); AIST++ Li et al. ICCV 2021.
- **Link:** see per-model URLs below.
- **Code:** all CUDA; licences per model below.
- **Read depth:** skimmed (READMEs, LICENSE files, arXiv abstracts; nothing run)
- **Date read:** 2026-08-26

## Relevance to us (1–3 lines)

Agenda §H: source of arbitrary VR-like / dance-like motion beyond what AMASS contains. Needed: per-frame SMPL(-X) rotations + root translation that a Blender/Unreal pipeline can render. Key question is which models emit rotations directly versus joint positions that need an IK fit.

## What they do

**Common dataset chain**: nearly all text-to-motion models train on HumanML3D (rebuilt from AMASS + HumanAct12; repo MIT, data not redistributable, https://github.com/EricGuo5513/HumanML3D), so weights inherit the AMASS non-commercial terms (see `2019-mahmood-amass-and-smplx-licences.md`). Motion-X / Motion-X++ (SMPL-X, 81K clips, https://github.com/IDEA-Research/Motion-X) is non-commercial with a licence form.

| Model | Licence | Output | SMPL export | Status |
|---|---|---|---|---|
| MDM https://github.com/GuyTevet/motion-diffusion-model | MIT | HumanML3D 263-d → 22×3 joints | `visualize/render_mesh.py` (joints2smpl SMPLify-style IK) → thetas + root_translation, **no betas**, slow, approximate | active (2025-10; 50-step fast models) |
| PriorMDM https://github.com/priorMDM/priorMDM | MIT | as MDM; DoubleTake long sequences, two-person, trajectory control | as MDM | active (2026-04) |
| MotionGPT / MotionGPT3 https://github.com/OpenMotionLab/MotionGPT3 | MIT (SMPL/data terms apply) | (n,22,3) joints | `fit.py` → SMPL vertices/PLY | active (2025-10) |
| MoMask https://github.com/EricGuo5513/momask-codes | MIT | 22×3 joints + **BVH** | none (BVH retarget in Blender) | 2024-08 |
| T2M-GPT https://github.com/Mael-zys/T2M-GPT | Apache-2.0 | joints | `render_final.py` mesh fit | stale 2023 |
| MotionLCM https://github.com/Dai-Wenxun/MotionLCM | custom non-commercial | joints | fit.py | 2024-12 |
| MotionStreamer (ICCV 2025) https://github.com/zju3dv/MotionStreamer | MIT | 272-d custom → BVH | none | 2025 |
| CLoSD https://github.com/GuyTevet/CLoSD | MIT | physics-simulated (Isaac Gym) humanoid | saves SMPL params | heavy setup |
| HY-Motion 1.0 (Tencent, 2512.23464) | Tencent community licence, **excludes EU/UK**, 1M MAU cap | FBX skeleton | unverified | 24–26 GB VRAM |
| OmniMotion-X (2510.19789) | MIT, SMPL-X | — | code/weights pending | — |
| ScaMo, MotionLLaMA, MotionGPT-2 | no licence / weights not released / no code | — | — | not usable |

**Dance (music-to-dance, AIST++-trained)**

| Model | Licence | Output |
|---|---|---|
| **EDGE** https://github.com/Stanford-TML/EDGE | MIT | **SMPL 6D rotations + root translation (pkl)**, `Convert.py` → FBX; CUDA 11.6, 16 GB; unmaintained since 2023-03 |
| Bailando https://github.com/lisiyao21/Bailando | NTU S-Lab 1.0 (restrictive) | SMPL |
| FineDance https://github.com/li-ronghui/FineDance | non-commercial, no commercial training | SMPL-H 52-joint |
| Lodge (CVPR 2024) https://github.com/li-ronghui/LODGE | no LICENSE file | FineDance features |
| POPDG https://github.com/Luke-Luo1/POPDG | MIT (dataset terms unverified) | pkl → FBX like EDGE |
| MEGADance (NeurIPS 2025), SoulDance (ICCV 2025) | unstated / non-commercial, no weights | — |

**AIST++ itself** (https://google.github.io/aistplusplus_dataset/, API Apache-2.0 https://github.com/google/aistplusplus_api): 1,408 sequences, 10 genres, 9 cameras, `smpl_poses` + `smpl_trans` (betas likely default — unverified). Annotation licence text not found on fetched pages (**"CC BY 4.0" unverified**); source AIST Dance DB: research free, commercial needs written consent, no redistribution (https://aistdancedb.ongaaccel.jp/terms_of_use/).

## Key numbers (with table/figure reference)

None extracted — motion quality metrics (FID, R-precision) are not what matters for us; coverage of pose space and physical plausibility (foot skate, penetration) are, and no paper reports them in a form comparable across models.

## What we can reuse / what to be careful about

- **Direct rotations, no IK**: EDGE (dance) and AIST++ (dance data) give SMPL rotations directly; AMASS gives SMPL-X directly. Everything HumanML3D-based gives 22 joint positions and needs joints2smpl (slow, no shape, twist ambiguity — exactly the elbow/wrist twist problem noted in `2021-li-hybrik.md`).
- Text prompts cannot express "person in VR playing Beat Saber"; VR-specific arm-heavy motion is better obtained by (a) AMASS/AIST++ selection, (b) PriorMDM trajectory/prefix control, or (c) David's own SlimeVR/headset recordings retargeted to SMPL-X — likely the highest-value source and licence-free.
- All weights here are non-commercial in practice because of AMASS/AIST training data, regardless of MIT code licences.
- Generated motion lacks hand/finger and head-gaze detail; for an HMD wearer the head pose distribution matters (headset tracking gives it for free in our own recordings).

## Open questions this raises

- AIST++ annotation licence (CC BY 4.0?) — verify on the download page.
- Does joints2smpl output from MDM render acceptably at 30 fps (jitter)? Needs a code run.
- Is a VR-motion prior even needed, or is AMASS dance/sports coverage + our own recordings sufficient? Decide after first render experiment.
